
# PDF Parsing and Standardization Tool

This tool is designed to parse PDF files or URLs and standardize their content into a structured JSON format. It utilizes the Mineru API for PDF parsing and processes the parsed results to generate standardized JSON files.

## Features

- **PDF File Parsing**: Supports batch parsing of local PDF files and directories.
- **URL Parsing**: Supports parsing remote PDF files via URLs.
- **Content Standardization**: Standardizes the parsed content into structured JSON files.
- **Multi-process Handling**: Uses multi-processing to handle multiple PDF files or URLs in parallel, improving efficiency.

## Dependencies

- Python 3.x
- `requests` library
- `multiprocessing` library
- `zipfile` library
- `json` library
- `os` library
- `sys` library
- `string` library

## Installation

1. Clone this repository to your local machine:
   ```bash
   https://github.com/freezed-corpse-143/afterMineru.git

2. Navigate to the project directory
   ```
   cd afterMineru
   ```

## Usage

### 1. Set Mineru API Key

Before running the script, ensure that the `MINERU_API_KEY` environment variable is set:

> [!WARNING]
>
> Please select a proxy region close to China.

```bash
# linux
export MINERU_API_KEY='your_mineru_api_key'

# windows
setx MINERU_API_KEY "your_mineru_api_key"
```

Get `MINERU_API_KEY` [mineru]([MinerU](https://mineru.net/apiManage/docs))

### 2. Run the Script

#### Parse Local PDF Files or Directories

```bash
python mineru_parser.py /path/to/pdf/file.pdf
```

or

```bash
python mineru_parser.py /path/to/pdf/directory
```

#### Parse Remote PDF File URLs

```bash
python mineru_parser.py https://example.com/file.pdf
```

#### Parse Both Local Files and Remote URLs

```bash
python mineru_parser.py /path/to/pdf/file.pdf https://example.com/file.pdf
```

### 3. Output

The parsed JSON files will be saved in the `./output` directory, with filenames corresponding to the input PDF files or URLs.

## File Structure

- `mineru_parser.py`: The main script responsible for parsing and standardizing PDF files and URLs.
- `json_standardize.py`: A helper script that standardizes the parsed JSON data.
- `README.md`: Project documentation.

## Notes

- Ensure that the Mineru API key is valid and that the API usage limits are sufficient.
- When parsing remote PDF files, ensure that the URL is valid and the file is accessible.
- The output JSON files will overwrite existing files with the same name. Ensure that important data is backed up.
