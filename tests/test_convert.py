import unittest
import os
import base64
from src.core.converters import genbank_to_fasta, get_conversion_summary, ConversionError


class TestConverters(unittest.TestCase):
    
    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
        
        with open(os.path.join(self.test_data_dir, 'sample.genbank'), 'r') as f:
            self.sample_genbank = f.read()
    
    def test_genbank_to_fasta_string_format(self):
        result = genbank_to_fasta(self.sample_genbank, input_format="string")
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('>'))
        self.assertIn('TEST_SEQUENCE', result)
        self.assertIn('atgaaatacagctatattgc', result)
    
    def test_genbank_to_fasta_base64_format(self):
        genbank_b64 = base64.b64encode(self.sample_genbank.encode('utf-8')).decode('utf-8')
        
        result = genbank_to_fasta(genbank_b64, input_format="base64")
        
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('>'))
        self.assertIn('TEST_SEQUENCE', result)
    
    def test_genbank_to_fasta_invalid_input(self):
        with self.assertRaises(ConversionError):
            genbank_to_fasta("invalid genbank content", input_format="string")
    
    def test_genbank_to_fasta_empty_input(self):
        with self.assertRaises(ConversionError):
            genbank_to_fasta("", input_format="string")
    
    def test_genbank_to_fasta_invalid_base64(self):
        with self.assertRaises(ConversionError):
            genbank_to_fasta("invalid base64!", input_format="base64")
    
    def test_get_conversion_summary(self):
        summary = get_conversion_summary(self.sample_genbank, input_format="string")
        
        self.assertIsInstance(summary, dict)
        self.assertIn('record_count', summary)
        self.assertIn('total_length', summary)
        self.assertIn('record_ids', summary)
        
        self.assertEqual(summary['record_count'], 1)
        self.assertEqual(summary['total_length'], 100)
        self.assertIn('TEST_SEQUENCE', summary['record_ids'])
    
    def test_get_conversion_summary_empty_input(self):
        summary = get_conversion_summary("", input_format="string")
        
        self.assertEqual(summary['record_count'], 0)
        self.assertEqual(summary['total_length'], 0)
        self.assertEqual(summary['record_ids'], [])
    
    def test_get_conversion_summary_base64(self):
        genbank_b64 = base64.b64encode(self.sample_genbank.encode('utf-8')).decode('utf-8')
        
        summary = get_conversion_summary(genbank_b64, input_format="base64")
        
        self.assertEqual(summary['record_count'], 1)
        self.assertEqual(summary['total_length'], 100)


if __name__ == '__main__':
    unittest.main()