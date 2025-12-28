"""Utility endpoints for health and metrics.

This router exposes a simple health check endpoint and a metrics
endpoint compatible with Prometheus.  The metrics endpoint will
automatically generate a text representation of registered metrics
if the :mod:`prometheus_client` library is installed.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
except Exception:
    generate_latest = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

router = APIRouter(prefix="", tags=["utilities"])


@router.get("/health", summary="Health check", response_description="Service status")
def health_check() -> dict[str, str]:
    """Return a simple status message.

    This endpoint can be used by load balancers or monitoring systems
    to verify that the service is running.  It always returns a
    200 OK response with a JSON body.
    """
    return {"status": "ok"}


@router.get("/metrics", summary="Prometheus metrics")
def metrics() -> Response:
    """Expose Prometheus metrics for scraping.

    If the :mod:`prometheus_client` library is not available, this
    endpoint returns an empty 200 response.  When available, it
    returns the latest metrics in the Prometheus text exposition
    format.
    """
    if generate_latest is None:
        return Response(content="", media_type=CONTENT_TYPE_LATEST)
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)