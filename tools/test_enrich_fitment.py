"""Regression checks for ambiguous identifiers and applicability labels."""
import unittest
from enrich_fitment import filename_parts, header_years, models_in_header, years_label

class FitmentLabels(unittest.TestCase):
    def test_part_numbers_survive_filename_delimiters(self):
        self.assertEqual(filename_parts('AAD1A07100-A61022_31711AJ782.bin'), ['31711AJ782'])
        self.assertEqual(filename_parts('31711AG589x'), [])

    def test_year_label_does_not_invent_missing_years(self):
        self.assertEqual(years_label([2003, 2005, 2006]), '2003+2005-2006')
        self.assertEqual(years_label([]), 'Unknown-Year')

    def test_header_years_exclude_trim_and_version_numbers(self):
        self.assertEqual(header_years('FORESTER 19,20MY ES'), [2019, 2020])
        self.assertEqual(header_years('TRIBECA 08/09MY 3.6L'), [2008, 2009])
        self.assertEqual(header_years('3.6L 5AT 30919AB193'), [])

    def test_explicit_models_include_previously_unknown_headers(self):
        self.assertEqual(models_in_header('N.AMERICA TRIBECCA 13MY'), ['Tribeca'])
        self.assertEqual(models_in_header('WRX 15MY EA E3'), ['WRX'])
        self.assertEqual(models_in_header('Unknown 5AT'), [])

if __name__ == '__main__':
    unittest.main()
