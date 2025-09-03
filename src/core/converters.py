import io
import base64
from typing import Union, Optional
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


class ConversionError(Exception):
    pass


def genbank_to_fasta(
    genbank_content: str, 
    input_format: str = "string"
) -> str:
    try:
        if input_format == "base64":
            try:
                genbank_content = base64.b64decode(genbank_content).decode('utf-8')
            except Exception as e:
                raise ConversionError(f"Failed to decode base64 input: {str(e)}")
        
        genbank_io = io.StringIO(genbank_content)
        fasta_io = io.StringIO()
        
        records = list(SeqIO.parse(genbank_io, "genbank"))
        
        if not records:
            raise ConversionError("No valid GenBank records found in input")
        
        SeqIO.write(records, fasta_io, "fasta")
        
        fasta_content = fasta_io.getvalue()
        fasta_io.close()
        genbank_io.close()
        
        return fasta_content
        
    except Exception as e:
        if isinstance(e, ConversionError):
            raise
        raise ConversionError(f"Failed to convert GenBank to FASTA: {str(e)}")


def get_conversion_summary(
    genbank_content: str, 
    input_format: str = "string"
) -> dict:
    try:
        if input_format == "base64":
            genbank_content = base64.b64decode(genbank_content).decode('utf-8')
        
        genbank_io = io.StringIO(genbank_content)
        records = list(SeqIO.parse(genbank_io, "genbank"))
        genbank_io.close()
        
        if not records:
            return {"record_count": 0, "total_length": 0, "record_ids": []}
        
        record_ids = [record.id for record in records]
        total_length = sum(len(record.seq) for record in records)
        
        return {
            "record_count": len(records),
            "total_length": total_length,
            "record_ids": record_ids
        }
        
    except Exception as e:
        raise ConversionError(f"Failed to analyze GenBank content: {str(e)}")