from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import time

from src.core.converters import genbank_to_fasta, get_conversion_summary, ConversionError
from src.utils.validators import (
    validate_input_format, 
    validate_content_size, 
    validate_genbank_format,
    ValidationError
)
from src.utils.logging import audit_logger, logger


router = APIRouter()


class GenBankToFastaRequest(BaseModel):
    content: str = Field(..., description="GenBank file content")
    input_format: Literal["string", "base64"] = Field(
        default="string", 
        description="Format of input content"
    )
    include_summary: bool = Field(
        default=False, 
        description="Include conversion summary in response"
    )


class GenBankToFastaResponse(BaseModel):
    fasta_content: str
    success: bool = True
    conversion_summary: Optional[dict] = None
    execution_time_ms: float


@router.post("/genbank-to-fasta", response_model=GenBankToFastaResponse)
async def convert_genbank_to_fasta(request: GenBankToFastaRequest):
    start_time = time.time()
    operation = "genbank_to_fasta_conversion"
    
    try:
        validate_input_format(request.input_format)
        validate_content_size(request.content)
        
        if request.input_format == "string":
            validate_genbank_format(request.content)
        
        fasta_result = genbank_to_fasta(
            request.content, 
            input_format=request.input_format
        )
        
        conversion_summary = None
        if request.include_summary:
            conversion_summary = get_conversion_summary(
                request.content, 
                input_format=request.input_format
            )
        
        execution_time = (time.time() - start_time) * 1000
        
        response = GenBankToFastaResponse(
            fasta_content=fasta_result,
            conversion_summary=conversion_summary,
            execution_time_ms=round(execution_time, 2)
        )
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/convert/genbank-to-fasta",
            parameters={
                "input_format": request.input_format,
                "include_summary": request.include_summary,
                "content_length": len(request.content)
            },
            success=True,
            execution_time_ms=execution_time,
            result_summary={
                "output_length": len(fasta_result),
                "conversion_summary": conversion_summary
            }
        )
        
        logger.info(f"GenBank to FASTA conversion completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Validation error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/convert/genbank-to-fasta",
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
        
    except ConversionError as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Conversion error: {str(e)}"
        
        audit_logger.log_operation(
            operation=operation,
            endpoint="/convert/genbank-to-fasta",
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
            endpoint="/convert/genbank-to-fasta",
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


@router.get("/formats")
async def get_supported_formats():
    return {
        "supported_conversions": [
            {
                "from": "genbank",
                "to": "fasta",
                "endpoint": "/convert/genbank-to-fasta",
                "description": "Convert GenBank format to FASTA format"
            }
        ],
        "input_formats": ["string", "base64"],
        "features": [
            "Conversion summary statistics",
            "Multiple record support",
            "Error handling and validation"
        ]
    }