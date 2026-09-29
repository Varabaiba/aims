"""AIMS.C1 FastAPI application and its AWTRIX middleware routes."""

# INT
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
import json
from typing import Annotated

# EXT
from fastapi import FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, field_validator

# OWN
from awtrix_client import AwtrixClient, AwtrixRequestError, AwtrixResponse
from cron_schedule_service import CronSchedule, CronScheduleStore, CronScheduleWorker, parse_cron_expression
from schedule_service import (
    ForwardingLogRecord,
    ScheduleStore,
)
from settings_service import SettingsError, load_settings


c_notification_path = "/api/v1/notifications"
c_default_notification_duration_ms = 7000


class ScheduleCreateRequest(BaseModel):
    """Define the public request body for a recurring CRON notification schedule."""

    cron: str
    notification: dict[str, object]

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, a_value: str) -> str:
        """Validate the five-field UTC CRON expression before persisting it."""
        parse_cron_expression(a_value)
        return " ".join(a_value.split())

    @field_validator("notification")
    @classmethod
    def validate_notification(cls, a_value: dict[str, object]) -> dict[str, object]:
        """Reject an empty payload before it enters the scheduler database."""
        if not a_value:
            raise ValueError("notification must be a non-empty JSON object.")

        return a_value


class ScheduleResponse(BaseModel):
    """Describe a persisted recurring schedule returned by the C1 API."""

    schedule_id: int
    cron: str
    notification: dict[str, object]
    status: str
    next_run_at: datetime
    last_run_at: datetime | None
    error_message: str | None


def schedule_to_response(a_schedule: CronSchedule) -> ScheduleResponse:
    """Convert one storage record into the public schedule response model."""
    return ScheduleResponse(
        schedule_id=a_schedule.schedule_id,
        cron=a_schedule.cron_expression,
        notification=a_schedule.notification,
        status=a_schedule.status,
        next_run_at=a_schedule.next_run_at,
        last_run_at=a_schedule.last_run_at,
        error_message=a_schedule.error_message,
    )


def get_client(a_request: Request) -> AwtrixClient:
    """Return the application-scoped AWTRIX client for one incoming request."""
    return a_request.app.state.awtrix_client


def get_schedule_store(a_request: Request) -> ScheduleStore:
    """Return the initialized SQLite store for one incoming request."""
    return a_request.app.state.schedule_store


def record_forwarding(
    a_request: Request,
    a_source: str,
    a_method: str,
    a_path: str,
    a_status_code: int,
    a_error_message: str | None = None,
) -> None:
    """Persist the outcome of an F1 or F2 request for the C2 log page."""
    x_settings = load_settings()
    get_schedule_store(a_request).record_forwarding(
        a_source,
        a_method,
        a_path,
        a_status_code,
        a_error_message,
        x_settings.forwarding_log_record_limit,
    )


def log_record_to_response(a_record: ForwardingLogRecord) -> dict[str, object]:
    """Convert a stored forwarding record into a JSON-safe C1 response object."""
    return {
        "log_id": a_record.log_id,
        "created_at": a_record.created_at.isoformat(),
        "source": a_record.source,
        "method": a_record.method,
        "path": a_record.path,
        "status_code": a_record.status_code,
        "error_message": a_record.error_message,
    }


def response_from_awtrix(a_response: AwtrixResponse) -> Response:
    """Translate a forwarded AWTRIX response into a FastAPI response."""
    return Response(
        content=a_response.body,
        status_code=a_response.status_code,
        headers=a_response.headers,
    )


def send_notification(
    a_client: AwtrixClient,
    a_notification: dict[str, object],
) -> AwtrixResponse:
    """Submit an AWTRIX notification payload and reject target-side errors."""
    x_response = a_client.forward(
        a_method="POST",
        a_path=c_notification_path,
        a_query_items=(),
        a_body=json.dumps(a_notification).encode("utf-8"),
        a_headers=(("Content-Type", "application/json"),),
    )
    if not 200 <= x_response.status_code < 300:
        raise AwtrixRequestError(
            f"AWTRIX rejected the notification with HTTP {x_response.status_code}."
        )

    return x_response


@asynccontextmanager
async def lifespan(a_app: FastAPI) -> AsyncIterator[None]:
    """Initialize SQLite and run the schedule worker for the app lifetime."""
    x_settings = load_settings()
    x_schedule_store = ScheduleStore(x_settings.sqlite_database_path)
    x_schedule_store.initialize()
    x_cron_schedule_store = CronScheduleStore(x_settings.sqlite_database_path)
    x_cron_schedule_store.initialize()
    x_awtrix_client = AwtrixClient(load_settings)
    x_schedule_worker = CronScheduleWorker(
        x_cron_schedule_store,
        lambda a_notification: send_notification(x_awtrix_client, a_notification),
    )
    a_app.state.awtrix_client = x_awtrix_client
    a_app.state.schedule_store = x_schedule_store
    a_app.state.cron_schedule_store = x_cron_schedule_store
    x_schedule_worker.start()

    try:
        yield
    finally:
        x_schedule_worker.stop()


c_app = FastAPI(
    title="AIMS C1",
    description="AWTRIX Informer Middleware Server API.",
    version="0.1.0",
    lifespan=lifespan,
)


@c_app.get("/health")
def get_health() -> dict[str, str]:
    """Return the C1 service health status for launch and deployment checks."""
    return {"status": "ok", "service": "AIMS.C1"}


@c_app.get("/notify")
def get_simple_notification(
    a_request: Request,
    a_text: Annotated[str, Query(min_length=1)],
    a_icon: str | None = None,
    a_duration_ms: Annotated[
        int, Query(ge=1, le=3_600_000)
    ] = c_default_notification_duration_ms,
) -> Response:
    """Translate a compact GET notification request into AWTRIX's POST payload."""
    x_notification: dict[str, object] = {
        "text": a_text,
        "durationMs": a_duration_ms,
    }
    if a_icon:
        x_notification["icon"] = a_icon

    try:
        x_response = send_notification(get_client(a_request), x_notification)
    except (AwtrixRequestError, SettingsError) as x_exception:
        record_forwarding(a_request, "simplified", "GET", "/notify", 502, str(x_exception))
        raise HTTPException(status_code=502, detail=str(x_exception)) from x_exception

    record_forwarding(
        a_request,
        "simplified",
        "GET",
        "/notify",
        x_response.status_code,
    )
    return response_from_awtrix(x_response)


@c_app.post("/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    a_request: Request,
    a_schedule: ScheduleCreateRequest,
) -> ScheduleResponse:
    """Store a recurring AWTRIX notification driven by a UTC CRON expression."""
    try:
        x_schedule = a_request.app.state.cron_schedule_store.create(
            a_schedule.cron,
            a_schedule.notification,
        )
    except ValueError as x_exception:
        raise HTTPException(status_code=422, detail=str(x_exception)) from x_exception

    return schedule_to_response(x_schedule)


@c_app.get("/schedules", response_model=list[ScheduleResponse])
def list_schedules(a_request: Request) -> list[ScheduleResponse]:
    """Return all persisted CRON schedules and their next dispatch time."""
    x_schedules = a_request.app.state.cron_schedule_store.list_all()
    return [schedule_to_response(x_schedule) for x_schedule in x_schedules]


@c_app.delete("/schedules/{a_schedule_id}", status_code=204)
def delete_schedule(a_request: Request, a_schedule_id: int) -> Response:
    """Remove one persisted CRON schedule by identifier."""
    if not a_request.app.state.cron_schedule_store.delete(a_schedule_id):
        raise HTTPException(status_code=404, detail="Schedule was not found.")

    return Response(status_code=204)


@c_app.get("/forwarding-logs")
def list_forwarding_logs(a_request: Request) -> list[dict[str, object]]:
    """Return retained F1 and F2 forwarding records for the C2 log page."""
    x_records = get_schedule_store(a_request).list_forwarding_logs()
    return [log_record_to_response(x_record) for x_record in x_records]


@c_app.api_route(
    "/{a_awtrix_path:path}",
    methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
    include_in_schema=False,
)
async def proxy_awtrix_request(a_request: Request, a_awtrix_path: str) -> Response:
    """Forward an AWTRIX-compatible request that is not handled by a C1 route."""
    try:
        x_response = get_client(a_request).forward(
            a_method=a_request.method,
            a_path=a_awtrix_path,
            a_query_items=a_request.query_params.multi_items(),
            a_body=await a_request.body(),
            a_headers=a_request.headers.items(),
        )
    except (AwtrixRequestError, SettingsError) as x_exception:
        record_forwarding(
            a_request,
            "proxy",
            a_request.method,
            f"/{a_awtrix_path}",
            502,
            str(x_exception),
        )
        raise HTTPException(status_code=502, detail=str(x_exception)) from x_exception

    record_forwarding(
        a_request,
        "proxy",
        a_request.method,
        f"/{a_awtrix_path}",
        x_response.status_code,
    )
    return response_from_awtrix(x_response)


if __name__ == "__main__":
    pass
