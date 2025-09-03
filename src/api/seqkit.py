from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any, Dict
import time

from src.core.seqkit_wrapper import (
    run_seqkit_stats, 
    run_seqkit_command, 
    validate_seqkit_installation,
    get_seqkit_version,
    SeqkitError
)
from src.utils.validators import (
    validate_input_format, 
    validate_content_size, 
    validate_fastq_format,
    validate_output_format,
    ValidationError
)
from src.utils.logging import audit_logger, logger


router = APIRouter()


class SeqkitStatsRequest(BaseModel):
    content: str = Field(..., description="FASTQ file content")
    input_format: Literal["string", "base64"] = Field(
        default="string", 
        description="Format of input content"
    )
    output_format: Literal["json", "text"] = Field(
        default="json", 
        description="Format of output statistics"
    )


class SeqkitStatsResponse(BaseModel):
    statistics: Dict[str, Any]
    success: bool = True
    execution_time_ms: float


class SeqkitCommandRequest(BaseModel):
    content: str = Field(..., description="FASTQ file content")
    command: str = Field(..., description="seqkit command to run")
    args: Optional[List[str]] = Field(default=None, description="Additional command arguments")
    input_format: Literal["string", "base64"] = Field(
        default="string", 
        description="Format of input content"
    )


class SeqkitCommandResponse(BaseModel):
    output: str
    success: bool = True
    execution_time_ms: float


@router.post("/stats", response_model=SeqkitStatsResponse)
async def get_fastq_stats(request: SeqkitStatsRequest):
    start_time = time.time()
    operation = "seqkit_stats"
    
    try:
        if not validate_seqkit_installation():
            raise HTTPException(
                status_code=503, 
                detail="seqkit is not available on this server"
            )
        
        validate_input_format(request.input_format)
        validate_output_format(request.output_format)
        validate_content_size(request.content)
        
        if request.input_format == "string":
            validate_fastq_format(request.content)
        
        stats_result = run_seqkit_stats(
            request.content,
            input_format=request.input_format,
            output_format=request.output_format
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        response = SeqkitStatsResponse(
            statistics=stats_result,
            execution_time_ms=round(execution_time, 2)
        )
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/stats",
            parameters={
                "input_format": request.input_format,
                "output_format": request.output_format,
                "content_length": len(request.content)
            },
            success=True,
            execution_time_ms=execution_time,
            result_summary={
                "statistics_generated": True,
                "output_format": request.output_format
            }
        )
        
        logger.info(f"seqkit stats completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Validation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/stats",
            parameters={
                "input_format": request.input_format,
                "output_format": request.output_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.warning(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
        
    except SeqkitError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"seqkit error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/stats",
            parameters={
                "input_format": request.input_format,
                "output_format": request.output_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=422, detail=error_msg)
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Unexpected error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/stats",
            parameters={
                "input_format": request.input_format,
                "output_format": request.output_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/command", response_model=SeqkitCommandResponse)
async def run_seqkit_command_endpoint(request: SeqkitCommandRequest):
    start_time = time.time()
    operation = f"seqkit_{request.command}"
    
    try:
        if not validate_seqkit_installation():
            raise HTTPException(
                status_code=503, 
                detail="seqkit is not available on this server"
            )
        
        validate_input_format(request.input_format)
        validate_content_size(request.content)
        
        if request.input_format == "string":
            validate_fastq_format(request.content)
        
        allowed_commands = [
            "stats", "head", "tail", "sample", "seq", "subseq", 
            "grep", "locate", "rmdup", "common", "split", "sort",
            "shuffle", "sliding", "range", "restart", "concat",
            "tab2fx", "fx2tab", "translate", "watch"
        ]
        
        if request.command not in allowed_commands:
            raise ValidationError(f"Command '{request.command}' not allowed. Allowed commands: {allowed_commands}")
        
        result = run_seqkit_command(
            request.content,
            request.command,
            args=request.args or [],
            input_format=request.input_format
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        response = SeqkitCommandResponse(
            output=result,
            execution_time_ms=round(execution_time, 2)
        )
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/command",
            parameters={
                "command": request.command,
                "args": request.args,
                "input_format": request.input_format,
                "content_length": len(request.content)
            },
            success=True,
            execution_time_ms=execution_time,
            result_summary={
                "output_length": len(result),
                "command": request.command
            }
        )
        
        logger.info(f"seqkit {request.command} completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Validation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/command",
            parameters={
                "command": request.command,
                "args": request.args,
                "input_format": request.input_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.warning(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
        
    except SeqkitError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"seqkit error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/command",
            parameters={
                "command": request.command,
                "args": request.args,
                "input_format": request.input_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=422, detail=error_msg)
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Unexpected error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/seqkit/command",
            parameters={
                "command": request.command,
                "args": request.args,
                "input_format": request.input_format,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/info")
async def get_seqkit_info():
    installation_status = validate_seqkit_installation()
    version = get_seqkit_version() if installation_status else None
    
    return {
        "seqkit_available": installation_status,
        "seqkit_version": version,
        "supported_commands": [
            "stats", "head", "tail", "sample", "seq", "subseq", 
            "grep", "locate", "rmdup", "common", "split", "sort",
            "shuffle", "sliding", "range", "restart", "concat",
            "tab2fx", "fx2tab", "translate", "watch"
        ],
        "endpoints": [
            {
                "endpoint": "/seqkit/stats",
                "description": "Generate FASTQ statistics using seqkit stats"
            },
            {
                "endpoint": "/seqkit/command",
                "description": "Run custom seqkit commands"
            }
        ]
    }