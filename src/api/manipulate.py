from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import time

from src.core.manipulators import (
    reverse_complement_fasta, 
    extract_subsequence, 
    get_fasta_summary,
    ManipulationError
)
from src.utils.validators import (
    validate_input_format, 
    validate_content_size, 
    validate_fasta_format,
    validate_coordinates,
    validate_sequence_id,
    ValidationError
)
from src.utils.logging import audit_logger, logger


router = APIRouter()


class ReverseComplementRequest(BaseModel):
    content: str = Field(..., description="FASTA file content")
    input_format: Literal["string", "base64"] = Field(
        default="string", 
        description="Format of input content"
    )
    include_summary: bool = Field(
        default=False, 
        description="Include manipulation summary in response"
    )


class ReverseComplementResponse(BaseModel):
    fasta_content: str
    success: bool = True
    manipulation_summary: Optional[dict] = None
    execution_time_ms: float


class SubsequenceRequest(BaseModel):
    content: str = Field(..., description="FASTA file content")
    sequence_id: str = Field(..., description="ID of sequence to extract from")
    start: int = Field(..., ge=0, description="Start position (0-based, inclusive)")
    end: int = Field(..., gt=0, description="End position (0-based, exclusive)")
    input_format: Literal["string", "base64"] = Field(
        default="string", 
        description="Format of input content"
    )


class SubsequenceResponse(BaseModel):
    fasta_content: str
    success: bool = True
    subsequence_info: dict
    execution_time_ms: float


@router.post("/reverse-complement", response_model=ReverseComplementResponse)
async def reverse_complement(request: ReverseComplementRequest):
    start_time = time.time()
    operation = "reverse_complement"
    
    try:
        validate_input_format(request.input_format)
        validate_content_size(request.content)
        
        if request.input_format == "string":
            validate_fasta_format(request.content)
        
        result = reverse_complement_fasta(
            request.content, 
            input_format=request.input_format
        )
        
        manipulation_summary = None
        if request.include_summary:
            manipulation_summary = get_fasta_summary(
                request.content, 
                input_format=request.input_format
            )
        
        execution_time = (time.time() - start_time) * 1000
        
        response = ReverseComplementResponse(
            fasta_content=result,
            manipulation_summary=manipulation_summary,
            execution_time_ms=round(execution_time, 2)
        )
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/reverse-complement",
            parameters={
                "input_format": request.input_format,
                "include_summary": request.include_summary,
                "content_length": len(request.content)
            },
            success=True,
            execution_time_ms=execution_time,
            result_summary={
                "output_length": len(result),
                "manipulation_summary": manipulation_summary
            }
        )
        
        logger.info(f"Reverse complement completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Validation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/reverse-complement",
            parameters={
                "input_format": request.input_format,
                "include_summary": request.include_summary,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.warning(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
        
    except ManipulationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Manipulation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/reverse-complement",
            parameters={
                "input_format": request.input_format,
                "include_summary": request.include_summary,
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
            endpoint="/manipulate/reverse-complement",
            parameters={
                "input_format": request.input_format,
                "include_summary": request.include_summary,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/extract-subsequence", response_model=SubsequenceResponse)
async def extract_subsequence_endpoint(request: SubsequenceRequest):
    start_time = time.time()
    operation = "extract_subsequence"
    
    try:
        validate_input_format(request.input_format)
        validate_content_size(request.content)
        validate_sequence_id(request.sequence_id)
        validate_coordinates(request.start, request.end)
        
        if request.input_format == "string":
            validate_fasta_format(request.content)
        
        result = extract_subsequence(
            request.content,
            request.sequence_id,
            request.start,
            request.end,
            input_format=request.input_format
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        subsequence_info = {
            "sequence_id": request.sequence_id,
            "start": request.start,
            "end": request.end,
            "length": request.end - request.start
        }
        
        response = SubsequenceResponse(
            fasta_content=result,
            subsequence_info=subsequence_info,
            execution_time_ms=round(execution_time, 2)
        )
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/extract-subsequence",
            parameters={
                "input_format": request.input_format,
                "sequence_id": request.sequence_id,
                "start": request.start,
                "end": request.end,
                "content_length": len(request.content)
            },
            success=True,
            execution_time_ms=execution_time,
            result_summary={
                "output_length": len(result),
                "subsequence_length": request.end - request.start
            }
        )
        
        logger.info(f"Subsequence extraction completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Validation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/extract-subsequence",
            parameters={
                "input_format": request.input_format,
                "sequence_id": request.sequence_id,
                "start": request.start,
                "end": request.end,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.warning(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
        
    except ManipulationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Manipulation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/manipulate/extract-subsequence",
            parameters={
                "input_format": request.input_format,
                "sequence_id": request.sequence_id,
                "start": request.start,
                "end": request.end,
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
            endpoint="/manipulate/extract-subsequence",
            parameters={
                "input_format": request.input_format,
                "sequence_id": request.sequence_id,
                "start": request.start,
                "end": request.end,
                "content_length": len(request.content) if request.content else 0
            },
            success=False,
            execution_time_ms=execution_time,
            result_summary={},
            error_message=error_msg
        )
        
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/operations")
async def get_supported_operations():
    return {
        "supported_operations": [
            {
                "operation": "reverse-complement",
                "endpoint": "/manipulate/reverse-complement",
                "description": "Generate reverse complement of all sequences in FASTA file",
                "input_format": "FASTA"
            },
            {
                "operation": "extract-subsequence",
                "endpoint": "/manipulate/extract-subsequence",
                "description": "Extract subsequence by coordinates from a specific sequence",
                "input_format": "FASTA"
            }
        ],
        "input_formats": ["string", "base64"],
        "features": [
            "Manipulation summary statistics",
            "Multiple sequence support",
            "Coordinate-based extraction",
            "Error handling and validation"
        ]
    }