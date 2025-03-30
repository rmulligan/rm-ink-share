# Test with Lines font
# This should display properly on Remarkable with filled characters

puts "size 1404 1872"  # Standard Remarkable portrait

# Set up pen and font
puts "pen black"
puts "line_width 1"

# Title
puts "set_font Lines 36"
puts "text 100 100 \"Lines Font Test\""

# Subtitle with timestamp
puts "set_font Lines 24"
puts "text 100 150 \"Created: 2025-03-28 23:37:59\""

# Body text
puts "set_font Lines 18"
puts "text 100 250 \"This text uses the Lines font family.\""
puts "text 100 300 \"Characters should appear filled, not as outlines.\""
puts "text 100 350 \"The content should be editable on the Remarkable tablet.\""

# Different sizes
puts "set_font Lines 28"
puts "text 100 450 \"Larger text (28pt)\""
puts "set_font Lines 14"
puts "text 100 500 \"Smaller text (14pt)\""

# Style variations
puts "set_font Lines-Italic 18"
puts "text 100 550 \"Italic text using Lines-Italic\""
puts "set_font LinesMono 18"
puts "text 100 600 \"Monospace text using LinesMono\""

# Line drawing
puts "line_width 2"
puts "moveto 100 650"
puts "lineto 600 650"

# Bullet points
puts "set_font Lines 18"
puts "text 100 700 \"• First bullet point\""
puts "text 100 750 \"• Second bullet point\""
puts "text 100 800 \"• Third bullet point with longer text that might wrap to another line\""
