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
  - QR code for quick access to the original URL
  - Extracted content with proper formatting
- Uploads directly to Remarkable Cloud using rmapi

## Installation

### Prerequisites

- Python 3.9+
- [Remarkable API (rmapi)](https://github.com/juruen/rmapi) - for cloud uploads
- [drawj2d](https://gitlab.com/erw7/drawj2d) - for creating Remarkable documents
- Optional: Node.js (for JavaScript-enabled web scraping)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pi_share_receiver.git
   cd pi_share_receiver
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Optional JavaScript scraper dependencies:
   ```
   cd js
   npm install
   ```

4. Set up rmapi authentication:
   ```
   rmapi
   ```
   Follow the prompts to authenticate with your Remarkable account.

5. Install the service:
   ```
   ./setup_deps.sh
   ```

## Configuration

The pi_share_receiver can be configured using environment variables or the `config.py` file. Key configuration options include:

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| PI_SHARE_HOST | 0.0.0.0 | Host address to listen on |
| PI_SHARE_PORT | 9999 | Port to listen on |
| PI_SHARE_TEMP | ./temp | Temporary file directory |
| PI_SHARE_OUTPUT | ./output | Output directory for QR codes and other files |
| PI_SHARE_RMAPI | /usr/local/bin/rmapi | Path to rmapi executable |
| PI_SHARE_DRAWJ2D | /usr/local/bin/drawj2d | Path to drawj2d executable |
| PI_SHARE_RM_FOLDER | / | Remarkable cloud folder for uploads |
| PI_SHARE_MAX_RETRIES | 3 | Maximum retry attempts for network operations |
| PI_SHARE_RETRY_DELAY | 2 | Base delay between retries (seconds) |
| PI_SHARE_LOG_LEVEL | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| PI_SHARE_LOG_FILE | pi_share_receiver.log | Path to log file |

## Usage

### Run the server

```
python app/server.py
```

Or as a service:

```
sudo systemctl start pi_share_receiver
```

### Share a URL

Send a POST request to the server:

```
curl -X POST http://localhost:9999/share -d "https://example.com"
```

Or use the iOS Shortcuts app to send URLs directly.

### Testing

Run the test suite:

```
python -m unittest discover app/tests
```

## Remarkable Pro Compatibility

This application is optimized for the Remarkable Pro tablet with its larger 1872×2404 pixel screen dimensions. If you're using a different Remarkable device, you may need to adjust the dimensions in `app/services/document_service.py`.

## Troubleshooting

Check the log file at `pi_share_receiver.log` for detailed error information.

Common issues:
- **Upload failures**: Ensure rmapi is properly authenticated
- **Conversion errors**: Check that drawj2d is correctly installed
- **Blank documents**: May indicate web scraping issues with complex sites

## License

[Your chosen license]
