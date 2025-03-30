# Minimal test with only built-in Hershey font
# Draw with just basic lines and simple text

puts "size 1872 2404"

# Simple white canvas with black lines
puts "line_width 1.0"
puts "line_color black"

# Draw a title line that is very basic
puts "set_font Lines 24"
puts "text_to_path 100 100 \"Basic Test Document\""

# Draw some simple vector shapes
puts "moveto 100 200"
puts "lineto 500 200"
puts "lineto 500 400"
puts "lineto 100 400"
puts "lineto 100 200"

# Add text with built-in hershey font
puts "set_font Lines 18"
puts "text_to_path 200 300 \"Simple Text with Lines font\""