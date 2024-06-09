import unittest
import os
from collections import Counter
from tempfile import NamedTemporaryFile
from unittest.mock import patch


from letter_counter.counter import (
    RandomLetterGenerator,
    FileProcessor,
    OccurrenceCalculator,
)


class TestRandomLetterGenerator(unittest.TestCase):
    def test_generate(self):
        generator = RandomLetterGenerator("A,B,C,D")
        result = generator.generate(10)
        self.assertEqual(len(result), 10)
        self.assertTrue(all(c in "ABCD" for c in result))


class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_file = NamedTemporaryFile(delete=False)
        self.file_path = self.temp_file.name
        self.processor = FileProcessor(self.file_path)

    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_write_file(self):
        content = "ABCD" * 25
        self.processor.write_file(content)
        with open(self.file_path, "r") as file:
            self.assertEqual(file.read(), content)

    def test_read_chunk(self):
        content = "ABCD" * 25
        self.processor.write_file(content)
        chunk_size = 10
        chunk = self.processor.read_chunk(0, chunk_size)
        self.assertEqual(chunk, "ABCDABCDAB")
        self.assertEqual(len(chunk), chunk_size)

    def test_get_file_size(self):
        content = "ABCD"
        self.processor.write_file(content)
        size = self.processor.get_file_size()
        self.assertEqual(size, 4)


class TestOccurrenceCalculator(unittest.TestCase):
    def setUp(self):
        self.temp_file = NamedTemporaryFile(delete=False)
        self.file_path = self.temp_file.name
        self.file_processor = FileProcessor(self.file_path)
        content = "AABBBCCCCDDDD" * 100
        self.file_processor.write_file(content)
        
        self.calculator = OccurrenceCalculator(self.file_processor, chunk_size=10)


    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_count_letter_occurrence_sequential(self):
        expected_counts = Counter("AABBBCCCCDDDD" * 100)
        result = self.calculator.count_letter_occurrence_sequential()
        self.assertEqual(result, expected_counts)

    def test_count_letter_occurrence_threading(self):
        expected_counts = Counter("AABBBCCCCDDDD" * 100)
        result = self.calculator.count_letter_occurrence_threading()
        self.assertEqual(result, expected_counts)

    def test_count_letter_occurrence_multiprocessing(self):
        expected_counts = Counter("AABBBCCCCDDDD" * 100)
        result = self.calculator.count_letter_occurrence_multiprocessing()
        self.assertEqual(result, expected_counts)


if __name__ == "__main__":
    unittest.main()
