# Simple test for drawj2d

puts "size 1872 2404"

# Basic shapes
puts "pen black"
puts "line_width 2"
puts "moveto 200 200"
puts "lineto 400 200"
puts "lineto 400 400"
puts "lineto 200 400"
puts "lineto 200 200"

# Simple text
puts "set_font LinesMono 24"
puts "text 500 300 \"This is a test\""

# Text path
puts "set_font Lines 24"
puts "text_to_path 500 400 \"This is a path text\""

# Circle
puts "circle 300 600 100"