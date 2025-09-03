import unittest
import os
import base64
from src.core.manipulators import (
    reverse_complement_fasta, 
    extract_subsequence, 
    get_fasta_summary,
    ManipulationError
)


class TestManipulators(unittest.TestCase):
    
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
        
        with open(os.path.join(self.test_data_dir, 'sample.fasta'), 'r') as f:
            self.sample_fasta = f.read()
    
    def test_reverse_complement_fasta_string_format(self):
        result = reverse_complement_fasta(self.sample_fasta, input_format="string")
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('>'))
        self.assertIn('_rc', result)
        self.assertIn('reverse complement', result)
        
        lines = result.strip().split('\n')
        self.assertTrue(any('_rc' in line for line in lines))
    
    def test_reverse_complement_fasta_base64_format(self):
        fasta_b64 = base64.b64encode(self.sample_fasta.encode('utf-8')).decode('utf-8')
        
        result = reverse_complement_fasta(fasta_b64, input_format="base64")
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('>'))
        self.assertIn('_rc', result)
    
    def test_reverse_complement_fasta_invalid_input(self):
        with self.assertRaises(ManipulationError):
            reverse_complement_fasta("invalid fasta content", input_format="string")
    
    def test_reverse_complement_fasta_empty_input(self):
        with self.assertRaises(ManipulationError):
            reverse_complement_fasta("", input_format="string")
    
    def test_reverse_complement_fasta_invalid_base64(self):
        with self.assertRaises(ManipulationError):
            reverse_complement_fasta("invalid base64!", input_format="base64")
    
    def test_extract_subsequence_valid(self):
        result = extract_subsequence(
            self.sample_fasta,
            "test_sequence_1",
            10,
            20,
            input_format="string"
        )
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('>'))
        self.assertIn('_subseq_10_20', result)
        self.assertIn('subsequence 10-20', result)
        
        lines = result.strip().split('\n')
        sequence_line = lines[1] if len(lines) > 1 else ""
        self.assertEqual(len(sequence_line), 10)
    
    def test_extract_subsequence_invalid_sequence_id(self):
        with self.assertRaises(ManipulationError):
            extract_subsequence(
                self.sample_fasta,
                "nonexistent_sequence",
                0,
                10,
                input_format="string"
            )
    
    def test_extract_subsequence_invalid_coordinates(self):
        with self.assertRaises(ManipulationError):
            extract_subsequence(
                self.sample_fasta,
                "test_sequence_1",
                50,
                1000,
                input_format="string"
            )
    
    def test_extract_subsequence_negative_start(self):
        with self.assertRaises(ManipulationError):
            extract_subsequence(
                self.sample_fasta,
                "test_sequence_1",
                -5,
                10,
                input_format="string"
            )
    
    def test_extract_subsequence_start_greater_than_end(self):
        with self.assertRaises(ManipulationError):
            extract_subsequence(
                self.sample_fasta,
                "test_sequence_1",
                20,
                10,
                input_format="string"
            )
    
    def test_get_fasta_summary(self):
        summary = get_fasta_summary(self.sample_fasta, input_format="string")
        
        self.assertIsInstance(summary, dict)
        self.assertIn('record_count', summary)
        self.assertIn('total_length', summary)
        self.assertIn('sequences', summary)
        
        self.assertEqual(summary['record_count'], 3)
        self.assertGreater(summary['total_length'], 0)
        self.assertEqual(len(summary['sequences']), 3)
        
        seq_ids = [seq['id'] for seq in summary['sequences']]
        self.assertIn('test_sequence_1', seq_ids)
        self.assertIn('test_sequence_2', seq_ids)
        self.assertIn('test_sequence_3', seq_ids)
    
    def test_get_fasta_summary_empty_input(self):
        summary = get_fasta_summary("", input_format="string")
        
        self.assertEqual(summary['record_count'], 0)
        self.assertEqual(summary['total_length'], 0)
        self.assertEqual(summary['sequences'], [])
    
    def test_get_fasta_summary_base64(self):
        fasta_b64 = base64.b64encode(self.sample_fasta.encode('utf-8')).decode('utf-8')
        
        summary = get_fasta_summary(fasta_b64, input_format="base64")
        
        self.assertEqual(summary['record_count'], 3)
        self.assertGreater(summary['total_length'], 0)


if __name__ == '__main__':
    unittest.main()