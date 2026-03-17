#include <iostream>
#include <cassert>
#include "utf8.h"

int scan(std::string& output, const std::string& input, size_t lineno) {
	bool is_valid = true;  // error flag
	size_t pos = 0;  // current offset within the UTF-8 input
	char32_t cur;  // current codepoint

	auto f_error = [&]() {
		std::cerr << "invalid input: position " << pos
					<< ", line " << lineno << std::endl;
		is_valid = false;
	};

	// get next unicode code point
	auto f_next = [&]() {
		cur = utf8_read(input, &pos);
		if (!utf8_is_valid(cur)) {
			f_error();
			return 0;
		}
	};

	while (is_valid && pos < input.size())  {
		f_next();
		utf8_append(output, cur);
	}

	if (is_valid) {
		return 0;  // ok
	} else {
		f_error();
		return 1;  // error
	}
}

// tokenized each line of standard input until
// invalid input or end of file
int main() {

	std::string line;
	size_t lineno = 0;
	while (std::getline(std::cin, line)) {
		std::string output;
		int err = scan(output, line, ++lineno);
		std::cout << line << std::endl;
		std::cout << output << std::endl;
		assert(output == line);
	}

	return 0;
}
