# Minimal example that should display on reMarkable
# Based strictly on the wiki examples

puts "size 1872 2404"  # reMarkable Pro dimensions

# Draw a simple line
puts "line_width 1"
puts "moveto 100 100"
puts "lineto 300 100"

# Add simple text
puts "set_font Lines 24"
puts "text 100 200 \"Hello reMarkable\""