import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from threading import Lock


@dataclass
class OperationLog:
    timestamp: str
    operation: str
    endpoint: str
    parameters: Dict[str, Any]
    success: bool
    execution_time_ms: float
    result_summary: Dict[str, Any]
    error_message: Optional[str] = None


class InMemoryLogger:
    def __init__(self, max_logs: int = 1000):
        self.logs: List[OperationLog] = []
        self.max_logs = max_logs
        self._lock = Lock()
    
    def log_operation(
        self,
        operation: str,
        endpoint: str,
        parameters: Dict[str, Any],
        success: bool,
        execution_time_ms: float,
        result_summary: Dict[str, Any],
        error_message: Optional[str] = None
    ):
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_entry = OperationLog(
            timestamp=timestamp,
            operation=operation,
            endpoint=endpoint,
            parameters=self._sanitize_parameters(parameters),
            success=success,
            execution_time_ms=execution_time_ms,
            result_summary=result_summary,
            error_message=error_message
        )
        
        with self._lock:
            self.logs.append(log_entry)
            
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
    
    def get_logs(
        self,
        limit: Optional[int] = None,
        operation: Optional[str] = None,
        success_only: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        with self._lock:
            filtered_logs = self.logs.copy()
        
        if operation:
            filtered_logs = [log for log in filtered_logs if log.operation == operation]
        
        if success_only is not None:
            filtered_logs = [log for log in filtered_logs if log.success == success_only]
        
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            filtered_logs = filtered_logs[:limit]
        
        return [asdict(log) for log in filtered_logs]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            logs = self.logs.copy()
        
        if not logs:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "operations_by_type": {},
                "average_execution_time_ms": 0
            }
        
        total_ops = len(logs)
        successful_ops = sum(1 for log in logs if log.success)
        failed_ops = total_ops - successful_ops
        
        operations_by_type = {}
        total_execution_time = 0
        
        for log in logs:
            operations_by_type[log.operation] = operations_by_type.get(log.operation, 0) + 1
            total_execution_time += log.execution_time_ms
        
        avg_execution_time = total_execution_time / total_ops if total_ops > 0 else 0
        
        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "operations_by_type": operations_by_type,
            "average_execution_time_ms": round(avg_execution_time, 2)
        }
    
    def clear_logs(self):
        with self._lock:
            self.logs.clear()
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in parameters.items():
            if key in ['content', 'fastq_content', 'fasta_content', 'genbank_content']:
                if isinstance(value, str):
                    sanitized[key] = f"<content_length:{len(value)}>"
                else:
                    sanitized[key] = "<content_provided>"
            else:
                sanitized[key] = value
        return sanitized


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()
audit_logger = InMemoryLogger()