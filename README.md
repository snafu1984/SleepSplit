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
- ID3 `TRCK` track-number assignment
- Automatic title numbering using ID3 `TIT2` tags
- Optional MP3 file renaming based on ID3 titles
- Sorting MP3 files into CD directories based on their `TPOS` tags
- Automatic M3U playlist creation for CD directories
- Combined processing options for full audiobook processing or iPod-compatible organization
- Dry-run mode to inspect planned operations without modifying files
- Command-line interface

SleepSplit processes MP3 files directly inside the specified directory. Subdirectories are not searched.

## Segment Lengths

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

## Track and Title Assignment

The optional `--track` argument assigns sequential track numbers to the generated MP3 files using the ID3 `TRCK` tag.

The optional `--title` argument prefixes the existing ID3 title (`TIT2`) with the corresponding track number.

Using `--title` automatically enables track-number assignment.

Example:

```bash
sleepsplit /path/to/audiobooks --track --title
```

## File Renaming

The optional `--file` argument renames output MP3 files based on their ID3 `TIT2` title tags.

Filenames are normalized to create consistent and filesystem-friendly names:

- German umlauts are converted (`ä` → `ae`, `ö` → `oe`, `ü` → `ue`).
- `ß` is converted to `ss`.
- Spaces and special characters are replaced with underscores.
- Consecutive underscores are collapsed.

Example:

```bash
sleepsplit /path/to/audiobooks --track --title --file
```

## CD Sorting and Playlists

The optional `--sort_cd` argument sorts MP3 files into separate directories based on their ID3 `TPOS` disc numbers.

Directories are named using two-digit disc numbers:

```text
CD01/
CD02/
CD03/
```

For each affected CD directory, SleepSplit creates or updates an M3U playlist containing the MP3 files in filename order.

Example:

```bash
sleepsplit /path/to/audiobooks --disk --sort_cd
```

The `--sort_cd` option requires valid disc-number information in the ID3 `TPOS` tags. Files without valid disc numbers are skipped with a warning.

## Combined Processing Options

SleepSplit provides two combined options for common workflows.

### Full processing: `--full`

The `--full` argument enables all available processing steps:

- `--disk`: assign disc numbers (`TPOS`)
- `--track`: assign track numbers (`TRCK`)
- `--title`: prefix titles (`TIT2`) with track numbers
- `--file`: rename MP3 files using their ID3 titles
- `--sort_cd`: sort files into CD directories and create M3U playlists

Example:

```bash
sleepsplit /path/to/audiobooks --full
```

### iPod-compatible processing: `--ipod`

The `--ipod` argument enables the following processing steps:

- `--track`: assign track numbers (`TRCK`)
- `--title`: prefix titles (`TIT2`) with track numbers
- `--file`: rename MP3 files using their ID3 titles

It does not assign disc numbers or sort files into CD directories.

Example:

```bash
sleepsplit /path/to/audiobooks --ipod
```

Both combined options can be used together with `--dry-run`.

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

### Command-line Options

| Option | Description |
|---|---|
| `--dry-run` | Preview planned operations without modifying files. |
| `--disk` | Assign disc numbers using ID3 `TPOS` tags. |
| `--track` | Assign track numbers using ID3 `TRCK` tags. |
| `--title` | Prefix ID3 titles with track numbers. Automatically enables `--track`. |
| `--file` | Rename MP3 files using their normalized ID3 titles. |
| `--sort_cd` | Sort files into CD directories and create M3U playlists. |
| `--full` | Enable all processing options. |
| `--ipod` | Enable track numbering, title assignment and file renaming. |

The positional directory argument is required for every invocation.

### Dry Run

Preview the planned cuts and post-processing operations without creating or modifying output files:

```bash
sleepsplit /path/to/audiobooks --full --dry-run
```

The dry-run mode also displays planned file renames, CD sorting operations and playlist creation where the necessary information is available.

### Processing Order

When multiple processing options are enabled, SleepSplit always uses the following order:

1. **Disc assignment:** Write ID3 `TPOS` tags.
2. **Track assignment:** Write ID3 `TRCK` tags.
3. **Title assignment:** Update ID3 `TIT2` tags with track numbers.
4. **File renaming:** Rename MP3 files based on their ID3 titles.
5. **CD sorting:** Move MP3 files into CD directories and create or update M3U playlists.

This order ensures that the metadata is assigned before filenames are changed and files are sorted into their final directories.

## Output

Output files are placed in a directory named after the album metadata, followed by `_cut`. Album names are normalized for use as directory names. If no album name is available, the output directory is named `cut`.

For example, an album named `Example Album` produces the directory `Example_Album_cut`.

Split files use sequential numbering:

```text
Example_Album_cut/
├── Chapter_001.mp3
├── Chapter_002.mp3
└── Chapter_003.mp3
```

Files that cannot be split because no suitable cut points are found are copied to the output directory without splitting.

Existing output files are not overwritten. If a planned output filename already exists, processing that file fails rather than replacing the existing file.

When CD sorting is enabled, the output directory additionally contains CD subdirectories and their corresponding playlists:

```text
Example_Album_cut/
├── CD01/
│   ├── Chapter_001.mp3
│   ├── Chapter_002.mp3
│   └── CD01.m3u
└── CD02/
    ├── Chapter_003.mp3
    └── CD02.m3u
```

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
