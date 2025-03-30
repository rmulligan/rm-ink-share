# Test with Roman font

puts "size 1872 2404"  # reMarkable Pro dimensions

# Draw a simple line
puts "line_width 1"
puts "moveto 100 100"
puts "lineto 300 100"

# Add simple text with Roman font
puts "set_font Roman 24"
puts "text 100 200 \"Hello reMarkable (Roman font)\""