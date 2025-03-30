# Pi Share Receiver

Receives URLs shared from iOS Shortcuts via Tailscale, generates QR codes, intelligently parses web content, and uploads richly formatted editable documents optimized for Remarkable Pro tablets.

## Features

- Receives URLs from iOS Shortcuts via HTTP POST
- Generates QR codes for easy scanning
- Advanced content processing:
  - JavaScript-enabled web scraping using Playwright for modern web apps
  - PDF extraction and conversion to editable Remarkable format
  - Intelligent content structure detection
- Intelligently parses web content with proper structure:
  - Preserves headings with proper formatting and font sizes
  - Handles images with captions
  - Formats code blocks with monospace font and background
  - Preserves lists with proper indentation
  - Formats blockquotes with distinctive styling
- Creates editable Remarkable documents (lines v6 format) containing:
  - The page title using Lines-Bold font with colored underline
  - Source URL reference with highlight color
  - QR code with dashed border for quick access to the original URL
  - Structured content with visual separation using dashed boxes
- Optimized for Remarkable Pro:
  - Uses exclusively Lines font family for properly filled-in text
  - Distinguishes code blocks through background and dashed borders rather than font change
  - Takes advantage of color display for visual hierarchy
  - Properly sized for Remarkable Pro dimensions
  - Uses dashed borders for visual separation of content blocks
- Documents are created using HCL and converted with drawj2d
- Uploads to Remarkable Cloud using rmapi for access on the tablet

## Setup

1. Run the `setup.sh` script (if you haven't already).
2. Place the `server.py` script inside the `app/` directory.
3. Edit `app/server.py` to configure settings:
   - `QR_OUTPUT_PATH`: Where QR codes are saved
   - `TEMP_DIR`: Where temporary files are stored
   - `RMAPI_PATH`: Path to rmapi executable
   - `DRAWJ2D_PATH`: Path to drawj2d executable
   - `RM_FOLDER`: Remarkable Cloud folder to upload to
4. Make sure rmapi and drawj2d are installed and rmapi is authenticated
5. Activate the virtual environment: `source venv/bin/activate`
6. Install dependencies: `pip install -r requirements.txt`

## Running the Service

### Manual Start
To run the server manually:
```
source venv/bin/activate
python app/server.py
```

### As a System Service
A systemd service file is provided for running as a background service:

1. Install the service:
   ```
   ./service.sh install
   ```

2. Start the service:
   ```
   ./service.sh start
   ```

3. Enable automatic start at boot:
   ```
   ./service.sh enable
   ```

4. Check service status:
   ```
   ./service.sh status
   ```

5. View service logs:
   ```
   ./service.sh logs
   ```

## Testing

A test script is provided to quickly verify the service is working:

```
./test_service.sh
```

This will send a test URL to the service. You can also specify your own URL:

```
./test_service.sh https://example.com
```

Check the service logs to see if the URL was processed successfully.

## Usage

Configure an Apple Shortcut to send a POST request with the URL to `http://<PI_TAILSCALE_IP>:9999/share`

The server accepts URLs in two formats:
- JSON format: `{"url": "https://example.com"}`
- Plain text: Simply the URL as the request body

## Process Flow

1. URL is received via HTTP POST
2. Web content is scraped from the URL
3. QR code is generated for the URL
4. HCL script is created with the content formatting
5. drawj2d converts the HCL script to Remarkable's lines v6 format (rmdoc)
6. The rmdoc is uploaded to Remarkable Cloud via rmapi
7. The document appears on the Remarkable tablet in editable format

## Requirements

- Python 3.x
- Flask
- qrcode[pil]
- requests
- beautifulsoup4
- playwright (for JavaScript rendering)
- pypdf2 (for PDF extraction)
- drawj2d (installed separately)
- rmapi (installed separately)

You can install all Python dependencies by running:
```
./setup_deps.sh
```
