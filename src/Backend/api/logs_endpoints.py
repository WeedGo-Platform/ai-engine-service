"""
Logs API Endpoints
Provides secure access to Elasticsearch logs for admin dashboard
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/logs", tags=["logs"])

# Elasticsearch configuration
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX = "ai-engine-logs"

# Initialize Elasticsearch client
try:
    es_client = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    logger.info(f"Elasticsearch client initialized: {ES_HOST}:{ES_PORT}")
except Exception as e:
    logger.error(f"Failed to initialize Elasticsearch client: {e}")
    es_client = None


@router.post("/search")
async def search_logs(
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(50)
):
    """
    Search logs in Elasticsearch with various filters
    """
    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch service unavailable")

    try:
        # Build Elasticsearch query
        must = []
        should = []

        # Date range filter
        if start_date or end_date:
            range_query = {}
            if start_date:
                range_query["gte"] = start_date
            if end_date:
                range_query["lte"] = end_date
            must.append({"range": {"@timestamp": range_query}})

        # Level filter
        if level and level != "all":
            must.append({"term": {"level.keyword": level.upper()}})

        # Correlation ID filter
        if correlation_id:
            must.append({"term": {"correlation_id.keyword": correlation_id}})

        # Tenant ID filter
        if tenant_id:
            must.append({"term": {"tenant_id.keyword": tenant_id}})

        # Store ID filter
        if store_id:
            must.append({"term": {"store_id.keyword": store_id}})

        # User ID filter
        if user_id:
            must.append({"term": {"user_id.keyword": user_id}})

        # Session ID filter
        if session_id:
            must.append({"term": {"session_id.keyword": session_id}})

        # Service filter
        if service:
            must.append({"term": {"service.keyword": service}})

        # Search filter (multi-field)
        if search:
            should.extend([
                {"match": {"message": search}},
                {"match": {"logger": search}},
                {"match": {"module": search}},
                {"match": {"function": search}}
            ])

        # Build final query
        query = {
            "bool": {
                "must": must if must else [{"match_all": {}}]
            }
        }

        if should:
            query["bool"]["should"] = should
            query["bool"]["minimum_should_match"] = 1

        # Calculate from offset
        from_offset = (page - 1) * page_size

        search_body = {
            "query": query,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "from": from_offset,
            "size": page_size
        }

        # Use date-based index pattern
        index_pattern = f"{ES_INDEX}-*"

        # Execute search
        response = es_client.search(
            index=index_pattern,
            body=search_body
        )

        # Format response
        return {
            "hits": response["hits"]["hits"],
            "total": response["hits"]["total"]["value"],
            "took": response["took"]
        }

    except Exception as e:
        logger.error(f"Error searching logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching logs: {str(e)}")


@router.get("/stats")
async def get_log_stats():
    """
    Get statistics about logs
    """
    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch service unavailable")

    try:
        index_pattern = f"{ES_INDEX}-*"

        # Get total count
        count_response = es_client.count(index=index_pattern)

        # Get log level distribution
        agg_response = es_client.search(
            index=index_pattern,
            body={
                "size": 0,
                "aggs": {
                    "levels": {
                        "terms": {"field": "level.keyword"}
                    },
                    "services": {
                        "terms": {"field": "service.keyword"}
                    }
                }
            }
        )

        return {
            "total_logs": count_response["count"],
            "level_distribution": {
                bucket["key"]: bucket["doc_count"]
                for bucket in agg_response["aggregations"]["levels"]["buckets"]
            },
            "service_distribution": {
                bucket["key"]: bucket["doc_count"]
                for bucket in agg_response["aggregations"]["services"]["buckets"]
            }
        }

    except Exception as e:
        logger.error(f"Error getting log stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting log stats: {str(e)}")


@router.get("/health")
async def check_elasticsearch_health():
    """
    Check Elasticsearch health
    """
    if not es_client:
        return {"status": "unavailable", "message": "Elasticsearch client not initialized"}

    try:
        health = es_client.cluster.health()
        return {
            "status": "available",
            "cluster_status": health["status"],
            "number_of_nodes": health["number_of_nodes"]
        }
    except Exception as e:
        logger.error(f"Error checking Elasticsearch health: {e}")
        return {"status": "error", "message": str(e)}
