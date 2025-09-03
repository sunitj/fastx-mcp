import unittest
import os
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app


class TestAPIIntegration(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
        
        with open(os.path.join(self.test_data_dir, 'sample.genbank'), 'r') as f:
            self.sample_genbank = f.read()
        
        with open(os.path.join(self.test_data_dir, 'sample.fasta'), 'r') as f:
            self.sample_fasta = f.read()
        
        with open(os.path.join(self.test_data_dir, 'sample.fastq'), 'r') as f:
            self.sample_fastq = f.read()
    
    def test_root_endpoint(self):
        response = self.client.get("/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("endpoints", data)
        self.assertEqual(data["message"], "FastX-MCP Server")
    
    def test_health_endpoint(self):
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("services", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("biopython", data["services"])
        self.assertTrue(data["services"]["biopython"])
    
    def test_convert_genbank_to_fasta_string_format(self):
        response = self.client.post(
            "/convert/genbank-to-fasta",
            json={
                "content": self.sample_genbank,
                "input_format": "string",
                "include_summary": True
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("fasta_content", data)
        self.assertIn("success", data)
        self.assertIn("conversion_summary", data)
        self.assertIn("execution_time_ms", data)
        
        self.assertTrue(data["success"])
        self.assertTrue(data["fasta_content"].startswith('>'))
        self.assertIsNotNone(data["conversion_summary"])
        self.assertEqual(data["conversion_summary"]["record_count"], 1)
    
    def test_convert_genbank_to_fasta_base64_format(self):
        genbank_b64 = base64.b64encode(self.sample_genbank.encode('utf-8')).decode('utf-8')
        
        response = self.client.post(
            "/convert/genbank-to-fasta",
            json={
                "content": genbank_b64,
                "input_format": "base64",
                "include_summary": False
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertTrue(data["fasta_content"].startswith('>'))
        self.assertIsNone(data["conversion_summary"])
    
    def test_convert_genbank_to_fasta_invalid_input(self):
        response = self.client.post(
            "/convert/genbank-to-fasta",
            json={
                "content": "invalid genbank content",
                "input_format": "string"
            }
        )
        
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
    
    def test_convert_formats_endpoint(self):
        response = self.client.get("/convert/formats")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("supported_conversions", data)
        self.assertIn("input_formats", data)
        self.assertIn("features", data)
    
    def test_manipulate_reverse_complement(self):
        response = self.client.post(
            "/manipulate/reverse-complement",
            json={
                "content": self.sample_fasta,
                "input_format": "string",
                "include_summary": True
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("fasta_content", data)
        self.assertIn("success", data)
        self.assertIn("manipulation_summary", data)
        self.assertIn("execution_time_ms", data)
        
        self.assertTrue(data["success"])
        self.assertTrue(data["fasta_content"].startswith('>'))
        self.assertIn("_rc", data["fasta_content"])
        self.assertIsNotNone(data["manipulation_summary"])
    
    def test_manipulate_extract_subsequence(self):
        response = self.client.post(
            "/manipulate/extract-subsequence",
            json={
                "content": self.sample_fasta,
                "sequence_id": "test_sequence_1",
                "start": 10,
                "end": 20,
                "input_format": "string"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("fasta_content", data)
        self.assertIn("success", data)
        self.assertIn("subsequence_info", data)
        self.assertIn("execution_time_ms", data)
        
        self.assertTrue(data["success"])
        self.assertTrue(data["fasta_content"].startswith('>'))
        self.assertIn("_subseq_10_20", data["fasta_content"])
        self.assertEqual(data["subsequence_info"]["length"], 10)
    
    def test_manipulate_extract_subsequence_invalid_id(self):
        response = self.client.post(
            "/manipulate/extract-subsequence",
            json={
                "content": self.sample_fasta,
                "sequence_id": "nonexistent_sequence",
                "start": 0,
                "end": 10,
                "input_format": "string"
            }
        )
        
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
    
    def test_manipulate_operations_endpoint(self):
        response = self.client.get("/manipulate/operations")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("supported_operations", data)
        self.assertIn("input_formats", data)
        self.assertIn("features", data)
    
    @patch('src.core.seqkit_wrapper.validate_seqkit_installation')
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_seqkit_stats_success(self, mock_run, mock_validate):
        mock_validate.return_value = True
        mock_stats = '[{"file": "test.fastq", "format": "FASTQ", "type": "DNA", "num_seqs": 3}]'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stats)
        
        response = self.client.post(
            "/seqkit/stats",
            json={
                "content": self.sample_fastq,
                "input_format": "string",
                "output_format": "json"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("statistics", data)
        self.assertIn("success", data)
        self.assertIn("execution_time_ms", data)
        
        self.assertTrue(data["success"])
        self.assertIsInstance(data["statistics"], list)
    
    @patch('src.core.seqkit_wrapper.validate_seqkit_installation')
    def test_seqkit_stats_unavailable(self, mock_validate):
        mock_validate.return_value = False
        
        response = self.client.post(
            "/seqkit/stats",
            json={
                "content": self.sample_fastq,
                "input_format": "string"
            }
        )
        
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn("error", data)
    
    def test_seqkit_info_endpoint(self):
        response = self.client.get("/seqkit/info")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("seqkit_available", data)
        self.assertIn("supported_commands", data)
        self.assertIn("endpoints", data)
        
        self.assertIsInstance(data["supported_commands"], list)
        self.assertIn("stats", data["supported_commands"])
    
    def test_logs_endpoint(self):
        response = self.client.get("/logs/")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("logs", data)
        self.assertIn("total_count", data)
        self.assertIn("filtered_count", data)
        self.assertIn("query_time_ms", data)
        
        self.assertIsInstance(data["logs"], list)
        self.assertIsInstance(data["total_count"], int)
    
    def test_logs_with_filters(self):
        response = self.client.get("/logs/?limit=10&success_only=true")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("logs", data)
        self.assertLessEqual(len(data["logs"]), 10)
    
    def test_logs_stats_endpoint(self):
        response = self.client.get("/logs/stats")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("stats", data)
        self.assertIn("query_time_ms", data)
        
        stats = data["stats"]
        self.assertIn("total_operations", stats)
        self.assertIn("successful_operations", stats)
        self.assertIn("failed_operations", stats)
    
    def test_logs_operations_endpoint(self):
        response = self.client.get("/logs/operations")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("available_operations", data)
        self.assertIn("total_unique_operations", data)
        self.assertIsInstance(data["available_operations"], list)
    
    def test_logs_info_endpoint(self):
        response = self.client.get("/logs/info")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("logging_system", data)
        self.assertIn("max_logs", data)
        self.assertIn("features", data)
        self.assertIn("endpoints", data)
    
    def test_logs_clear_endpoint(self):
        response = self.client.delete("/logs/clear")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("success", data)
        self.assertIn("message", data)
        self.assertIn("execution_time_ms", data)
        
        self.assertTrue(data["success"])
    
    def test_error_handling_invalid_json(self):
        response = self.client.post(
            "/convert/genbank-to-fasta",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()