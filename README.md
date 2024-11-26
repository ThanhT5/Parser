# PDF Parser Setup on macOS

This README provides step-by-step instructions for setting up the project directory, initializing a virtual environment, and installing dependencies for the PDF parsing project on macOS.

## Project Structure

Organize your project with the following directory structure:

```plaintext
pdf_parser_project/
│
├── README.md                   # Project documentation
├── LICENSE                      # License information
├── requirements.txt             # Python dependencies
├── venv/                        # Virtual environment (optional but recommended)
│
├── data/                        # Sample PDF files for testing
│   └── example.pdf              # Sample or test PDF file
│
├── src/                         # Source code directory
│   ├── __init__.py              # Marks 'src' as a package
│   ├── pdf_parser.py            # Main PDF parser script
│   ├── utils.py                 # Utility functions (helper methods)
│   └── config.py                # Configuration for paths and settings
│
├── output/                      # Directory for parsed output (e.g., JSON/XML)
│   └── parsed_output.json       # Sample output file
│
├── tests/                       # Test cases for unit and integration testing
│   ├── test_pdf_parser.py       # Unit tests for PDF parser functions
│   └── test_text_extraction.py  # Test cases for text extraction and formatting
│
└── logs/                        # Logs directory for debugging and monitoring
    └── pdf_parser.log           # Log file for parsing process
```

### Step 1: Installing Python 3 on macOS

Most macOS systems come with Python pre-installed, but you may want to install the latest version of Python 3. To check if Python 3 is installed, run:

```bash
python3 --version
```

If Python 3 is not installed, follow these steps:

1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python 3 using Homebrew:
   ```bash
   brew install python
   ```

3. Verify the installation:
   ```bash
   python3 --version
   ```

### Step 2: Set Up a Virtual Environment (Recommended)

A virtual environment isolates the dependencies for your project. Follow these steps to set up and activate a virtual environment:

1. Install `virtualenv`:
   ```bash
   pip3 install virtualenv
   ```

2. Create a virtual environment inside the project folder:
   ```bash
   virtualenv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

After activating the virtual environment, any Python packages installed will be contained within this environment and won’t affect other projects.

To deactivate the virtual environment, simply run:
```bash
deactivate
```

### Step 3: Install Dependencies

All project dependencies are listed in the `requirements.txt` file. Here’s how to install them:

1. Create a `requirements.txt` file in your project root directory and list your dependencies. Example:
   ```plaintext
   pdfplumber
   pdfminer.six
   Pillow
   ```

2. Install the dependencies using pip:
   ```bash
   pip3 install -r requirements.txt
   ```

This will install all the necessary packages, including:
- **pdfplumber**: For extracting text from PDFs.
- **pdfminer.six**: For advanced PDF parsing and layout extraction.
- **Pillow**: For handling images within PDFs.
