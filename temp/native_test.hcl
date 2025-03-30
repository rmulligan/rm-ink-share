# Native RM format test
puts "size 1872 2404"

# Basic settings for RM
puts "line_width 1" 
puts "line_color black"

# Test different text methods
puts "set_font Helvetica-Bold 36"
puts "text_to_path 120 120 \"Test Header (path)\""

puts "set_font Helvetica 18"
puts "text_to_path 120 300 \"This text is converted to paths - should be editable\""

# Draw basic shapes
puts "line_width 2"
puts "moveto 120 400"
puts "lineto 600 400"

puts "circle 300 500 50"