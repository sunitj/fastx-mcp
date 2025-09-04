# FastX-MCP Server
#
## MCP Protocol Support

This server supports MCP protocol configuration via `mcp_config.yaml` and exposes its OpenAPI schema at `/openapi.yaml`.

### MCP Configuration
- See `mcp_config.yaml` for protocol version, enabled features, and options for authentication/logging.
- You can extend this file for custom deployment needs.

### OpenAPI Schema
- The full OpenAPI specification is available at: `GET /openapi.yaml`
- Use this for MCP client integration, validation, or documentation.

### Environment Variables
- Configure secrets and environment variables using a `.env` file (local) or Docker secrets (production).
- Document all required variables in this README for clarity.

A Python-based MCP server for FASTA/FASTQ manipulation and file conversion, containerized with Docker. This server provides in-memory tools for bioinformatics file format conversion and sequence operations using Biopython and seqkit.

## Features

### File Conversion
- **GenBank to FASTA**: Convert GenBank format files to FASTA format
- Support for both string and base64 input formats
- Conversion summary statistics

### Sequence Manipulation
- **Reverse Complement**: Generate reverse complement of DNA sequences in FASTA files
- **Subsequence Extraction**: Extract specific regions from sequences by coordinates
- Support for multiple sequences in a single file

### seqkit Integration
- **FASTQ Statistics**: Generate comprehensive statistics for FASTQ files
- **Custom Commands**: Run various seqkit operations (head, tail, sample, etc.)
- JSON and text output formats

### Additional Features
- **In-Memory Operations**: All file manipulations performed in memory (no disk I/O)
- **Audit Logging**: Complete operation tracking with timestamps and performance metrics
- **Error Handling**: Comprehensive validation and error reporting
- **Docker Support**: Easy deployment with pre-configured dependencies

## Quick Start

### Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build -t fastx-mcp .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 fastx-mcp
   ```

3. **Access the API:**
   - Server: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install seqkit** (required for seqkit operations):
   ```bash
   # Using conda/bioconda (recommended)
   conda install -c bioconda seqkit
   
   # Or download binary from: https://github.com/shenwei356/seqkit/releases
   ```

3. **Run the server:**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Usage

### 1. File Conversion

#### GenBank to FASTA
```bash
curl -X POST "http://localhost:8000/convert/genbank-to-fasta" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "LOCUS TEST_SEQUENCE 100 bp DNA...",
    "input_format": "string",
    "include_summary": true
  }'
```

**Response:**
```json
{
  "fasta_content": ">TEST_SEQUENCE\nATGCAGCTATT...",
  "success": true,
  "conversion_summary": {
    "record_count": 1,
    "total_length": 100,
    "record_ids": ["TEST_SEQUENCE"]
  },
  "execution_time_ms": 45.2
}
```

### 2. Sequence Manipulation

#### Reverse Complement
```bash
curl -X POST "http://localhost:8000/manipulate/reverse-complement" \
  -H "Content-Type: application/json" \
  -d '{
    "content": ">seq1\nATGCAGCTATT\n>seq2\nGGCCTAGG",
    "input_format": "string",
    "include_summary": true
  }'
```

#### Extract Subsequence
```bash
curl -X POST "http://localhost:8000/manipulate/extract-subsequence" \
  -H "Content-Type: application/json" \
  -d '{
    "content": ">seq1\nATGCAGCTATTGGCCTAGG",
    "sequence_id": "seq1",
    "start": 5,
    "end": 10,
    "input_format": "string"
  }'
```

### 3. seqkit Operations

#### FASTQ Statistics
```bash
curl -X POST "http://localhost:8000/seqkit/stats" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "@read1\nATGCAGCTATT\n+\nIIIIIIIIIII",
    "input_format": "string",
    "output_format": "json"
  }'
```
#### FASTQ Statistics from a File (base64)

To compute statistics for a FASTQ file, encode the file in base64 and send it in the request. Note: The base64 command usage differs between macOS and Linux.

**macOS:**
```bash
curl -X POST "http://localhost:8000/seqkit/stats" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "'"$(base64 < /path/to/your.fastq | tr -d '\n')"'",
    "input_format": "base64",
    "output_format": "json"
  }'
```

**Linux:**
```bash
curl -X POST "http://localhost:8000/seqkit/stats" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "'"$(base64 -w 0 /path/to/your.fastq)"'",
    "input_format": "base64",
    "output_format": "json"
  }'
```

Replace `/path/to/your.fastq` with your FASTQ file path. This ensures the file content is safely transmitted and processed by the MCP server.

#### Custom seqkit Commands
```bash
curl -X POST "http://localhost:8000/seqkit/command" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "@read1\nATGCAGCTATT\n+\nIIIIIIIIIII",
    "command": "head",
    "args": ["-n", "1"],
    "input_format": "string"
  }'
```

### 4. Logging and Monitoring

#### Get Audit Logs
```bash
curl "http://localhost:8000/logs/?limit=10&success_only=true"
```

#### Get Statistics
```bash
curl "http://localhost:8000/logs/stats"
```

#### Health Check
```bash
curl "http://localhost:8000/health"
```

## Input Formats

The server supports two input formats for all operations:

- **string**: Direct text content
- **base64**: Base64-encoded content (useful for binary data or special characters)

## Error Handling

The API provides detailed error responses with appropriate HTTP status codes:

- `400`: Validation errors (invalid input format, malformed data)
- `422`: Processing errors (invalid sequences, seqkit failures)
- `503`: Service unavailable (seqkit not installed)
- `500`: Internal server errors

Example error response:
```json
{
  "error": "Validation error: Invalid sequence characters found",
  "status_code": 400,
  "timestamp": 1703123456.789
}
```

## Testing

### Run Unit Tests
```bash
python -m pytest tests/test_convert.py -v
python -m pytest tests/test_manipulate.py -v
python -m pytest tests/test_seqkit.py -v
```

### Run Integration Tests
```bash
python -m pytest tests/test_api_integration.py -v
```

### Run All Tests
```bash
python -m pytest tests/ -v
```

## Project Structure

```
fastx-mcp/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API route handlers
│   │   ├── convert.py       # File conversion endpoints
│   │   ├── manipulate.py    # Sequence manipulation endpoints
│   │   ├── seqkit.py        # seqkit integration endpoints
│   │   └── logs.py          # Logging and monitoring endpoints
│   ├── core/                # Core business logic
│   │   ├── converters.py    # File format conversion functions
│   │   ├── manipulators.py  # Sequence manipulation functions
│   │   └── seqkit_wrapper.py # seqkit subprocess interface
│   └── utils/               # Utility modules
│       ├── logging.py       # Audit logging system
│       └── validators.py    # Input validation functions
├── tests/                   # Test suite
│   ├── sample_data/         # Test data files
│   ├── test_convert.py      # Conversion function tests
│   ├── test_manipulate.py   # Manipulation function tests
│   ├── test_seqkit.py       # seqkit wrapper tests
│   └── test_api_integration.py # API integration tests
├── Dockerfile               # Docker container configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Dependencies

- **Python 3.10+**
- **FastAPI**: Web framework for building APIs
- **Biopython**: Bioinformatics library for sequence manipulation
- **seqkit**: High-performance sequence toolkit (Go binary)
- **uvicorn**: ASGI server for running FastAPI

## Limitations

- **Memory Usage**: All operations are performed in-memory. Large files may consume significant RAM.
- **File Size**: Recommended maximum file size is 50MB per request.
- **Concurrency**: The server processes requests sequentially. For high concurrency, consider deploying multiple instances.

## Security Considerations

- **Authentication**: The server can be extended to support API key or other authentication via `mcp_config.yaml`.
- **Input Validation**: All inputs are validated, but additional sanitization may be needed for production.
- **Network Security**: Run behind a proxy/firewall in production environments.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the test cases for usage examples
3. Open an issue on the GitHub repository