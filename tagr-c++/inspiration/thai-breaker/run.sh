#!/bin/sh

# 1) pipe the Thai UTF-8 input file into the syllable breaker
# 2) transform the output of syllable breaker into HTML
# 3) redirect to output file

INPUT=thai-input.txt
OUTPUT=thai-breaker-output.html

cat $INPUT |
./thai-breaker |
awk '
/* transform standard input into HTML5, appending a <br> tag to each line */
BEGIN {
	print "<!DOCTYPE html>"
	print "<html>"
	print "<head>"
	print "<meta charset=\"utf-8\">"
	print "</head>"
	print "<body>"
}
{
	print $0"<br />"
}
END {
	print "</body>"
	print "</html>"
}
' > $OUTPUT
