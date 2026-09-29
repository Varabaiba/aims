"""Persist and dispatch recurring CRON notification schedules."""

# INT
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from threading import Event, Thread

# OWN
from schedule_service import deserialize_datetime, get_utc_now, serialize_datetime


c_schedule_poll_interval_seconds = 1.0
c_max_cron_search_minutes = 527_040


@dataclass(frozen=True)
class CronSchedule:
    """Represent a persistent UTC CRON notification schedule."""

    schedule_id: int
    cron_expression: str
    notification: dict[str, object]
    status: str
    next_run_at: datetime
    last_run_at: datetime | None
    error_message: str | None


def parse_cron_field(a_value: str, a_minimum: int, a_maximum: int) -> set[int]:
    """Parse one CRON field supporting lists, ranges, and step expressions."""
    x_values: set[int] = set()
    for x_item in a_value.split(","):
        x_base, x_separator, x_step_text = x_item.partition("/")
        x_step = 1
        if x_separator:
            if not x_step_text.isdigit() or int(x_step_text) < 1:
                raise ValueError(f"Invalid CRON step: {x_item}")
            x_step = int(x_step_text)
        if x_base == "*":
            x_start, x_end = a_minimum, a_maximum
        elif "-" in x_base:
            x_start_text, x_end_text = x_base.split("-", maxsplit=1)
            if not x_start_text.isdigit() or not x_end_text.isdigit():
                raise ValueError(f"Invalid CRON range: {x_item}")
            x_start, x_end = int(x_start_text), int(x_end_text)
        elif x_base.isdigit():
            x_start = int(x_base)
            x_end = a_maximum if x_separator else x_start
        else:
            raise ValueError(f"Invalid CRON value: {x_item}")
        if x_start < a_minimum or x_end > a_maximum or x_start > x_end:
            raise ValueError(f"CRON value is outside {a_minimum}-{a_maximum}: {x_item}")
        x_values.update(range(x_start, x_end + 1, x_step))
    return x_values


def parse_cron_expression(a_expression: str) -> tuple[set[int], set[int], set[int], set[int], set[int]]:
    """Validate and parse a five-field UTC CRON expression."""
    x_fields = a_expression.split()
    if len(x_fields) != 5:
        raise ValueError("CRON must have five fields: minute hour day month weekday.")
    return (
        parse_cron_field(x_fields[0], 0, 59),
        parse_cron_field(x_fields[1], 0, 23),
        parse_cron_field(x_fields[2], 1, 31),
        parse_cron_field(x_fields[3], 1, 12),
        parse_cron_field(x_fields[4], 0, 6),
    )


def get_next_cron_time(a_expression: str, a_after: datetime) -> datetime:
    """Return the next UTC minute matching a five-field CRON expression."""
    if a_after.tzinfo is None or a_after.utcoffset() is None:
        raise ValueError("CRON reference time must include a timezone.")
    x_minutes, x_hours, x_days, x_months, x_weekdays = parse_cron_expression(a_expression)
    x_candidate = a_after.astimezone(timezone.utc).replace(second=0, microsecond=0)
    x_candidate += timedelta(minutes=1)
    for x_index in range(c_max_cron_search_minutes):
        x_weekday = (x_candidate.weekday() + 1) % 7
        x_day_matches = x_candidate.day in x_days
        x_weekday_matches = x_weekday in x_weekdays
        # Standard CRON treats two restricted day fields as alternatives.
        if x_days != set(range(1, 32)) and x_weekdays != set(range(0, 7)):
            x_calendar_matches = x_day_matches or x_weekday_matches
        else:
            x_calendar_matches = x_day_matches and x_weekday_matches
        if (
            x_candidate.minute in x_minutes
            and x_candidate.hour in x_hours
            and x_candidate.month in x_months
            and x_calendar_matches
        ):
            return x_candidate
        x_candidate += timedelta(minutes=1)
    raise ValueError("CRON expression has no matching time within one year.")


class CronScheduleStore:
    """Manage recurring schedules in the AIMS SQLite database."""

    def __init__(self, a_database_path: Path) -> None:
        """Set the SQLite file used for persistent CRON schedules."""
        self._database_path = a_database_path

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with named result columns."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        x_connection = sqlite3.connect(self._database_path)
        x_connection.row_factory = sqlite3.Row
        return x_connection

    def initialize(self) -> None:
        """Create the recurring schedule table without altering legacy one-time data."""
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute("""CREATE TABLE IF NOT EXISTS cron_schedules (schedule_id INTEGER PRIMARY KEY AUTOINCREMENT, cron_expression TEXT NOT NULL, notification_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', next_run_at_utc TEXT NOT NULL, last_run_at_utc TEXT, error_message TEXT)""")
            x_connection.execute("UPDATE cron_schedules SET status = 'active' WHERE status = 'dispatching'")

    def create(self, a_expression: str, a_notification: dict[str, object]) -> CronSchedule:
        """Persist a CRON expression and calculate its first UTC dispatch time."""
        x_expression = " ".join(a_expression.split())
        x_next_run_at = get_next_cron_time(x_expression, get_utc_now())
        x_notification_json = json.dumps(a_notification, separators=(",", ":"))
        with closing(self.connect()) as x_connection, x_connection:
            x_cursor = x_connection.execute("INSERT INTO cron_schedules (cron_expression, notification_json, next_run_at_utc) VALUES (?, ?, ?)", (x_expression, x_notification_json, serialize_datetime(x_next_run_at)))
        if x_cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return the created schedule identifier.")
        return CronSchedule(x_cursor.lastrowid, x_expression, a_notification, "active", x_next_run_at, None, None)

    def list_all(self) -> list[CronSchedule]:
        """Return active recurring schedules ordered by their next occurrence."""
        with closing(self.connect()) as x_connection, x_connection:
            x_rows = x_connection.execute("SELECT * FROM cron_schedules ORDER BY next_run_at_utc, schedule_id").fetchall()
        return [self.row_to_schedule(x_row) for x_row in x_rows]

    def delete(self, a_schedule_id: int) -> bool:
        """Delete one recurring schedule by identifier."""
        with closing(self.connect()) as x_connection, x_connection:
            x_cursor = x_connection.execute("DELETE FROM cron_schedules WHERE schedule_id = ?", (a_schedule_id,))
        return x_cursor.rowcount == 1

    def claim_due(self, a_current_time: datetime) -> CronSchedule | None:
        """Atomically claim one active schedule whose next occurrence is due."""
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute("BEGIN IMMEDIATE")
            x_row = x_connection.execute("SELECT * FROM cron_schedules WHERE status = 'active' AND next_run_at_utc <= ? ORDER BY next_run_at_utc LIMIT 1", (serialize_datetime(a_current_time),)).fetchone()
            if x_row is None:
                return None
            x_connection.execute("UPDATE cron_schedules SET status = 'dispatching' WHERE schedule_id = ?", (x_row["schedule_id"],))
        return self.row_to_schedule(x_row, a_status="dispatching")

    def complete_run(self, a_schedule: CronSchedule, a_error_message: str | None = None) -> None:
        """Advance a schedule to its next CRON occurrence after one delivery attempt."""
        x_now = get_utc_now()
        x_next_run_at = get_next_cron_time(a_schedule.cron_expression, x_now)
        with closing(self.connect()) as x_connection, x_connection:
            x_connection.execute("UPDATE cron_schedules SET status = 'active', next_run_at_utc = ?, last_run_at_utc = ?, error_message = ? WHERE schedule_id = ?", (serialize_datetime(x_next_run_at), serialize_datetime(x_now), a_error_message, a_schedule.schedule_id))

    def row_to_schedule(self, a_row: sqlite3.Row, a_status: str | None = None) -> CronSchedule:
        """Convert one SQLite row into a recurring schedule object."""
        x_notification = json.loads(a_row["notification_json"])
        x_next_run_at = deserialize_datetime(a_row["next_run_at_utc"])
        if not isinstance(x_notification, dict) or x_next_run_at is None:
            raise ValueError("Stored CRON schedule is invalid.")
        return CronSchedule(a_row["schedule_id"], a_row["cron_expression"], x_notification, a_status or a_row["status"], x_next_run_at, deserialize_datetime(a_row["last_run_at_utc"]), a_row["error_message"])


class CronScheduleWorker:
    """Dispatch due recurring schedules from a dedicated background thread."""

    def __init__(self, a_store: CronScheduleStore, a_sender: Callable[[dict[str, object]], object]) -> None:
        """Set the persistent schedule store and AWTRIX notification sender."""
        self._store = a_store
        self._sender = a_sender
        self._stop_event = Event()
        self._thread = Thread(target=self.run, name="aims-cron-schedule-worker", daemon=True)

    def start(self) -> None:
        """Start the schedule worker thread."""
        self._thread.start()

    def stop(self) -> None:
        """Stop the worker after its current polling cycle."""
        self._stop_event.set()
        self._thread.join(timeout=c_schedule_poll_interval_seconds * 2)

    def run(self) -> None:
        """Claim and dispatch every due CRON occurrence until stopped."""
        while not self._stop_event.is_set():
            x_schedule = self._store.claim_due(get_utc_now())
            if x_schedule is None:
                self._stop_event.wait(c_schedule_poll_interval_seconds)
                continue
            try:
                self._sender(x_schedule.notification)
            except Exception as x_exception:
                self._store.complete_run(x_schedule, str(x_exception))
            else:
                self._store.complete_run(x_schedule)


if __name__ == "__main__":
    pass
