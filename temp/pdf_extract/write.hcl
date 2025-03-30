#!/usr/bin/env hecl
# write.hcl -- Write text onto a page
# Example usage:
#  drawj2d -Trmdoc write.hcl textfile.txt
#
# Requirements:
# * textfile.txt should have UTF-8 encoding

if {[llength $argv] < 1} {
    puts "usage: write.hcl <textfile>"
    exit
}

set filename [lindex $argv 0]

if {![file exists $filename]} {
    puts "Error: $filename does not exist."
    exit
}

# Open file and read contents
set f [open $filename r]
fconfigure $f -encoding utf-8
set text [read $f]
close $f

# Set font to single line font "Lines" with font size of 3.5 mm
# The Lines font supports Basic Latin, Latin-1, Greek, Latvian, Polish, Russian
# letters (Glyphs 0x20-0x7e 0xa0-0x17f 0x380-0x3f6 0x400-0x45f 0x490-0x4f9)
set fontname "Lines"
set fontsize 3.5

# Position of first line
set x 15
set y 5

# Maximum width of a line (x + maxw should not exceed the page width)
set maxw 138

# Write text to page
write_text $text $x $y $maxw $fontsize $fontname
