use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, Read, Seek, SeekFrom};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Instant;


atruct FileProcessor {
     file_path: String,
}


impl FileProcessor {
    fn new(file_path: &str) -> Self {
        FileProcessor {
            file_path: file_path.to_string(),
        }
    }

    fn read_chunk(&self, start: u64, size: usize) -> std::io::Result<Vec<u8>> {
        let file = File::open(&self.file_path)?;
        let mut reader = BufReader::new(file);
        reader.seek(SeekFrom::Start(start))?;
        let mut buffer = vec![0; size];
        reader.read_exact(&mut buffer)?;
        Ok(buffer)
    }

    fn write_counts_to_files(&self, letter_counts: &HashMap<u8, usize>) -> std::io::Result<()> {
        for (letter, count) in letter_counts {
            let file_name = format!("{}.txt", *letter as char);
            std::fs::write(&file_name, count.to_string())?;
        }
        Ok(())
    }

    fn get_file_size(&self) -> std::io::Result<u64> {
        let metadata = std::fs::metadata(&self.file_path)?;
        Ok(metadata.len())
    }
}

struct OccurrenceCalculator {
    file_processor: FileProcessor,
    chunk_size: usize,
}

impl OccurrenceCalculator {
    fn new(file_processor: FileProcessor, chunk_size: usize) -> Self {
        OccurrenceCalculator {
            file_processor,
            chunk_size,
        }
    }

    fn count_letters_in_chunk(chunk: &[u8]) -> HashMap<u8, usize> {
        let mut counts = HashMap::new();
        for &byte in chunk {
            *counts.entry(byte).or_insert(0) += 1;
        }
        counts
    }

    fn count_letter_occurrence_sequential(&self) -> std::io::Result<HashMap<u8, usize>> {
        let file_size = self.file_processor.get_file_size()?;
        let mut counts = HashMap::new();

        let start = Instant::now();
        let mut current_position = 0;
        while current_position < file_size {
            let chunk = self.file_processor.read_chunk(current_position, self.chunk_size)?;
            let chunk_counts = Self::count_letters_in_chunk(&chunk);
            for (letter, count) in chunk_counts {
                *counts.entry(letter).or_insert(0) += count;
            }
            current_position += self.chunk_size as u64;
        }
        let duration = start.elapsed();
        println!(
            "Time taken by count_letter_occurrence_sequential: {:?} seconds",
            duration.as_secs_f64()
        );

        self.file_processor.write_counts_to_files(&counts)?;
        Ok(counts)
    }

    fn count_letter_occurrence_parallel(&self) -> std::io::Result<HashMap<u8, usize>> {
        let file_size = self.file_processor.get_file_size()?;
        let num_chunks = (file_size + self.chunk_size as u64 - 1) / self.chunk_size as u64;
        let counts = Arc::new(Mutex::new(HashMap::new()));
        let mut handles = vec![];

        let start = Instant::now();

        for i in 0..num_chunks {
            let counts = Arc::clone(&counts);
            let file_path = self.file_processor.file_path.clone();
            let chunk_size = self.chunk_size;
            let handle = thread::spawn(move || {
                let file_processor = FileProcessor::new(&file_path);
                let start_position = i * chunk_size as u64;
                let chunk = file_processor.read_chunk(start_position, chunk_size).unwrap();
                let chunk_counts = OccurrenceCalculator::count_letters_in_chunk(&chunk);

                let mut counts = counts.lock().unwrap();
                for (letter, count) in chunk_counts {
                    *counts.entry(letter).or_insert(0) += count;
                }
            });
            handles.push(handle);
        }

        for handle in handles {
            handle.join().unwrap();
        }

        let duration = start.elapsed();
        println!(
            "Time taken by count_letter_occurrence_parallel: {:?} seconds",
            duration.as_secs_f64()
        );

        let counts = Arc::try_unwrap(counts).unwrap().into_inner().unwrap();
        self.file_processor.write_counts_to_files(&counts)?;
        Ok(counts)
    }
}

fn main() -> std::io::Result<()> {
    let file_path = "../original.txt";
    let chunk_size = 100_000;
    let file_processor = FileProcessor::new(file_path);
    let calculator = OccurrenceCalculator::new(file_processor, chunk_size);

    // Sequential counting
    calculator.count_letter_occurrence_sequential()?;

    // Parallel counting
    calculator.count_letter_occurrence_parallel()?;

    Ok(())
}
