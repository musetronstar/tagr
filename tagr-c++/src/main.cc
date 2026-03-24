#include <iostream>
#include <cstddef>
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
#include "tagr.h"

/*\
|*| Reads an input stream from STDIN and outputs TAGL
|*|
|*| tokens are stored in a trie
\*/

// TODO provide a concise comment for each non-trivial block/section of code
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

	tagr t(&tdb, args.opt_print_events);

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
