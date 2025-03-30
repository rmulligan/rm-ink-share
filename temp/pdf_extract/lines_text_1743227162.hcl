# HCL for simple text document with Lines font
# Generated: 2025-03-28 22:46:02
# Title: test_content.txt

puts "size 1404 1872"  # Standard Remarkable size

# Set up pen and font
puts "pen black"
puts "line_width 1"
puts "set_font Lines 18"  # Using Lines font at readable size

# Add title (larger font)
puts "set_font Lines 24"
puts "text 100 100 \"test_content.txt\""
puts "set_font Lines 18"  # Back to normal font size

puts "text 100 150 \"Test Document for Remarkable\""
puts "text 100 210 \"This is a simple test document to verify that text content is properly converted to an editable format on the Remarkable tablet.\""
puts "text 100 270 \"The key requirements:\""
puts "text 100 300 \"- Content must be editable on the tablet\""
puts "text 100 330 \"- Text should be rendered using the Lines font\""
puts "text 100 360 \"- Document should be properly formatted\""
puts "text 100 420 \"When converting web content:\""
puts "text 100 450 \"1. Extract the main text content\""
puts "text 100 480 \"2. Format it as plain text\""
puts "text 100 510 \"3. Use the text_to_remarkable.py script to create a document\""
puts "text 100 540 \"4. Upload to the Remarkable tablet\""
puts "text 100 600 \"This approach is based on the successful md2rm tool which creates editable content on the Remarkable tablet.\""
