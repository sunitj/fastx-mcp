import base64
import re
from typing import Optional, Tuple


class ValidationError(Exception):
    pass


def validate_input_format(input_format: str) -> str:
    valid_formats = ["string", "base64"]
    if input_format not in valid_formats:
        raise ValidationError(f"Invalid input format. Must be one of: {valid_formats}")
    return input_format


def validate_output_format(output_format: str) -> str:
    valid_formats = ["json", "text"]
    if output_format not in valid_formats:
        raise ValidationError(f"Invalid output format. Must be one of: {valid_formats}")
    return output_format


def validate_base64_content(content: str) -> bool:
    try:
        base64.b64decode(content)
        return True
    except Exception:
        return False


def validate_content_size(content: str, max_size_mb: int = 50) -> bool:
    max_size_bytes = max_size_mb * 1024 * 1024
    content_size = len(content.encode('utf-8'))
    
    if content_size > max_size_bytes:
        raise ValidationError(f"Content size ({content_size} bytes) exceeds maximum allowed size ({max_size_bytes} bytes)")
    
    return True


def validate_fasta_format(content: str) -> bool:
    if not content.strip():
        raise ValidationError("Empty content provided")
    
    lines = content.strip().split('\n')
    if not lines[0].startswith('>'):
        raise ValidationError("FASTA content must start with a header line (>)")
    
    has_sequence = False
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            continue
        if re.match(r'^[ATCGRYSWKMBDHVN-]+$', line.upper()):
            has_sequence = True
        else:
            raise ValidationError(f"Invalid sequence characters found: {line}")
    
    if not has_sequence:
        raise ValidationError("No valid sequence data found in FASTA content")
    
    return True


def validate_fastq_format(content: str) -> bool:
    if not content.strip():
        raise ValidationError("Empty content provided")
    
    lines = content.strip().split('\n')
    if len(lines) < 4:
        raise ValidationError("FASTQ content must have at least 4 lines per record")
    
    if len(lines) % 4 != 0:
        raise ValidationError("FASTQ content must have complete 4-line records")
    
    for i in range(0, len(lines), 4):
        if not lines[i].startswith('@'):
            raise ValidationError(f"Line {i+1}: FASTQ header must start with '@'")
        
        if not lines[i+2].startswith('+'):
            raise ValidationError(f"Line {i+3}: FASTQ quality header must start with '+'")
        
        seq_line = lines[i+1].strip()
        qual_line = lines[i+3].strip()
        
        if len(seq_line) != len(qual_line):
            raise ValidationError(f"Record starting at line {i+1}: sequence and quality lengths don't match")
        
        if not re.match(r'^[ATCGRYSWKMBDHVN-]+$', seq_line.upper()):
            raise ValidationError(f"Line {i+2}: Invalid sequence characters found")
    
    return True


def validate_genbank_format(content: str) -> bool:
    if not content.strip():
        raise ValidationError("Empty content provided")
    
    if "LOCUS" not in content and "locus" not in content.lower():
        raise ValidationError("GenBank content must contain LOCUS line")
    
    if "ORIGIN" not in content and "origin" not in content.lower():
        raise ValidationError("GenBank content must contain ORIGIN section")
    
    if "//" not in content:
        raise ValidationError("GenBank content must end with '//'")
    
    return True


def validate_coordinates(start: int, end: int, max_length: Optional[int] = None) -> Tuple[int, int]:
    if start < 0:
        raise ValidationError("Start coordinate must be non-negative")
    
    if end <= start:
        raise ValidationError("End coordinate must be greater than start coordinate")
    
    if max_length is not None and end > max_length:
        raise ValidationError(f"End coordinate ({end}) exceeds sequence length ({max_length})")
    
    return start, end


def validate_sequence_id(sequence_id: str) -> str:
    if not sequence_id or not sequence_id.strip():
        raise ValidationError("Sequence ID cannot be empty")
    
    sequence_id = sequence_id.strip()
    
    if len(sequence_id) > 255:
        raise ValidationError("Sequence ID cannot exceed 255 characters")
    
    if re.search(r'[<>:"/\\|?*]', sequence_id):
        raise ValidationError("Sequence ID contains invalid characters")
    
    return sequence_id


def sanitize_content_for_logging(content: str, max_preview_length: int = 100) -> str:
    if len(content) <= max_preview_length:
        return content
    
    return content[:max_preview_length] + f"... (truncated, total length: {len(content)})"