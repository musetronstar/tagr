#include <iostream>
#include <functional>
#include <vector>
#include "utf8.h"



/*\
|*| Reads contiguous lines of Thai script encoded in UTF-8 from stdin
|*| and prints a space between each syllable.
\*/

/*** Thai character categories ***/

// Preposed vowel
// เ แ โ ใ ไ
inline bool is_V1(char32_t ch) {
	return (ch >= 0x0E40 && ch <= 0x0E44);
}

/* Preposed vowel
ก ข ฃ ค ฅ ฆ ง จ
ฉ ช ซ ฌ ญ ฎ ฏ
ฐ ฑ ฒ ณ ด ต ถ
ท ธ น บ ป ผ ฝ พ
ฟ ภ ม ย ร ฤ ล ฦ
ว ศ ษ ส ห ฬ อ ฮ
*/
inline bool is_C1(char32_t ch) {
	return (ch >= 0x0E01 && ch <= 0x0E2E);
}

// Clustered consonant
// ร ล ว น ม
bool is_C2(char32_t ch) {
	switch (ch) {
		case 0x0E19:
		case 0x0E21:
		case 0x0E23:
		case 0x0E25:
		case 0x0E27:
			return true;
		default:
			return false;
	}
}

// Super- or subscript vowel
// ◌ิ ◌ี ◌ึ ◌ื ◌ุ ◌ู ◌ั ◌
bool is_V2(char32_t ch) {
	switch (ch) {
		case 0x0E31:
		case 0x0E34:
		case 0x0E35:
		case 0x0E36:
		case 0x0E37:
		case 0x0E38:
		case 0x0E39:
		case 0x0E47:
			return true;
		default:
			return false;
	}
}

// Superscript tone mark
// ◌่ ◌ ้ ◌๊ ◌่
bool is_T(char32_t ch) {
	switch (ch) {
		case 0x0E48:
		case 0x0E49:
		case 0x0E4A:
		case 0x0E4B:
			return true;
		default:
			return false;
	}
}

// Postposed vowel or glide
// า อ ย ว
bool is_V3(char32_t ch) {
	switch (ch) {
		case 0x0E22:
		case 0x0E27:
		case 0x0E2D:
		case 0x0E32:
			return true;
		default:
			return false;
	}
}

// Final consonant
// ง น ม ด บ ก ย ว
bool is_C3(char32_t ch) {
	switch (ch) {
		case 0x0E01:
		case 0x0E07:
		case 0x0E14:
		case 0x0E19:
		case 0x0E1A:
		case 0x0E21:
		case 0x0E22:
		case 0x0E27:
			return true;
		default:
			return false;
	}
}

/*** END Thai character categories ***/

// FSM state handler lambdas
// return true only on final states
typedef std::function<bool()> state_function_t;

// vector to hold offets to the beginning of each syllable
// within a UTF-8 string of Thai script
typedef std::vector<size_t> offsets_t;

/*
 * scans an input string of Thai UTF-8 text populating an offset vector
 * with the start position of each syllable
 *
 * returns 0 on success or error code on invalid input
 */
int scan_syllables(offsets_t& breaks, const std::string& input, size_t lineno) {
	size_t pos = 0;       // current offset within input
	size_t prev = 0;      // previous offset within input
	char32_t ch = '\0';   // current scanned codepoint

	auto f_error = [&]() -> int {
		std::cerr << "invalid input: 0x" << std::hex << (char16_t)ch
			<< ", position " << std::dec << pos
			<< ", line " << lineno << std::endl;
		return 1;
	};

	// scan next codepoint
	auto f_next = [&]() {
		prev = pos;
		ch = utf8_read(input, &pos);  // ch will be 0 if at end
	};

	/*\
	|*| Each of the following FSM state lambdas check for
	|*| accepted character categories and call their corresponding
	|*| state transitions.  If any characters are not accepted,
	|*| a state will return false, indicating invalid input.
	|*|
	|*| Only final states 7, 8, or 9 can return true
	\*/
	state_function_t state[10];

	state[0] = [&]() -> bool {
		f_next();
		if (is_V1(ch)) return state[1]();
		if (is_C1(ch)) return state[2]();

		return false;
	};

	state[1] = [&]() -> bool {
		f_next();
		if (is_C1(ch)) return state[2]();

		return false;
	};

	state[2] = [&]() -> bool {
		f_next();
		if (is_C2(ch)) return state[3]();
		if (is_V2(ch)) return state[4]();
		if (is_T(ch))  return state[5]();
		if (is_V3(ch)) return state[6]();
		if (is_C3(ch)) return state[9]();
		if (is_V1(ch)) return state[7]();
		if (is_C1(ch)) return state[8]();

		return false;
	};

	state[3] = [&]() -> bool {
		f_next();
		if (is_V2(ch)) return state[4]();
		if (is_T(ch))  return state[5]();
		if (is_V3(ch)) return state[6]();
		if (is_C3(ch)) return state[9]();

		return false;
	};

	state[4] = [&]() -> bool {
		f_next();
		if (is_T(ch))  return state[5]();
		if (is_V3(ch)) return state[6]();
		if (is_C3(ch)) return state[9]();
		if (is_V1(ch)) return state[7]();
		if (is_C1(ch)) return state[8]();

		return false;
	};

	state[5] = [&]() -> bool {
		f_next();
		if (is_V3(ch)) return state[6]();
		if (is_C3(ch)) return state[9]();
		if (is_V1(ch)) return state[7]();
		if (is_C1(ch)) return state[8]();

		return false;
	};

	state[6] = [&]() -> bool {
		f_next();
		if (is_C3(ch)) return state[9]();
		if (is_V1(ch)) return state[7]();
		if (is_C1(ch)) return state[8]();

		return false;
	};

	state[7] = [&]() -> bool {
		// no break at end of input
		if (pos == input.size())
			return true;

		// break at the position of the previous character
		breaks.push_back(prev);

		return state[1]();
	};

	state[8] = [&]() -> bool {
		// no break at end of input
		if (pos == input.size())
			return true;

		// break at the position of the previous character
		breaks.push_back(prev);

		return state[2]();
	};

	state[9] = [&]() -> bool {
		// no break at end of input
		if (pos == input.size())
			return true;

		// break at position of the current character
		breaks.push_back(pos);

		return true;
	};

	// scan until end of string (ch == 0) or invalid input
	do {
		if (!state[0]() && ch)
			return f_error();
	} while (ch);

	return 0;  // ok
}

// outputs to a stream a string inserting spaces at each syllable break offset
void print_syllables(std::ostream& os, const offsets_t& breaks, const std::string& s) {
	size_t prev = 0;
	for (size_t cur : breaks) {
		os << s.substr(prev, (cur-prev)) << ' ';
		prev = cur;
	}
	os << s.substr(prev) << std::endl;
}

int main() {
	// get each line of standard input until EOF
	size_t lineno = 0;
	for (std::string line; std::getline(std::cin, line);) {
		offsets_t breaks;  // offsets to the start of syllable breaks
		int err = scan_syllables(breaks, line, ++lineno);
		if (err != 0) return err;
		print_syllables(std::cout, breaks, line);
	}

	return 0;
}
