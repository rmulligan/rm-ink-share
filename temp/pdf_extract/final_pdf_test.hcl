# PDF test for Remarkable
# Generate a PDF that should display correctly

puts "size 1404 1872"  # Standard remarkable size (portrait)
puts "line_width 1"
puts "pen black"

# Draw a border
puts "moveto 100 100"
puts "lineto 1300 100"
puts "lineto 1300 1772"
puts "lineto 100 1772"
puts "lineto 100 100"

# Add title
puts "set_font Lines 36"
puts "text_to_path 200 200 \"PDF Test Document\""

# Add timestamp
puts "set_font Lines 18"
puts "text_to_path 200 250 \"Created at 2025-03-28 22:20:46\""

# Add testing text
puts "set_font Lines 24"
puts "text_to_path 200 400 \"This is a test using PDF format\""
puts "text_to_path 200 450 \"This document should display on the Remarkable\""

# Draw some shapes
puts "circle 300 600 50"
puts "rect 500 550 100 100"
puts "moveto 700 550"
puts "lineto 800 650"
puts "moveto 800 550"
puts "lineto 700 650"
