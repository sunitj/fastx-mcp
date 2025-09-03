import unittest
import os
import base64
from unittest.mock import patch, MagicMock
from src.core.seqkit_wrapper import (
    run_seqkit_stats,
    run_seqkit_command,
    validate_seqkit_installation,
    get_seqkit_version,
    SeqkitError
)


class TestSeqkitWrapper(unittest.TestCase):
    
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
        
        with open(os.path.join(self.test_data_dir, 'sample.fastq'), 'r') as f:
            self.sample_fastq = f.read()
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_validate_seqkit_installation_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="seqkit v2.0.0")
        
        result = validate_seqkit_installation()
        
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_validate_seqkit_installation_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        
        result = validate_seqkit_installation()
        
        self.assertFalse(result)
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_get_seqkit_version_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="seqkit v2.0.0\n")
        
        result = get_seqkit_version()
        
        self.assertEqual(result, "seqkit v2.0.0")
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_get_seqkit_version_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        
        result = get_seqkit_version()
        
        self.assertIsNone(result)
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_stats_json_format(self, mock_run):
        mock_stats = '[{"file": "test.fastq", "format": "FASTQ", "type": "DNA", "num_seqs": 3, "sum_len": 100, "min_len": 30, "avg_len": 33.3, "max_len": 40}]'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stats)
        
        result = run_seqkit_stats(self.sample_fastq, input_format="string", output_format="json")
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn('num_seqs', result[0])
        self.assertEqual(result[0]['num_seqs'], 3)
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_stats_text_format(self, mock_run):
        mock_stats = "file\tformat\ttype\tnum_seqs\tsum_len\tmin_len\tavg_len\tmax_len\ntest.fastq\tFASTQ\tDNA\t3\t100\t30\t33.3\t40"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stats)
        
        result = run_seqkit_stats(self.sample_fastq, input_format="string", output_format="text")
        
        self.assertIsInstance(result, dict)
        self.assertIn('output', result)
        self.assertIn('FASTQ', result['output'])
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_stats_base64_input(self, mock_run):
        fastq_b64 = base64.b64encode(self.sample_fastq.encode('utf-8')).decode('utf-8')
        mock_stats = '[{"file": "test.fastq", "num_seqs": 3}]'
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stats)
        
        result = run_seqkit_stats(fastq_b64, input_format="base64", output_format="json")
        
        self.assertIsInstance(result, list)
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_stats_command_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Error: invalid file format")
        
        with self.assertRaises(SeqkitError):
            run_seqkit_stats(self.sample_fastq, input_format="string")
    
    def test_run_seqkit_stats_invalid_base64(self):
        with self.assertRaises(SeqkitError):
            run_seqkit_stats("invalid base64!", input_format="base64")
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_stats_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json")
        
        with self.assertRaises(SeqkitError):
            run_seqkit_stats(self.sample_fastq, input_format="string", output_format="json")
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_command_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="command output")
        
        result = run_seqkit_command(
            self.sample_fastq,
            "head",
            args=["-n", "2"],
            input_format="string"
        )
        
        self.assertEqual(result, "command output")
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        self.assertIn("seqkit", call_args)
        self.assertIn("head", call_args)
        self.assertIn("-n", call_args)
        self.assertIn("2", call_args)
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_command_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Command failed")
        
        with self.assertRaises(SeqkitError):
            run_seqkit_command(self.sample_fastq, "invalid_command")
    
    @patch('src.core.seqkit_wrapper.subprocess.run')
    def test_run_seqkit_command_timeout(self, mock_run):
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("seqkit", 60)
        
        with self.assertRaises(SeqkitError):
            run_seqkit_command(self.sample_fastq, "stats")


if __name__ == '__main__':
    unittest.main()