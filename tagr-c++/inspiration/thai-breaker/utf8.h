#pragma once
#include <limits>

/*\
|*| Parts of the following code were borrowed from utf.c
|*| of the sqlite v3.7.17 distribution, which is in the
|*| Public Domain
|*|
|*| Thank you Dr. Hipp!
\*/

// append code point as utf8 to string
// and return number of bytes appended
size_t utf8_append(std::string&, char32_t);

// reads one code point from utf8 from input string,
// advances to the position past the last byte byte sequence,
// and returns the code point
// out of bounds returns 0 and set pos to std::string::npos
char32_t utf8_read(const std::string&, size_t*);

// returns the position of the start of the last byte sequence
// moving backwards from pos (or the end of the string if pos not given)
// returns std::string::npos if not found
size_t utf8_pos_back(const std::string&, size_t pos=std::string::npos);

// increments and returns code point
// returns 0xFFFD if cannot be incremented
char32_t utf8_increment(char32_t);

// returns whether a code point is valid for utf8 encoding
bool utf8_is_valid(char32_t);

/*
** This lookup table is used to help decode the first byte of
** a multi-byte UTF8 character.
*/
static const unsigned char sqlite3Utf8Trans1[] = {
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
  0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
  0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x00, 0x00,
};

// modified from WRITE_UTF8 macro to append to string
size_t utf8_append(std::string &s, char32_t c) {
	if (c == 0)
		return 0;

	char utf8[5] = {'\0','\0','\0','\0','\0'};
	size_t sz = 0;

	if ( c<0x00080 ) {
		utf8[sz++] = (c&0xFF);
	}
	else if ( c<0x00800 ) {
		utf8[sz++] = 0xC0 + ((c>>6)&0x1F);
		utf8[sz++] = 0x80 + (c & 0x3F);
	}
	else if ( c<0x10000 ) {
		utf8[sz++] = 0xE0 + ((c>>12)&0x0F);
		utf8[sz++] = 0x80 + ((c>>6) & 0x3F);
		utf8[sz++] = 0x80 + (c & 0x3F);
	} else {
		utf8[sz++] = 0xF0 + ((c>>18) & 0x07);
		utf8[sz++] = 0x80 + ((c>>12) & 0x3F);
		utf8[sz++] = 0x80 + ((c>>6) & 0x3F);
		utf8[sz++] = 0x80 + (c & 0x3F);
	}

	s.append(utf8);
	return sz;
}

// modified from sqlite3Utf8Read to deal with std::string
char32_t utf8_read(const std::string &s, size_t *pos) {
	if (s.empty()) {
		*pos = 0;
		return 0;
	}

	if (*pos == std::string::npos)
		return 0;

	if (*pos >= (s.size()-1)) {  // out of bounds
		*pos = std::string::npos;
		return 0;
	}

	unsigned int c = (unsigned char) s[(*pos)++];

	if ( c>=0xc0 ) {                           // 0xc0 == 11000000 - leading byte of multibyte sequence
		c = sqlite3Utf8Trans1[c-0xc0];         // value of leading byte
		while( (s[*pos] & 0xc0)==0x80 ) {      // 0x80 == 10000000 - continuation byte
			c = (c<<6) + (0x3f & s[(*pos)++]); // 0x3f == 00111111 - shift in value of each continuation byte
		}
		if( c<0x80                             // leading byte w/o continuation bytes
			|| (c&0xFFFFF800)==0xD800          // UTF16 surrogate
			|| (c&0xFFFFFFFE)==0xFFFE )        // 11111110 - leading byte w/ no space for value
		{  c = 0xFFFD; }                       // replacement character �
	}

	return c;
}

size_t utf8_pos_back(const std::string &s, size_t pos) {
	if (s.size() == 0)
		return std::string::npos;

	if (pos == std::string::npos)
		pos = s.size() - 1;

	do {
		if ( (unsigned char)s[pos] < 0x80     // regular ASCII
		  || (unsigned char)s[pos] >= 0xc0 )  // leading multibyte sequence
			return pos;
	} while (pos-- != 0);

	return std::string::npos;
}

char32_t utf8_increment(char32_t cp) {
	if ((cp + 1) >= std::numeric_limits<char32_t>::max())
		return 0xFFFD;

	cp++;

	if ( cp == 0xFFFD )
		return (cp + 1);  // advance past replacement sequence

	if ( (cp>=0xD800 && cp<=0xDFFF) )
		return (0xDFFF + 1);  // advance past UTF16 surrogate

	if ( (cp&0xFFFFFFFE)==0xFFFE )
		return 0xFFFD;   // no room for value

	return cp;
}

bool utf8_is_valid(char32_t cp) {
	return (
		cp <= std::numeric_limits<char32_t>::max() &&
		cp != 0xFFFD &&             // replacement sequence
		!(cp >= 0xD800 && cp <= 0xDFFF) && // UTF16 surrogate
		(cp & 0xFFFFFFFE) != 0xFFFE // no room for value
	);
}
