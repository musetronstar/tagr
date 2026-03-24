#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstring>
#include <fstream>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <vector>

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include <event2/buffer.h>

#include "tagr.h"

trie_value::trie_value() :
	offset_count{0},
	offsets{}
{}

void trie_value::add_offset(size_t offset) {
	if (offset_count < MAX_TOKEN_POSITIONS)
		offsets[offset_count++] = offset;
}

tagr_tokenizer::tagr_tokenizer(TAGL::driver *drv, std::ostream& out) :
	_driver{drv},
	_out{&out},
	_trie{nullptr}
{}

// returns true if file exists and optionally sets a filesize pointer
bool file_exists(const char *fname, size_t *sz=nullptr) {
	struct stat st_buf;
	if(stat(fname, &st_buf) != 0)
		return false;

	if (sz) *sz = st_buf.st_size;

	return true;
}

// mmap wrapper - holds a reference to a memory mapped file
// destructor handles unmapping automatically
struct mmap_t {
	char *data;  // bytes returned by mmap
	size_t size; // size of the mmapped file
	std::string fname;

	mmap_t() = delete;  // no default constructor

	// construct memory map given filname
	// throws invalid_argument exception for errors caused by filename argument, otherwise runtime_error
	mmap_t(const char *f) : data{nullptr}, size{0}, fname{f} {
		// TODO use `file_exists` defined in `tagd/tagd/include/tagd/io.h`

		if (!file_exists(fname.c_str(), &size))
			throw std::invalid_argument(std::string("no such file: ").append(fname));

		// open file read only and return a file descriptor
		int fd = open(fname.c_str(), O_RDONLY);
		if (fd < 0)
			throw std::runtime_error(std::string("failed to open file: ").append(fname));

		// Memory map the read only file descriptor. MAP_SHARED flag allows the map to be shared by other processes.
		// void * mmap (void *address, size_t length, int protect, int flags, int filedes, off_t offset)
		data = (char *) mmap(0, size, PROT_READ, MAP_SHARED, fd, 0);
		close(fd); // file descriptor not needed after mmap

		if (data == MAP_FAILED)
			throw std::runtime_error(std::string("failed to memory map file: ").append(fname));
	}

	~mmap_t() {
		// unmap memory from address to (address + length)
		if (data) munmap(data, size);
	}
};

// forward declare because nodes refer to nodes
struct node;

// represents a trie node for a token at a position in the input byte stream 
struct node {
	// array of node pointers, indexed by byte value
	node* data[256];

	/*
	 * TODO
	 * the terminal node marks the end of a token
	 * since this prototype has not yet dealt with tokens that are contained in other tokens as their prefix
	 *
	 * Also, we could make `val` to be a trei_val pointer set to `nullptr` when terminal node
	 */
	bool term;

	trie_value val;  // data at this node (set when term == true)

	node() :
		// C++11 value initialization of pointer array defaults to nullptr
		data{},
		term{false}
	{}

	// delete all allocated nodes cascading downwards
	~node() {
		for (int i=0; i<256; i++) {
			if (data[i]) delete data[i];
		}
	}
};

// holds a trie structure of values
struct trie {
	node root;  // root node of the trie

	trie() : root() {}

	// construct trie given filename of bytes
	// throws invalid_argument exception for errors caused by filename argument, otherwise runtime_error
	trie(char *fname) : root() {
		if (!file_exists(fname))
			throw std::invalid_argument(std::string("no such file: ").append(fname));

		std::ifstream ifs(fname);  // open input file stream
		if (!ifs.is_open())
			throw std::runtime_error(std::string("failed to open file: ").append(fname));

		// TODO <POS lookups> is this where to do POS lookups?

		// get bytes from file or STDIN, then scan/lookup token positions in the trie
		for (std::string tok; std::getline(ifs, tok); this->add(tok));
	}

	// add a node for each byte in the given token
	// the end of the token will be represented by an empty node and a terminal flag
	void add(const std::string& tok, size_t offset = 0) {
		// current node being added to
		node *cur = &root;
		for (char c : tok) {
			auto b = (unsigned char)c;

			if (!cur->data[b]) // not exists, so create
				cur->data[b] = new node();

			// point to next node down the trie
			cur = cur->data[b];
		}
		cur->term = true;  // mark end of the token with a term flag
		cur->val.add_offset(offset);
	}

	// TODO prints to the trie to the output stream (defalut STDOUT).
	// the output bytes should match exactly the normalized input stream bytes (TODO: normalize input bytes)
	void print_trie(std::ostream& out, TAGL::driver *drv = nullptr) const {
		/* Collect all terminal nodes, then emit in input-stream order (by first offset).
		   Traversal does not stop at terminal nodes so that tokens which are prefixes
		   of longer tokens are not shadowed (e.g. "any" does not block "anything"). */
		struct entry_t { std::string tok; const trie_value *val; };
		std::vector<entry_t> entries;

		std::function<void(const node*, std::string, char)> f_traverse;
		f_traverse = [&f_traverse, &entries](const node* nd, std::string s, char c) {
			if (c) s.push_back(c);
			if (nd->term)
				entries.push_back({s, &nd->val});
			for (int i = 0; i < 256; i++) {
				if (nd->data[i])
					f_traverse(nd->data[i], s, (char)i);
			}
		};
		f_traverse(&root, std::string(), '\0');

		std::sort(entries.begin(), entries.end(), [](const entry_t& a, const entry_t& b) {
			return a.val->offsets[0] < b.val->offsets[0];
		});

		for (const auto& e : entries) {
			out << e.tok;
			for (size_t i = 0; i < e.val->offset_count; ++i)
				out << (i == 0 ? "\t" : " ") << e.val->offsets[i];
			if (drv) {
				auto tpos_str = TAGL::token_str(drv->lookup_pos(e.tok));
				out << "\t" << tpos_str;
			}
			out << '\n';
		}
	}

	// called when a match occurs
	// parameters: <source filename>, <offset>, <matched token>
	typedef std::function<void(const std::string&, size_t, const std::string&)> match_function_t;

	// searches the mapped data for token targets and calls the match function for each match
	void matches(const mmap_t& mapped, const match_function_t& f_match) const {
		// for each byte in mapped data
		for (size_t i=0; i<mapped.size; i++) {
			// a match starts by comparing the root node of the trie and traversing downwards
			const node *cur = &root;
			// for each byte in mapped data
			// match a node until a terminal node is encountered
			for (size_t j=i; j<mapped.size; j++) {
				auto b = (unsigned char)mapped.data[j];
				if (!cur->data[b]) // not a match
					break;  // next i

				// at this point the input byte matches the current trie node,
				// we either have a match, or traverse to the next node

				// terminal node, we have a match
				if (cur->data[b]->term) {
					// call the match function, passing the filename, offset, and token
					f_match(
						mapped.fname,
						i,
						std::string(&mapped.data[i], (j - i + 1))
					);
					break;  // next i
				}

				// traverse to next trie node
				cur = cur->data[b];
			}  // next j
		}
	}
};

void tagr_tokenizer::print_trie(std::ostream& out) const {
	if (_trie)
		_trie->print_trie(out, _driver);
}

tagr_tokenizer::~tagr_tokenizer() = default;

void tagr_tokenizer::emit(const std::string& tok, size_t offset) {
	int token = _driver->lookup_pos(tok);
	const char *name = TAGL::token_str(token);

	_trie->add(tok, offset);

	// Emit the observed token as a token-value and token-type TSV line.
	(*_out) << tok << '\t' << name << '\n';
}

void tagr_tokenizer::scan(const unsigned char *data, size_t len) {
	if (!_trie)
		_trie = std::make_unique<trie>();

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


tagr_args::tagr_args() : cmd_args() {
	_cmds["--print-events"] = {
		[this](char *) { opt_print_events = true; },
		false
	};
}

void tagr_args::parse(int argc, char **argv) {
	// pre-filter argv: pull out positional (non-flag) args as scan_fnames,
	// pass remaining flags and their values to cmd_args::parse()
	std::vector<char*> filtered;
	filtered.push_back(argv[0]);
	for (int i = 1; i < argc; ++i) {
		auto it = _cmds.find(std::string(argv[i]));
		if (it != _cmds.end()) {
			filtered.push_back(argv[i]);
			if (it->second.has_arg && ++i < argc)
				filtered.push_back(argv[i]);  // flag value
		} else if (argv[i][0] == '-') {
			filtered.push_back(argv[i]);  // unknown flag: let cmd_args error
		} else {
			scan_fnames.push_back(argv[i]);  // positional: file to scan
		}
	}
	cmd_args::parse(filtered.size(), filtered.data());
}

tagr::tagr(tagdb_type *tdb, bool opt_print_events) :
	tagsh(tdb),
	_tokenizer(&_driver, std::cerr),
	_opt_print_events{opt_print_events}
{}

tagd::code tagr::scan_fd(int fd) {
	struct evbuffer *input = evbuffer_new();
	if (input == nullptr) {
		std::cerr << "evbuffer_new failed" << std::endl;
		return tagd::TAGD_ERR;
	}

	int nread;
	// read raw bytes from fd into the libevent buffer until EOF
	while ((nread = evbuffer_read(input, fd, -1)) > 0) {}

	if (nread < 0) {
		evbuffer_free(input);
		std::cerr << "evbuffer_read failed: " << std::strerror(errno) << std::endl;
		return tagd::TAGD_ERR;
	}

	// Tokenize the buffered bytes and log the emitted token stream.
	size_t len = evbuffer_get_length(input);
	const unsigned char *data = evbuffer_pullup(input, len);
	_tokenizer.scan(data, len);

	auto rc = tagd::TAGD_OK;
	evbuffer_free(input);
	return rc;
}

tagd::code tagr::scan_fname(const std::string& fname) {
	int fd = open(fname.c_str(), O_RDONLY);
	if (fd < 0) {
		std::cerr << "failed to open file: " << fname << std::endl;
		return tagd::TAGD_ERR;
	}

	auto rc = this->scan_fd(fd);
	close(fd);
	return rc;
}

tagd::code tagr::scan_stdin() {
	return this->scan_fd(STDIN_FILENO);
}
