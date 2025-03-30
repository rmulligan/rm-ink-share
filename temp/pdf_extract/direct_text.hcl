# Direct text approach for Remarkable
# Generated manually with text commands

puts "size 1404 1872"

puts "line_width 1"
puts "pen black"

# Title
puts "set_font Lines 24"
puts "text 50 100 \"Test Document for Remarkable\""

# Body text
puts "set_font Lines 18"
puts "text 50 150 \"This is a direct test using drawj2d.\""
puts "text 50 180 \"When displayed on Remarkable, this text should be editable.\""
puts "text 50 210 \"Lines font should be properly supported for editing.\""

# Bullet points
puts "text 50 260 \"• Key points from the wiki examples:\""
puts "text 70 290 \"• Use Lines font for editable text\""
puts "text 70 320 \"• The -Trm format creates editable RM files\""
puts "text 70 350 \"• Simple content is more reliable\""

# Test different font sizes
puts "set_font Lines 36"
puts "text 50 420 \"Large Text\""
puts "set_font Lines 12"
puts "text 50 460 \"Small Text\""

# Draw some shapes for testing
puts "line_width 2"
puts "moveto 50 500"
puts "lineto 300 500"
puts "lineto 300 600"
puts "lineto 50 600"
puts "lineto 50 500"