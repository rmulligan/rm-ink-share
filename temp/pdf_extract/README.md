# PDF to Remarkable Conversion Tools

This directory contains tools for extracting text from PDFs and converting them to Remarkable-compatible formats with editable text.

## Requirements

- Python 3.6+
- `drawj2d` command-line tool in your PATH
- Python libraries: PyPDF2, BeautifulSoup4, requests

## Tools

### 1. Extract PDF Text (`extract_pdf_text.py`)

Extract text content from PDFs while preserving structure like paragraphs and headings.

```bash
python extract_pdf_text.py input.pdf [--output output.txt] [--hcl] [--title "Document Title"]
```

Options:
- `--output` / `-o`: Specify output text file (default: input filename with .txt extension)
- `--hcl`: Create an HCL script for use with drawj2d
- `--title`: Set document title for the HCL output

### 2. PDF to Remarkable Converter (`pdf_to_remarkable.py`)

Convert PDFs directly to Remarkable-compatible format with editable text using the Lines font.

```bash
python pdf_to_remarkable.py input.pdf [--output output.rmdoc] [--resolution 229] [--rm-only]
```

Options:
- `--output` / `-o`: Specify output file (default: input filename with .rmdoc extension)
- `--resolution` / `-r`: Set resolution (default: 229 for Remarkable Pro)
- `--rm-only`: Create only RM file, not RMDOC package

## How It Works

1. **Text Extraction**: Uses PyPDF2 to extract text from PDFs, preserving structure
2. **Document Formatting**: 
   - Generates HCL script for drawj2d
   - Uses Lines font for body text to ensure editability
   - Uses Roman font for headings
3. **Conversion**: Uses drawj2d to convert HCL to RM format
4. **Packaging**: Creates RMDOC package with metadata for Remarkable

## Font Settings

- **Title/Headings**: Roman font (will appear as outlines to be filled in manually)
- **Body Text**: Lines font (appears properly filled on Remarkable)

## Tips for Best Results

1. For simple documents, use the direct conversion with `pdf_to_remarkable.py`
2. For more complex documents:
   - Extract text with `extract_pdf_text.py --hcl`
   - Edit the HCL file manually to adjust formatting
   - Convert to RM format with drawj2d: `drawj2d -Trm -r229 -o output.rm input.hcl`

## Remarkable Pro Support

These tools are optimized for Remarkable Pro with:
- Higher resolution (`-r229`)
- Appropriate dimensions (1872x1404)
- Lines font for proper text appearance