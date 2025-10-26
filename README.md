# Market Sim

This is a just for fun project to try and make a simple stock market sim website. This however is an actual market sim where buys and sells impact the price of the fake stock. It will have some bots to also trade and try to make money (dumb bots for now)

I'm going to start with a python backend and use basic terminal output to start. Then I will try to make a simple web frontend.

Started on 10/13/2025

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd market-sim
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
   ```

3. Install the project in editable mode:

   ```bash
   pip install -e .
   ```

4. Install the requirements:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Once the project is installed, you can run the market simulation by typing the following command in your terminal:

```bash
market-sim
```

This will execute the simulation defined in `src/main.py`.

## Project Structure

The project is structured as follows:

- `src/`: This directory contains the main source code of the application.
- `core/`: Contains the core data structures of the simulation, such as `Order`, `Trade`, and `User`.
- `engine/`: Contains the market simulation logic, including the `MatchingEngine` and `OrderBook`.
- `main.py`: The main entry point of the application, which can be run as a script.
- `tests/`: Contains the tests for the project.
- `pyproject.toml`: The project definition file, used by modern Python packaging tools.
- `.gitignore`: A file that tells git which files and directories to ignore.
- `README.md`: This file.
