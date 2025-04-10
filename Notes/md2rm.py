#!/home/ryan/remarkable_ai/venv/bin/python
"""
Convert Markdown to reMarkable format.
This script converts Markdown files to reMarkable's native format for optimal display.
"""
import os
import subprocess
import tempfile
import argparse
import markdown
from bs4 import BeautifulSoup

def markdown_to_html(markdown_text):
    """Convert markdown text to HTML."""
    return markdown.markdown(markdown_text)

def html_to_text(html_content):
    """Extract text content from HTML, preserving structure."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.extract()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading/trailing space
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Remove blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def markdown_to_hcl(markdown_text, output_file):
    """Convert markdown to Hierarchical Content Language (HCL) format."""
    html = markdown_to_html(markdown_text)
    text = html_to_text(html)
    
    # Create HCL file
    with open(output_file, 'w') as f:
        f.write("doc {\n")
        f.write("  page {\n")
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            f.write(f'    text "{para}"\n')
            f.write("    br\n")
        
        f.write("  }\n")
        f.write("}\n")
    
    return output_file

def generate_output(hcl_file, output_file, format_type="rm"):
    """Generate reMarkable format file from HCL file using drawj2d."""
    if not os.path.exists(hcl_file):
        raise FileNotFoundError(f"HCL file not found: {hcl_file}")
    
    # Use drawj2d to convert HCL to reMarkable format
    try:
        subprocess.run(["drawj2d", hcl_file, "-o", output_file, f"--{format_type}"], 
                    check=True, capture_output=True, text=True)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to reMarkable format')
    parser.add_argument('input_file', help='Input Markdown file')
    parser.add_argument('-o', '--output', help='Output file', default=None)
    parser.add_argument('-f', '--format', choices=['rm', 'pdf', 'svg', 'png'], 
                        default='rm', help='Output format (default: rm)')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}")
        return 1
    
    # Default output filename if not specified
    if args.output is None:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f"{base_name}.{args.format}"
    
    # Create temporary HCL file
    with tempfile.NamedTemporaryFile(suffix='.hcl', delete=False) as tmp:
        temp_hcl = tmp.name
    
    try:
        # Read markdown file
        with open(args.input_file, 'r') as f:
            markdown_text = f.read()
        
        # Convert to HCL
        markdown_to_hcl(markdown_text, temp_hcl)
        
        # Generate output in desired format
        generate_output(temp_hcl, args.output, args.format)
        
        print(f"Converted {args.input_file} to {args.output}")
        return 0
    finally:
        # Clean up temporary file
        if os.path.exists(temp_hcl):
            os.unlink(temp_hcl)

if __name__ == "__main__":
    exit(main())
