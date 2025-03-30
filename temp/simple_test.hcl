# Simple test for editable content
puts "size 1872 2404"

# Basic settings
puts "line_width 1" 
puts "line_color black"

# Test text_to_path
puts "set_font Helvetica-Bold 36"
puts "text_to_path 120 120 \"Test Header\""

# Test regular text for comparison
puts "set_font Helvetica 18"
puts "text 120 200 \"This is regular text - should not be editable\""

# More text_to_path
puts "set_font Helvetica 18"
puts "text_to_path 120 300 \"This should be editable on device via text_to_path\""

# Draw a simple line 
puts "line_width 2"
puts "moveto 120 400"
puts "lineto 600 400"

# Draw a circle
puts "circle 300 500 50"