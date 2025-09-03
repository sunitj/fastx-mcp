from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import time

from src.utils.logging import audit_logger, logger


router = APIRouter()


class LogsResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total_count: int
    filtered_count: int
    query_time_ms: float


class StatsResponse(BaseModel):
    stats: Dict[str, Any]
    query_time_ms: float


@router.get("/", response_model=LogsResponse)
async def get_logs(
    limit: Optional[int] = Query(default=50, ge=1, le=1000, description="Maximum number of logs to return"),
    operation: Optional[str] = Query(default=None, description="Filter by operation type"),
    success_only: Optional[bool] = Query(default=None, description="Filter by success status")
):
    start_time = time.time()
    
    try:
        all_logs = audit_logger.get_logs()
        total_count = len(all_logs)
        
        filtered_logs = audit_logger.get_logs(
            limit=limit,
            operation=operation,
            success_only=success_only
        )
        
        query_time = (time.time() - start_time) * 1000
        
        response = LogsResponse(
            logs=filtered_logs,
            total_count=total_count,
            filtered_count=len(filtered_logs),
            query_time_ms=round(query_time, 2)
        )
        
        audit_logger.log_operation(
            operation="get_logs",
            endpoint="/logs",
            parameters={
                "limit": limit,
                "operation": operation,
                "success_only": success_only
            },
            success=True,
            execution_time_ms=query_time,
            result_summary={
                "logs_returned": len(filtered_logs),
                "total_logs": total_count
            }
        )
        
        logger.info(f"Logs query completed in {query_time:.2f}ms, returned {len(filtered_logs)} logs")
        
        return response
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        error_msg = f"Failed to retrieve logs: {str(e)}"
        
        audit_logger.log_operation(
            operation="get_logs",
            endpoint="/logs",
            parameters={
                "limit": limit,
                "operation": operation,
                "success_only": success_only
            },
            success=False,
            execution_time_ms=query_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise


@router.get("/stats", response_model=StatsResponse)
async def get_log_stats():
    start_time = time.time()
    
    try:
        stats = audit_logger.get_stats()
        query_time = (time.time() - start_time) * 1000
        
        response = StatsResponse(
            stats=stats,
            query_time_ms=round(query_time, 2)
        )
        
        audit_logger.log_operation(
            operation="get_log_stats",
            endpoint="/logs/stats",
            parameters={},
            success=True,
            execution_time_ms=query_time,
            result_summary={
                "total_operations": stats.get("total_operations", 0),
                "success_rate": stats.get("success_rate", 0)
            }
        )
        
        logger.info(f"Log stats query completed in {query_time:.2f}ms")
        
        return response
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        error_msg = f"Failed to retrieve log stats: {str(e)}"
        
        audit_logger.log_operation(
            operation="get_log_stats",
            endpoint="/logs/stats",
            parameters={},
            success=False,
            execution_time_ms=query_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise


@router.delete("/clear")
async def clear_logs():
    start_time = time.time()
    
    try:
        logs_before = len(audit_logger.get_logs())
        audit_logger.clear_logs()
        
        query_time = (time.time() - start_time) * 1000
        
        audit_logger.log_operation(
            operation="clear_logs",
            endpoint="/logs/clear",
            parameters={},
            success=True,
            execution_time_ms=query_time,
            result_summary={
                "logs_cleared": logs_before
            }
        )
        
        logger.info(f"Cleared {logs_before} logs in {query_time:.2f}ms")
        
        return {
            "success": True,
            "message": f"Cleared {logs_before} log entries",
            "execution_time_ms": round(query_time, 2)
        }
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        error_msg = f"Failed to clear logs: {str(e)}"
        
        audit_logger.log_operation(
            operation="clear_logs",
            endpoint="/logs/clear",
            parameters={},
            success=False,
            execution_time_ms=query_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise


@router.get("/operations")
async def get_available_operations():
    try:
        logs = audit_logger.get_logs()
        operations = set()
        
        for log in logs:
            operations.add(log.get("operation", "unknown"))
        
        return {
            "available_operations": sorted(list(operations)),
            "total_unique_operations": len(operations),
            "description": "List of all operation types that have been logged"
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve operations: {str(e)}"
        logger.error(error_msg)
        raise


@router.get("/info")
async def get_logging_info():
    try:
        stats = audit_logger.get_stats()
        
        return {
            "logging_system": "In-Memory Audit Logger",
            "max_logs": audit_logger.max_logs,
            "current_log_count": stats.get("total_operations", 0),
            "features": [
                "Operation tracking",
                "Performance monitoring", 
                "Error logging",
                "Parameter sanitization",
                "Statistical analysis"
            ],
            "endpoints": [
                {
                    "endpoint": "/logs",
                    "method": "GET",
                    "description": "Retrieve audit logs with filtering options"
                },
                {
                    "endpoint": "/logs/stats",
                    "method": "GET", 
                    "description": "Get aggregated statistics about operations"
                },
                {
                    "endpoint": "/logs/clear",
                    "method": "DELETE",
                    "description": "Clear all audit logs"
                },
                {
                    "endpoint": "/logs/operations",
                    "method": "GET",
                    "description": "List all available operation types"
                }
            ]
        }
        
    except Exception as e:
        error_msg = f"Failed to retrieve logging info: {str(e)}"
        logger.error(error_msg)
        raise