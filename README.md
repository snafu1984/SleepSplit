# SleepSplit

SleepSplit is a Python command-line application that splits long MP3 audiobooks into smaller listening segments suitable for bedtime listening.

It detects silences and plans cuts at suitable pause points. MP3 files are split using `mp3splt` to preserve the original audio quality.

## Features

- Automatic silence detection and cut-point planning
- MP3 splitting at suitable pause points
- Batch processing of MP3 files in a single directory
- Sequentially numbered output files
- Preservation of audio metadata through MP3 splitting
- Optional disc-number assignment based on segment durations
- ID3 `TPOS` tags with two-digit disc numbers (`01`, `02`, `03`, ...)
- Dry-run mode to inspect planned cuts without modifying files
- Command-line interface

SleepSplit processes MP3 files directly inside the specified directory. Subdirectories are not searched.

### Segment Lengths

SleepSplit aims to create audiobook segments of approximately 5 minutes, making them suitable for bedtime listening.

- **Target duration:** 5 minutes (300 seconds).
- **Regular segments:** 4–7 minutes (240–420 seconds).
- **Final segment:** 2–9 minutes (120–540 seconds).
- **Cut positions:** SleepSplit analyzes silent passages and selects suitable cut points, preferring segments close to the 5-minute target.
- **Short audio files:** Files with a duration of 7 minutes or less are not split. They are copied unchanged to the output directory.

SleepSplit first attempts to find a complete cutting plan that satisfies the duration limits for all segments, including the final segment. If no valid plan can be found, no cut points are returned. In this case, the original file is copied to the output directory without splitting.

Actual segment lengths depend on the available pauses in the source audio.

## Disc Assignment

The optional `--disk` argument assigns disc numbers to the generated MP3 files based on their durations.

- **Target duration:** approximately 60 minutes per disc.
- **Regular discs:** 55–65 minutes total duration.
- **Final disc:** may be shorter than 55 minutes.
- **Maximum segment duration:** a segment longer than 65 minutes cannot be assigned to a disc.

Disc numbers are written to the ID3 `TPOS` tag as two-digit values, such as `01`, `02`, and `03`.

Disc assignment does not change the audio segments themselves. It adds disc-number metadata to the output files.

Example:

```bash
sleepsplit /path/to/audiobooks --disk
```

Without `--disk`, SleepSplit does not perform the optional disc-number assignment.

## Requirements

- Python 3.13 or later
- `ffmpeg` available on your `PATH`
- `mp3splt` available on your `PATH`

## Installation

### Install from source

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd SleepSplit
```

Create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Install SleepSplit:

```bash
python -m pip install .
```

### Development installation

For development, install the project in editable mode with its development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Usage

Process all MP3 files in a directory:

```bash
sleepsplit /path/to/audiobooks
```

SleepSplit analyzes the MP3 files and creates output directories for the generated segments.

### Dry run

Preview the planned cuts without creating or modifying output files:

```bash
sleepsplit --dry-run /path/to/audiobooks
```

### Assign disc numbers

Assign disc numbers to newly generated output files based on their durations:

```bash
sleepsplit --disk /path/to/audiobooks
```

The disc numbers are stored in the ID3 `TPOS` tag. Regular discs target approximately 60 minutes, with a duration range of 55–65 minutes. The final disc may be shorter.

## Output

Output files are placed in a directory named after the album metadata, followed by `_cut`. If no album name is available, the output directory is named `cut`.

Split files use sequential numbering, for example:

```text
Example Album_cut/
├── Chapter_001.mp3
├── Chapter_002.mp3
└── Chapter_003.mp3
```

Files that cannot be split because no suitable cut points are found are copied to the output directory without splitting.

Existing output files are not overwritten. If a planned output filename already exists, processing that file fails rather than replacing the existing file.

## Development

Run the test suite:

```bash
pytest -v
```

Check code quality:

```bash
ruff check .
ruff format --check .
```

Build the package:

```bash
python -m pip install build
python -m build
```

## Development Principles

- Every commit should leave the project runnable.
- Keep each commit focused on one logical change.
- Run tests before committing.
- Prefer simple, readable code.
- Document important design decisions.

## License

SleepSplit is licensed under the MIT License. See [LICENSE](LICENSE) for details.
