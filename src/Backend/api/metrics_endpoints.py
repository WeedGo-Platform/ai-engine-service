"""
Prometheus Metrics API Endpoints
Exposes metrics for monitoring and observability
"""

import logging
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus exposition format
    Accessible at: http://localhost:5024/metrics

    Metrics include:
    - WebSocket connections and messages
    - Signup flow progress and outcomes
    - Verification code statistics
    - Admin review metrics
    - Redis operation metrics
    - API request metrics
    """
    try:
        # Generate Prometheus metrics
        metrics_output = generate_latest()

        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}",
            media_type="text/plain",
            status_code=500
        )


@router.get("/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {
        "status": "healthy",
        "service": "prometheus_metrics",
        "endpoint": "/metrics"
    }
