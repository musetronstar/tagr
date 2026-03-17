#include <iostream>
#include <cerrno>
#include <fstream>
#include <stdexcept>   // logic_error, invalid_argument, runtime_error exceptions
#include <cstring>     // basename
#include <fcntl.h>     // open
#include <unistd.h>    // close
#include <sys/stat.h>  // stat
#include <sys/mman.h>  // mmap, munmap
#include <functional>  // std::function
#include <event2/buffer.h>
#include "tagl.h"
#include "tagd/codes.h"
#include "tagsh.h"

/*\
|*| Parses an input file and print an ngram frequency table
|*| 	in the form: ngram <tab> freqency
|*|
|*| ngrams are stored in a trie
\*/

// TODO
// add frequency counts to trie
// add a contained_in vector of ngram pointers where this ngram is a member

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

// value stored at a terminal trie node
// freq now - later: tagd_pos, NLP part-of-speech, etc.
struct trie_value {
	size_t freq;  // number of times this token was seen in the input
	trie_value() : freq{0} {}
};

// forward declare because nodes refer to nodes
struct node;

// represents a trie node for the allowed bases at a position in the sequence
struct node {
	// array of node pointers, indexed by byte value
	// TODO change to a std::string of bytes of an ngram
	node* data[256];

	// terminal node marks the end of a target
	// since this assignment does not deal with target sequences that are prefixes of other sequences,
	// the trie could have been implemented without this flag by checking a node for empty data array.
	// However, this flag gives a significant runtime performance boost.
	bool term;

	// remove term use n == 0 for empty node
	// TODO (the n in ngram)
	// size_t n;

	trie_value val;  // data at this node (set when term == true)

	node() :
		// C++11 value initialization of pointer array defaults to nullptr
		data{},
		term{false}
	{}

	// delete all allocated nodes cascading downwards
	~node() {
		for (int i=0; i<256; i++) {
			if (data[i])
				delete data[i];
		}
	}
};

// holds a trie structure of ngrams
struct trie {
	node root;  // root node of the trie

	trie() = delete;  // no default constructor

	// construct trie given filename of sequences
	// throws invalid_argument exception for errors caused by filename argument, otherwise runtime_error
	trie(char *fname) : root() {
		if (!file_exists(fname))
			throw std::invalid_argument(std::string("no such file: ").append(fname));

		std::ifstream ifs(fname);  // open input file stream
		if (!ifs.is_open())
			throw std::runtime_error(std::string("failed to open file: ").append(fname));

		// get sequences from targets file and add to the trie
		// TODO tokensize the input and adding each ngram from 1 to n for each token of input
		for (std::string seq; std::getline(ifs, seq); this->add(seq));
	}

	// add a node for each byte in the given sequence
	// the end of the string will be represented by an empty node and a terminal flag
	void add(const std::string& seq) {
		// current node being added to
		node *cur = &root;
		for (char c : seq) {
			auto b = (unsigned char)c;

			if (!cur->data[b]) // not exists, so create
				cur->data[b] = new node();

			// point to next node down the trie
			cur = cur->data[b];
		}
		cur->term = true;  // mark end of the sequence with a term flag
	}

	// prints the trie in same format as the input targets file - ASCII text, on sequence per line
	void print_targets(TAGL::driver *drv = nullptr) const {
		// recursive function that traverses the trie
		// note the sequence prefix of each node is passed by copy (no reference)
		// this might be expensive, but I didn't see an easy way around it
		std::function<void(const node*, std::string, char)> f_traverse;

		// traverse the trie, recursively passing the current sequence prefix plus the next
		// char to append until a terminal node is encountered
		f_traverse = [&f_traverse, drv](const node* nd, std::string s, char c) {
			if (c) s.push_back(c);
			if (nd->term) {
				if (drv) {
					// TODO why is this code not being executed?
					auto tpos_str = TAGL::token_str(drv->lookup_pos(s));
					std::cout << s << "\t" << tpos_str << std::endl;
				} else {
					std::cout << s << std::endl;
				}
				return;
			}
			for (int i=0; i<256; i++) {
				if (nd->data[i])
					f_traverse(nd->data[i], s, (char)i);
			}
		};

		// start traversing at the root
		f_traverse(&root, std::string(), '\0');
	}

	// called when a match occurs
	// parameters: <source filename>, <offset>, <matched sequence>
	typedef std::function<void(const std::string&, size_t, const std::string&)> match_function_t;

	// searches the mapped data for sequence targets and calls the match function for each match
	void matches(const mmap_t& mapped, const match_function_t& f_match) const {
		// for each byte in mapped source chromosome file
		for (size_t i=0; i<mapped.size; i++) {
			// a match starts by comparing the root node of the trie and traversing downwards
			const node *cur = &root;
			// for each byte in mapped source chromosome file,
			// match a node until a terminal node is encountered
			for (size_t j=i; j<mapped.size; j++) {
				auto b = (unsigned char)mapped.data[j];
				if (!cur->data[b]) // not a match
					break;  // next i

				// at this point the input byte matches the current trie node,
				// we either have a match, or traverse to the next node

				// terminal node, we have a match
				if (cur->data[b]->term) {
					// call the match function, passing the filename, offset, and sequence
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


// interates over each byte of the mapped data and outputs ngram sequences
void ngrams(const mmap_t& mapped) {
	// for each byte in mapped source chromosome file
	for (size_t i=0; i<mapped.size; i++) {
		for (size_t j=i; (j-i)<81 && j<mapped.size; j++) {
			std::cout << std::string(&mapped.data[i], (j - i + 1));
		}
		std::cout << std::endl;
	}
}

// tagr argument parser - extends cmd_args to handle positional scan file arguments
class tagr_args : public cmd_args {
	public:
		std::vector<std::string> scan_fnames;

		void parse(int argc, char **argv) {
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
};

// tagr - inherits tagsh for tagdb/driver/session setup
class tagr : public tagsh {
	public:
		tagr(tagdb_type *tdb) : tagsh(tdb) {}

		tagd::code scan_fd(int fd) {
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

			auto rc = _driver.execute(input);
			evbuffer_free(input);
			return rc;
		}

		tagd::code scan_fname(const std::string& fname) {
			int fd = open(fname.c_str(), O_RDONLY);
			if (fd < 0) {
				std::cerr << "failed to open file: " << fname << std::endl;
				return tagd::TAGD_ERR;
			}

			auto rc = this->scan_fd(fd);
			close(fd);
			return rc;
		}

		tagd::code scan_stdin() {
			return this->scan_fd(STDIN_FILENO);
		}
};

int main(int argc, char **argv) {
	tagr_args args;
	args.parse(argc, argv);

	if (args.has_errors()) {
		args.print_errors();
		return args.code();
	}

	tagdb::sqlite tdb;
	if (tdb.init(args.db_fname) != tagd::TAGD_OK) {
		tdb.print_errors();
		return tdb.code();
	}

	tagr t(&tdb);

	// load tagspace first without TAGL trace noise from the bootstrap file(s)
	bool opt_trace = args.opt_trace;
	args.opt_trace = false;
	if (args.interpret(t) != 0)
		return 1;
	if (opt_trace)
		TAGL_SET_TRACE_ON();

	try {
		tagd::code rc;
		if (args.scan_fnames.empty()) {
			rc = t.scan_stdin();
		} else {
			rc = tagd::TAGD_OK;
			for (auto& f : args.scan_fnames) {
				rc = t.scan_fname(f);
				if (rc != tagd::TAGD_OK)
					break;
			}
		}
		if (rc != tagd::TAGD_OK)
			return 1;
	} catch (const std::exception& e) {
		std::cerr << e.what() << std::endl;
		return 1;
	}

	return 0;  // ok
}
