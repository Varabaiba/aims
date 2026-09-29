"""Persist and dispatch scheduled AWTRIX notification payloads."""

# INT
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from threading import Event, Thread


c_schedule_poll_interval_seconds = 1.0
x_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScheduledNotification:
    """Represent one durable notification scheduled for an AWTRIX device."""

    schedule_id: int
    run_at: datetime
    notification: dict[str, object]
    status: str
    delivered_at: datetime | None
    error_message: str | None


@dataclass(frozen=True)
class ForwardingLogRecord:
    """Represent one C1 request forwarded through the proxy or simplified route."""

    log_id: int
    created_at: datetime
    source: str
    method: str
    path: str
    status_code: int
    error_message: str | None


def get_utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(timezone.utc)


def serialize_datetime(a_value: datetime) -> str:
    """Convert a timezone-aware datetime into canonical UTC ISO-8601 text."""
    if a_value.tzinfo is None or a_value.utcoffset() is None:
        raise ValueError("Scheduled time must include a timezone.")

    return a_value.astimezone(timezone.utc).isoformat()


def deserialize_datetime(a_value: str | None) -> datetime | None:
    """Convert stored ISO-8601 text into a timezone-aware datetime."""
    if a_value is None:
        return None

    x_datetime = datetime.fromisoformat(a_value)
    if x_datetime.tzinfo is None or x_datetime.utcoffset() is None:
        raise ValueError("Stored schedule timestamp has no timezone.")

    return x_datetime


class ScheduleStore:
    """Manage AIMS notification schedules in one SQLite database."""

    def __init__(self, a_database_path: Path) -> None:
        """Set the SQLite file that stores scheduled notifications."""
        self._database_path = a_database_path

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with row names enabled."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        x_connection = sqlite3.connect(self._database_path)
        x_connection.row_factory = sqlite3.Row
        return x_connection

    def initialize(self) -> None:
        """Create the schedule table when the database is first used."""
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_notifications (
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_at_utc TEXT NOT NULL,
                    notification_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    delivered_at_utc TEXT,
                    error_message TEXT
                )
                """
            )

            x_connection.execute(
                """
                CREATE TABLE IF NOT EXISTS forwarding_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at_utc TEXT NOT NULL,
                    source TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    error_message TEXT
                )
                """
            )
            # A shutdown during dispatch leaves a claim incomplete; retry it on restart.
            x_connection.execute(
                """
                UPDATE scheduled_notifications
                SET status = 'pending'
                WHERE status = 'dispatching'
                """
            )

    def create(
        self,
        a_run_at: datetime,
        a_notification: dict[str, object],
    ) -> ScheduledNotification:
        """Persist one future AWTRIX notification and return its identifier."""
        x_run_at = serialize_datetime(a_run_at)
        try:
            x_notification_json = json.dumps(a_notification, separators=(",", ":"))
        except (TypeError, ValueError) as x_exception:
            raise ValueError("notification must contain JSON-compatible values.") from x_exception

        with closing(self.connect()) as x_connection, x_connection:
            x_cursor = x_connection.execute(
                """
                INSERT INTO scheduled_notifications (run_at_utc, notification_json)
                VALUES (?, ?)
                """,
                (x_run_at, x_notification_json),
            )
            x_schedule_id = x_cursor.lastrowid

        if x_schedule_id is None:
            raise RuntimeError("SQLite did not return the created schedule identifier.")

        return ScheduledNotification(
            schedule_id=x_schedule_id,
            run_at=deserialize_datetime(x_run_at),
            notification=a_notification,
            status="pending",
            delivered_at=None,
            error_message=None,
        )

    def list_all(self) -> list[ScheduledNotification]:
        """Return schedules ordered by their requested dispatch time."""
        with closing(self.connect()) as x_connection, x_connection:
            x_rows = x_connection.execute(
                """
                SELECT schedule_id, run_at_utc, notification_json, status,
                       delivered_at_utc, error_message
                FROM scheduled_notifications
                ORDER BY run_at_utc, schedule_id
                """
            ).fetchall()

        return [self.row_to_schedule(x_row) for x_row in x_rows]

    def delete(self, a_schedule_id: int) -> bool:
        """Delete a schedule by identifier and report whether it existed."""
        with closing(self.connect()) as x_connection, x_connection:
            x_cursor = x_connection.execute(
                "DELETE FROM scheduled_notifications WHERE schedule_id = ?",
                (a_schedule_id,),
            )

        return x_cursor.rowcount == 1

    def claim_due(self, a_current_time: datetime) -> ScheduledNotification | None:
        """Atomically claim one pending schedule whose dispatch time has arrived."""
        x_current_time = serialize_datetime(a_current_time)
        with closing(self.connect()) as x_connection, x_connection:
            # An immediate transaction prevents multiple workers from claiming one row.
            x_connection.execute("BEGIN IMMEDIATE")
            x_row = x_connection.execute(
                """
                SELECT schedule_id, run_at_utc, notification_json, status,
                       delivered_at_utc, error_message
                FROM scheduled_notifications
                WHERE status = 'pending' AND run_at_utc <= ?
                ORDER BY run_at_utc, schedule_id
                LIMIT 1
                """,
                (x_current_time,),
            ).fetchone()

            if x_row is None:
                return None

            x_connection.execute(
                """
                UPDATE scheduled_notifications
                SET status = 'dispatching'
                WHERE schedule_id = ? AND status = 'pending'
                """,
                (x_row["schedule_id"],),
            )

        return self.row_to_schedule(x_row, a_status="dispatching")

    def mark_delivered(self, a_schedule_id: int) -> None:
        """Record that a claimed notification was accepted by AWTRIX."""
        x_delivered_at = serialize_datetime(get_utc_now())
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute(
                """
                UPDATE scheduled_notifications
                SET status = 'delivered', delivered_at_utc = ?, error_message = NULL
                WHERE schedule_id = ?
                """,
                (x_delivered_at, a_schedule_id),
            )

    def mark_failed(self, a_schedule_id: int, a_error_message: str) -> None:
        """Record an unsuccessful delivery without retrying it indefinitely."""
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute(
                """
                UPDATE scheduled_notifications
                SET status = 'failed', error_message = ?
                WHERE schedule_id = ?
                """,
                (a_error_message, a_schedule_id),
            )

    def row_to_schedule(
        self,
        a_row: sqlite3.Row,
        a_status: str | None = None,
    ) -> ScheduledNotification:
        """Convert a SQLite row into an API-ready scheduled notification."""
        x_notification = json.loads(a_row["notification_json"])
        if not isinstance(x_notification, dict):
            raise ValueError("Stored notification payload is not a JSON object.")

        x_run_at = deserialize_datetime(a_row["run_at_utc"])
        if x_run_at is None:
            raise ValueError("Stored schedule has no dispatch time.")

        return ScheduledNotification(
            schedule_id=a_row["schedule_id"],
            run_at=x_run_at,
            notification=x_notification,
            status=a_status or a_row["status"],
            delivered_at=deserialize_datetime(a_row["delivered_at_utc"]),
            error_message=a_row["error_message"],
        )

    def record_forwarding(
        self,
        a_source: str,
        a_method: str,
        a_path: str,
        a_status_code: int,
        a_error_message: str | None,
        a_record_limit: int,
    ) -> None:
        """Persist one forwarding result and retain only the configured record count."""
        x_created_at = serialize_datetime(get_utc_now())
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute(
                """
                INSERT INTO forwarding_logs (
                    created_at_utc, source, method, path, status_code, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    x_created_at,
                    a_source,
                    a_method,
                    a_path,
                    a_status_code,
                    a_error_message,
                ),
            )
            x_connection.execute(
                """
                DELETE FROM forwarding_logs
                WHERE log_id NOT IN (
                    SELECT log_id FROM forwarding_logs
                    ORDER BY log_id DESC
                    LIMIT ?
                )
                """,
                (a_record_limit,),
            )

    def list_forwarding_logs(self) -> list[ForwardingLogRecord]:
        """Return retained forwarding records with newest entries first."""
        with closing(self.connect()) as x_connection, x_connection:
            x_rows = x_connection.execute(
                """
                SELECT log_id, created_at_utc, source, method, path, status_code,
                       error_message
                FROM forwarding_logs
                ORDER BY log_id DESC
                """
            ).fetchall()

        return [
            ForwardingLogRecord(
                log_id=x_row["log_id"],
                created_at=deserialize_datetime(x_row["created_at_utc"]),
                source=x_row["source"],
                method=x_row["method"],
                path=x_row["path"],
                status_code=x_row["status_code"],
                error_message=x_row["error_message"],
            )
            for x_row in x_rows
        ]


class ScheduleWorker:
    """Poll SQLite for due schedules and submit them to AWTRIX on one thread."""

    def __init__(
        self,
        a_store: ScheduleStore,
        a_sender: Callable[[dict[str, object]], object],
    ) -> None:
        """Set the durable store and notification sender used by the worker."""
        self._store = a_store
        self._sender = a_sender
        self._stop_event = Event()
        self._thread = Thread(target=self.run, name="aims-schedule-worker", daemon=True)

    def start(self) -> None:
        """Start the background worker thread once FastAPI has initialized."""
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker to stop and wait briefly for the active loop to finish."""
        self._stop_event.set()
        self._thread.join(timeout=c_schedule_poll_interval_seconds * 2)

    def run(self) -> None:
        """Claim and dispatch due notifications until the application shuts down."""
        while not self._stop_event.is_set():
            try:
                x_schedule = self._store.claim_due(get_utc_now())
                if x_schedule is not None:
                    self.dispatch(x_schedule)
                    continue
            except Exception:
                # A worker boundary must not die because one database operation failed.
                x_logger.exception("Unable to process scheduled AWTRIX notifications.")

            self._stop_event.wait(c_schedule_poll_interval_seconds)

    def dispatch(self, a_schedule: ScheduledNotification) -> None:
        """Submit a claimed notification and store its delivery outcome."""
        try:
            self._sender(a_schedule.notification)
        except Exception as x_exception:
            # Keep failure details for C2 schedule management and later diagnosis.
            self._store.mark_failed(a_schedule.schedule_id, str(x_exception))
            x_logger.warning("Scheduled notification %s failed: %s", a_schedule.schedule_id, x_exception)
        else:
            self._store.mark_delivered(a_schedule.schedule_id)


if __name__ == "__main__":
    pass
