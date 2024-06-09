import os
import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Manager
from typing import Dict, List, Callable, Union, Type



def performance_decorator(func: Callable) -> Callable:
    """Decorator to measure the performance of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Time taken by {func.__name__}: {end_time - start_time:.4f} seconds")
        return result
    return wrapper


class RandomLetterGenerator:
    def __init__(self, choices: str):
        self.choices = choices.split(",")

    def generate(self, count: int) -> str:
        """Generate a string of random letters from the set choices."""
        return ''.join(random.choice(self.choices) for _ in range(count))


class FileProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def write_file(self, content: str) -> None:
        """Write content to the file."""
        with open(self.file_path, 'w') as f:
            f.write(content)

    def read_chunk(self, start: int, size: int) -> str:
        """Read a chunk of the file."""
        with open(self.file_path, 'r') as f:
            f.seek(start)
            return f.read(size)

    def write_counts_to_files(self, letter_counts: Dict[str, int]) -> None:
        """Write the counts to their respective files."""
        for letter, count in letter_counts.items():
            with open(f'{letter}.txt', 'w') as f:
                f.write(str(count))

    def get_file_size(self) -> int:
        """Get the size of the file."""
        return os.path.getsize(self.file_path)


class OccurrenceCalculator:
    def __init__(self, file_processor: FileProcessor, chunk_size: int):
        self.file_processor = file_processor
        self.chunk_size = chunk_size

    def count_letters_in_chunk(self, chunk: str) -> Counter:
        """Count the occurrences of each letter in the chunk. (ex. AAB will become {'A': 2, 'B':1})"""
        return Counter(chunk)

    @performance_decorator
    def count_letter_occurrence_sequential(self) -> Dict[str, int]:
        """Count letter occurrences in the file sequentially."""
        counts = Counter()
        with open(self.file_processor.file_path, 'r') as f:
            data = f.read()
            counts = self.count_letters_in_chunk(data)
        self.file_processor.write_counts_to_files(counts)
        return counts

    @performance_decorator
    def count_letter_occurrence_threading(self) -> Dict[str, int]:
        """Count letter occurrences in the file using threading."""
        return self._count_letter_occurrence_concurrent(ThreadPoolExecutor)

    @performance_decorator
    def count_letter_occurrence_multiprocessing(self) -> Dict[str, int]:
        """Count letter occurrences in the file using multiprocessing."""
        return self._count_letter_occurrence_concurrent(ProcessPoolExecutor)

    def _count_letter_occurrence_concurrent(self, executor_cls: Type[Union[ThreadPoolExecutor, ProcessPoolExecutor]]) -> Dict[str, int]:
        """Count letter occurrences in the file using concurrent execution."""
        with Manager() as manager:
            queue = manager.Queue()
            file_size = self.file_processor.get_file_size()
            num_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
            
            with executor_cls() as executor:
                futures = [
                    executor.submit(self.process_chunk, i * self.chunk_size, self.chunk_size, queue)
                    for i in range(num_chunks)
                ]
                for future in futures:
                    future.result()  # Wait for all threads/processes to complete

            counts_list = []
            while not queue.empty():
                counts_list.append(queue.get())

            # each chunk implements its own Counter object, so if we have 10 chunks we will have 10 
            # Counter objects. However, for final results we need to group all Counter data 
            # into one to output the results
            combined_counts = self.combine_counts(counts_list)

            self.file_processor.write_counts_to_files(combined_counts)
            return combined_counts

    def process_chunk(self, start: int, size: int, queue) -> None:
        """Process a chunk of the file and update shared counts."""
        chunk = self.file_processor.read_chunk(start, size)
        chunk_counts = self.count_letters_in_chunk(chunk)
        queue.put(chunk_counts)

    def combine_counts(self, counts_list: List[Counter]) -> Counter:
        """Combine a list of Counter objects into one Counter."""
        total_counts = Counter()
        for counts in counts_list:
            total_counts.update(counts)
        return total_counts


def main() -> None:
    num_records_to_generate = 10_000_000
    chunk_size = 100_000
    file_path = 'original.txt'

    # Generate and write the original file
    generator = RandomLetterGenerator("A,B,C,D")
    random_letters = generator.generate(num_records_to_generate)
    file_processor = FileProcessor(file_path)
    file_processor.write_file(random_letters)

    # Create an instance of OccurrenceCalculator
    calculator = OccurrenceCalculator(file_processor, chunk_size)

    # Measure performance of counting letter occurrences sequentially
    calculator.count_letter_occurrence_sequential()

    # Measure performance of counting letter occurrences using threading
    calculator.count_letter_occurrence_threading()

    # Measure performance of counting letter occurrences using multiprocessing
    calculator.count_letter_occurrence_multiprocessing()


if __name__ == "__main__":
    main()
