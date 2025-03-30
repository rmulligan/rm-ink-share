# Final test for PDF output
puts "size 1872 2404"

# Basic settings
puts "line_width 1" 
puts "line_color black"

# Title text
puts "set_font Helvetica-Bold 36"
puts "text 120 120 \"PDF Solution Test\""

# URL
puts "set_font Helvetica 18"
puts "text 120 200 \"Source: https://docs.mulligan.dev/test-url\""

# Body text
puts "set_font Helvetica 18"
puts "text 120 300 \"This content is rendered as a PDF which will display correctly\""
puts "text 120 330 \"on the Remarkable tablet, though it won't be directly editable.\""
puts "text 120 360 \"This is a good compromise solution for URL sharing.\""

# Draw a line 
puts "line_width 2"
puts "moveto 120 400"
puts "lineto 600 400"

# Draw a circle
puts "circle 300 500 50"