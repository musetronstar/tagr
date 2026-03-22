#pragma once

#include <cctype>
#include <ostream>
#include <string>

#include "tagl.h"

class tagr_tokenizer {
	TAGL::driver *_driver;
	std::ostream *_out;

	// TODO `.h` headers for definitionp; `.cc` for implementation
	void emit(const std::string& tok, size_t) {
		int token = _driver->lookup_pos(tok);
		const char *name = TAGL::token_str(token);

		// Emit the observed token as a token-value and token-type TSV line.
		(*_out) << tok << '\t' << name << '\n';
	}

	public:
		tagr_tokenizer(TAGL::driver *drv, std::ostream& out)
			: _driver{drv}, _out{&out} {}

		// TODO `.h` headers for definitionp; `.cc` for implementation
		void scan(const unsigned char *data, size_t len) {
			std::string tok;
			size_t tok_offset = 0;

			for (size_t i = 0; i < len; ++i) {
				unsigned char c = data[i];

				// Start or extend the current token until whitespace terminates it.
				if (!std::isspace(c)) {
					if (tok.empty())
						tok_offset = i;
					tok.push_back((char)c);
				} else if (!tok.empty()) {
					emit(tok, tok_offset);
					tok.clear();
				}
			}

			// Flush the trailing token when input does not end with whitespace.
			if (!tok.empty())
				emit(tok, tok_offset);
		}
};
