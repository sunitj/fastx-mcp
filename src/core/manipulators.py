import io
import base64
from typing import Union, Optional
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq


class ManipulationError(Exception):
    pass


def reverse_complement_fasta(
    fasta_content: str, 
    input_format: str = "string"
) -> str:
    try:
        if input_format == "base64":
            try:
                fasta_content = base64.b64decode(fasta_content).decode('utf-8')
            except Exception as e:
                raise ManipulationError(f"Failed to decode base64 input: {str(e)}")
        
        fasta_input = io.StringIO(fasta_content)
        fasta_output = io.StringIO()
        
        records = list(SeqIO.parse(fasta_input, "fasta"))
        
        if not records:
            raise ManipulationError("No valid FASTA records found in input")
        
        rc_records = []
        for record in records:
            try:
                rc_seq = record.seq.reverse_complement()
                rc_record = SeqRecord(
                    rc_seq,
                    id=record.id + "_rc",
                    description=record.description + " (reverse complement)"
                )
                rc_records.append(rc_record)
            except Exception as e:
                raise ManipulationError(f"Failed to reverse complement sequence {record.id}: {str(e)}")
        
        SeqIO.write(rc_records, fasta_output, "fasta")
        
        result = fasta_output.getvalue()
        fasta_output.close()
        fasta_input.close()
        
        return result
        
    except Exception as e:
        if isinstance(e, ManipulationError):
            raise
        raise ManipulationError(f"Failed to reverse complement FASTA: {str(e)}")


def extract_subsequence(
    fasta_content: str,
    sequence_id: str,
    start: int,
    end: int,
    input_format: str = "string"
) -> str:
    try:
        if input_format == "base64":
            fasta_content = base64.b64decode(fasta_content).decode('utf-8')
        
        fasta_input = io.StringIO(fasta_content)
        records = list(SeqIO.parse(fasta_input, "fasta"))
        fasta_input.close()
        
        if not records:
            raise ManipulationError("No valid FASTA records found in input")
        
        target_record = None
        for record in records:
            if record.id == sequence_id:
                target_record = record
                break
        
        if target_record is None:
            raise ManipulationError(f"Sequence with ID '{sequence_id}' not found")
        
        if start < 0 or end > len(target_record.seq) or start >= end:
            raise ManipulationError(
                f"Invalid coordinates: start={start}, end={end}, sequence_length={len(target_record.seq)}"
            )
        
        subseq = target_record.seq[start:end]
        subseq_record = SeqRecord(
            subseq,
            id=f"{sequence_id}_subseq_{start}_{end}",
            description=f"{target_record.description} (subsequence {start}-{end})"
        )
        
        fasta_output = io.StringIO()
        SeqIO.write([subseq_record], fasta_output, "fasta")
        result = fasta_output.getvalue()
        fasta_output.close()
        
        return result
        
    except Exception as e:
        if isinstance(e, ManipulationError):
            raise
        raise ManipulationError(f"Failed to extract subsequence: {str(e)}")


def get_fasta_summary(
    fasta_content: str, 
    input_format: str = "string"
) -> dict:
    try:
        if input_format == "base64":
            fasta_content = base64.b64decode(fasta_content).decode('utf-8')
        
        fasta_input = io.StringIO(fasta_content)
        records = list(SeqIO.parse(fasta_input, "fasta"))
        fasta_input.close()
        
        if not records:
            return {"record_count": 0, "total_length": 0, "sequences": []}
        
        sequences = []
        total_length = 0
        
        for record in records:
            seq_length = len(record.seq)
            total_length += seq_length
            sequences.append({
                "id": record.id,
                "description": record.description,
                "length": seq_length
            })
        
        return {
            "record_count": len(records),
            "total_length": total_length,
            "sequences": sequences
        }
        
    except Exception as e:
        raise ManipulationError(f"Failed to analyze FASTA content: {str(e)}")