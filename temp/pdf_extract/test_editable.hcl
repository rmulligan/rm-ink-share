# Test Remarkable document with editable content
# Generated at 2025-03-28 21:57:33

puts "size 1872 2404"

# Set up for vector paths (editable on device)
puts "line_width 1"
puts "line_color #000000"

# Title using text_to_path
puts "set_font Lines 36"
puts "text_to_path 120 120 \"Editable Content Test\""

# Subtitle
puts "set_font Lines 24"
puts "text_to_path 120 170 \"This document tests vector text paths\""

# Body text paragraphs
puts "set_font Lines 18"
puts "text_to_path 120 270 \"This is a paragraph with text converted to vector paths.\""
puts "text_to_path 120 310 \"All text should be editable on the Remarkable tablet.\""
puts "text_to_path 120 350 \"The Lines font is a single-line font supported by drawj2d.\""

# Italic text
puts "set_font Lines-Italic 18"
puts "text_to_path 120 430 \"This text uses the Lines-Italic font.\""

# Monospace text
puts "set_font LinesMono 18"
puts "text_to_path 120 510 \"This text uses the LinesMono font for code.\""

# Different sizes
puts "set_font Lines 24"
puts "text_to_path 120 590 \"Larger text size (24pt)\""
puts "set_font Lines 14"
puts "text_to_path 120 650 \"Smaller text size (14pt)\""

# Color test (for Remarkable Pro)
puts "pen inkblue"
puts "set_font Lines 24"
puts "text_to_path 120 730 \"Blue text for Remarkable Pro\""
puts "pen inkred"
puts "text_to_path 120 790 \"Red text for Remarkable Pro\""
puts "pen darkgreen"
puts "text_to_path 120 850 \"Green text for Remarkable Pro\""

# Reset pen color
puts "pen black"
