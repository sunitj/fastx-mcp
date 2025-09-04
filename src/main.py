from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
from contextlib import asynccontextmanager

from src.api.convert import router as convert_router
from src.api.manipulate import router as manipulate_router
from src.api.seqkit import router as seqkit_router
from src.api.logs import router as logs_router
from src.mcp.endpoints import router as mcp_router
from src.utils.logging import logger, audit_logger
from src.core.seqkit_wrapper import validate_seqkit_installation
from src.core.config import load_mcp_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastX-MCP Server...")

    seqkit_available = validate_seqkit_installation()
    if seqkit_available:
        logger.info("seqkit installation validated successfully")
    else:
        logger.warning("seqkit not found - seqkit operations will be unavailable")

    yield

    logger.info("Shutting down FastX-MCP Server...")


app = FastAPI(
    title="FastX-MCP Server",
    description="MCP Server for FASTA/FASTQ manipulation and file conversion",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


mcp_config = load_mcp_config()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FastX-MCP Server",
        version="1.0.0",
        description="MCP Server for FASTA/FASTQ manipulation and file conversion",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000

        audit_logger.log_operation(
            operation="http_request",
            endpoint=str(request.url.path),
            parameters={
                "method": request.method,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else "unknown",
            },
            success=response.status_code < 400,
            execution_time_ms=process_time,
            result_summary={
                "status_code": response.status_code,
                "response_time_ms": round(process_time, 2),
            },
        )

        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000

        audit_logger.log_operation(
            operation="http_request",
            endpoint=str(request.url.path),
            parameters={
                "method": request.method,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else "unknown",
            },
            success=False,
            execution_time_ms=process_time,
            result_summary={},
            error_message=str(e),
        )

        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": time.time(),
        },
    )


@app.get("/")
async def root():
    return {
        "message": "FastX-MCP Server",
        "version": "1.0.0",
        "description": "MCP Server for FASTA/FASTQ manipulation and file conversion",
        "endpoints": {
            "convert": "/convert/genbank-to-fasta",
            "manipulate": "/manipulate/reverse-complement",
            "seqkit": "/seqkit/stats",
            "logs": "/logs",
        },
    }


@app.get("/health")
async def health_check():
    seqkit_available = validate_seqkit_installation()

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {"biopython": True, "seqkit": seqkit_available},
    }


app.include_router(convert_router, prefix="/convert", tags=["conversion"])
app.include_router(manipulate_router, prefix="/manipulate", tags=["manipulation"])
app.include_router(seqkit_router, prefix="/seqkit", tags=["seqkit"])
app.include_router(logs_router, prefix="/logs", tags=["logging"])
app.include_router(mcp_router, prefix="/mcp", tags=["MCP"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
