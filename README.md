
## Installation

1. **Clone the repository**:

    ```sh
    git clone git remote add origin git@github.com:sarkissian001/perf_counter.git
    cd letter_counter
    ```

2. **Install Poetry**:

    Follow the instructions at [Poetry's official documentation](https://python-poetry.org/docs/#installation) to install Poetry.

3. **Install dependencies**:

    ```sh
    poetry install
    ```

## Usage

You can run the main script using Poetry. This script generates a file with random letters and counts the occurrences of each letter using different methods (sequential, threading, and multiprocessing).

1. **Run the script**:

    ```sh
    poetry run counter
    ```

This will execute the `main` function in `letter_counter/counter.py`.

## Testing

Unit tests are included in the `tests` directory. To run the tests, use the following command:

```sh
poetry run pytest