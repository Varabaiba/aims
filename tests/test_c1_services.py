"""Offline behavioral tests for C1 forwarding and schedule persistence."""

# INT
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

# OWN
from awtrix_client import build_target_url, filter_headers
from c2_service import get_default_notification_payload
from cron_schedule_service import CronScheduleStore, get_next_cron_time
from schedule_service import ScheduleStore


class AwtrixClientTests(unittest.TestCase):
    """Verify the pure URL and header behavior of the AWTRIX proxy client."""

    def test_build_target_url_retains_path_and_repeated_queries(self) -> None:
        """The proxy must preserve AWTRIX paths and repeated query values."""
        x_url = build_target_url(
            "http://awtrix.local",
            "/api/v1/files",
            (("tag", "one"), ("tag", "two")),
        )

        self.assertEqual(x_url, "http://awtrix.local/api/v1/files?tag=one&tag=two")

    def test_filter_headers_removes_connection_specific_headers(self) -> None:
        """The proxy must not forward Host and connection-level headers."""
        x_headers = filter_headers(
            (("Host", "aims.local"), ("Content-Type", "application/json"))
        )

        self.assertEqual(x_headers, {"Content-Type": "application/json"})


class ScheduleStoreTests(unittest.TestCase):
    """Verify durable creation, claiming, and delivery state transitions."""

    def test_due_schedule_is_claimed_and_marked_delivered(self) -> None:
        """A due notification should transition from pending to delivered exactly once."""
        with TemporaryDirectory() as x_directory_name:
            x_database_path = Path(x_directory_name) / "schedules.sqlite3"
            x_store = ScheduleStore(x_database_path)
            x_store.initialize()
            x_now = datetime.now(timezone.utc)
            x_created = x_store.create(
                x_now + timedelta(seconds=1),
                {"text": "Reminder", "durationMs": 7000},
            )

            self.assertIsNone(x_store.claim_due(x_now))

            x_claimed = x_store.claim_due(x_now + timedelta(seconds=2))
            self.assertIsNotNone(x_claimed)
            self.assertEqual(x_claimed.schedule_id, x_created.schedule_id)
            self.assertEqual(x_claimed.status, "dispatching")
            self.assertIsNone(x_store.claim_due(x_now + timedelta(seconds=2)))

            x_store.mark_delivered(x_created.schedule_id)
            x_schedules = x_store.list_all()

        self.assertEqual(x_schedules[0].status, "delivered")
        self.assertIsNotNone(x_schedules[0].delivered_at)

    def test_forwarding_log_retains_the_configured_count(self) -> None:
        """Only the newest configured number of forwarding records should remain."""
        with TemporaryDirectory() as x_directory_name:
            x_store = ScheduleStore(Path(x_directory_name) / "logs.sqlite3")
            x_store.initialize()
            x_store.record_forwarding("proxy", "GET", "/api/v1/device", 200, None, 1)
            x_store.record_forwarding("simplified", "GET", "/notify", 200, None, 1)
            x_records = x_store.list_forwarding_logs()

        self.assertEqual(len(x_records), 1)
        self.assertEqual(x_records[0].source, "simplified")

    def test_cron_schedule_persists_its_next_utc_occurrence(self) -> None:
        """A CRON schedule should persist the expression and calculated next run."""
        with TemporaryDirectory() as x_directory_name:
            x_store = CronScheduleStore(Path(x_directory_name) / "cron.sqlite3")
            x_store.initialize()
            x_created = x_store.create("*/15 * * * *", {"text": "Reminder"})
            x_schedules = x_store.list_all()

        self.assertEqual(x_schedules[0].cron_expression, "*/15 * * * *")
        self.assertEqual(x_schedules[0].next_run_at, x_created.next_run_at)

    def test_cron_day_and_weekday_fields_use_standard_or_matching(self) -> None:
        """A restricted day-of-month and weekday pair should match either field."""
        x_next_run = get_next_cron_time(
            "0 9 30 * 1",
            datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(x_next_run, datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc))


class C2DefaultsTests(unittest.TestCase):
    """Verify that C2 exposes the complete documented notification shape."""

    def test_default_notification_has_all_42_fields(self) -> None:
        """The default editor payload must expose every AWTRIX notification field."""
        self.assertEqual(len(get_default_notification_payload()), 42)


if __name__ == "__main__":
    unittest.main()
