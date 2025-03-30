# Modified write.hcl for Remarkable document creation
# This version hardcodes the file to convert

# Set font to Lines with font size of 3.5 mm
puts "set_font Lines 3.5"

# Position of first line and maximum width
set x 15
set y 25
set maxw 138

# Open the hardcoded file and read it
puts "Read text from /home/ryan/pi_share_receiver/temp/pdf_extract/simple_demo.txt"
set f [open "/home/ryan/pi_share_receiver/temp/pdf_extract/simple_demo.txt" r]
fconfigure $f -encoding utf-8
set text [read $f]
close $f

# Set size for Remarkable
puts "size 1404 1872"

# Split text into lines and display
set y_pos $y
foreach line [split $text "\n"] {
  # Skip empty lines
  if {[string length $line] > 0} {
    puts "text $x $y_pos \"$line\""
    incr y_pos 5
  } else {
    incr y_pos 8
  }
}