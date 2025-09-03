import subprocess
import tempfile
import os
import base64
from typing import Dict, Any, Optional


def parse_seqkit_tabular_output(tabular_text: str) -> Any:
    """
    Parse seqkit tabular output into a list of dicts (one per record/file).
    Assumes tab-separated columns, first line is header.
    Returns a list of dicts if multiple records, or a single dict if one record.
    """
    lines = [line.strip() for line in tabular_text.strip().splitlines() if line.strip()]
    if not lines or len(lines) < 2:
        return {}
    header = lines[0].split("\t")
    records = []
    for line in lines[1:]:
        values = line.split("\t")
        record = dict(zip(header, values))
        records.append(record)
    return records[0] if len(records) == 1 else records


class SeqkitError(Exception):
    pass


def run_seqkit_stats(
    fastq_content: str, input_format: str = "string", output_format: str = "json"
) -> Dict[str, Any]:
    try:
        if input_format == "base64":
            try:
                fastq_content = base64.b64decode(fastq_content).decode("utf-8")
            except Exception as e:
                raise SeqkitError(f"Failed to decode base64 input: {str(e)}")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fastq", delete=False
        ) as temp_file:
            temp_file.write(fastq_content)
            temp_file_path = temp_file.name

        try:
            # Always get tabular output, then parse to JSON if requested
            cmd = ["seqkit", "stats", "-T", temp_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise SeqkitError(f"seqkit command failed: {result.stderr}")

            if output_format == "json":
                try:
                    stats_data = parse_seqkit_tabular_output(result.stdout)
                    return stats_data
                except Exception as e:
                    raise SeqkitError(f"Failed to parse tabular output: {str(e)}")
            else:
                return {"output": result.stdout.strip()}

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except subprocess.TimeoutExpired:
        raise SeqkitError("seqkit command timed out")
    except Exception as e:
        if isinstance(e, SeqkitError):
            raise
        raise SeqkitError(f"Failed to run seqkit stats: {str(e)}")


def run_seqkit_command(
    fastq_content: str, command: str, args: list = None, input_format: str = "string"
) -> str:
    try:
        if input_format == "base64":
            fastq_content = base64.b64decode(fastq_content).decode("utf-8")

        if args is None:
            args = []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fastq", delete=False
        ) as temp_input:
            temp_input.write(fastq_content)
            temp_input_path = temp_input.name

        try:
            cmd = ["seqkit", command] + args + [temp_input_path]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise SeqkitError(f"seqkit {command} failed: {result.stderr}")

            # Optionally parse tabular output if caller requests
            return result.stdout

        finally:
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)

    except subprocess.TimeoutExpired:
        raise SeqkitError(f"seqkit {command} command timed out")
    except Exception as e:
        if isinstance(e, SeqkitError):
            raise
        raise SeqkitError(f"Failed to run seqkit {command}: {str(e)}")


def validate_seqkit_installation() -> bool:
    try:
        result = subprocess.run(
            ["seqkit", "version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def get_seqkit_version() -> Optional[str]:
    try:
        result = subprocess.run(
            ["seqkit", "version"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return None

    except Exception:
        return None
