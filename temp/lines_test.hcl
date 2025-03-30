# Test with Lines font
puts "size 1872 2404"

# Basic settings
puts "line_width 1" 
puts "line_color black"

# Text with Lines font - which should be more compatible with Remarkable
puts "set_font Lines-Bold 36"
puts "text_to_path 120 120 \"Test with Lines font\""

puts "set_font Lines 18"
puts "text_to_path 120 300 \"Using Lines font with text_to_path for better compatibility\""

# Draw a simple line 
puts "line_width 2"
puts "moveto 120 400"
puts "lineto 600 400"

# Draw a circle
puts "circle 300 500 50"