# Remarkable document for URL: https://docs.google.com/document/d/1IKuHKJu5xH5KFVCZ1X8N9JTwMd_INTPfpnuuLRGXfoo/
# Generated at 2025-03-29 00:08:54

puts "size 1404 1872"  # Standard Remarkable size (portrait)

# Set up for editable text with proper font
puts "pen black"
puts "line_width 1"

# Title
puts "set_font Lines 36"
puts "text 120 120 \"Error: Could not scrape https://docs.google.com/document/d/1IKuHKJu5xH5KFVCZ1X8N\""

# URL
puts "set_font Lines 18"
puts "text 120 190 \"Source: https://docs.google.com/document/d/1IKuHKJu5xH5KFVCZ1X8N9JTwMd_INTPfpnuuLRGXfoo/\""

# QR Code
puts "image 1402 120 350 350 \"/home/ryan/pi_share_receiver/output/qr_-7154474191615624020.png\""
puts "set_font Lines 18"
puts "text 120 330 \"Failed to scrape content: 404 Client Error: Not Found for url: https:/\""
puts "text 120 365 \"/docs.google.com/document/d/1IKuHKJu5xH5KFVCZ1X8N9JTwMd_INTPfpnuuLRGXf\""
puts "text 120 400 \"oo/edit\""
