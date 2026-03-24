#pragma once

#include <cstddef>
#include <memory>
#include <ostream>
#include <string>
#include <vector>

#include "tagsh.h"

static constexpr size_t MAX_TOKEN_POSITIONS = 64;

struct trie_value {
	// offset_count doubles as the occurrence count for now.
	size_t offset_count;

	// Byte offsets where this token occurred in the input stream.
	size_t offsets[MAX_TOKEN_POSITIONS];

	trie_value();
	void add_offset(size_t offset);
};

class trie;

class tagr_tokenizer {
	TAGL::driver *_driver;
	std::ostream *_out;
	std::unique_ptr<trie> _trie;

	void emit(const std::string& tok, size_t offset);

	public:
		tagr_tokenizer(TAGL::driver *drv, std::ostream& out);
		~tagr_tokenizer();
		void scan(const unsigned char *data, size_t len);
		void print_trie(std::ostream& out) const;
};

class tagr_args : public cmd_args {
	public:
		std::vector<std::string> scan_fnames;
		bool opt_print_events = false;

		tagr_args();
		void parse(int argc, char **argv);
};

class tagr : public tagsh {
		tagr_tokenizer _tokenizer;
		bool _opt_print_events;

	public:
		tagr(tagdb_type *tdb, bool opt_print_events = false);
		tagd::code scan_fd(int fd);
		tagd::code scan_fname(const std::string& fname);
		tagd::code scan_stdin();
};
