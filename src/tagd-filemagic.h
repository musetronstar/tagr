#ifndef TAGD_FILEMAGIC_H
#define TAGD_FILEMAGIC_H

#include <stdbool.h>
#include <stddef.h>

struct evbuffer;

/* Stream identification result. */
struct magic_result {
	char *mime_type;
	char *charset;
	char *description;
	size_t bytes_examined;
	bool identity_known;
};

/* Release strings owned by result. */
void free_magic_result(struct magic_result *result);

/* Classify bytes read into buffer from fd. */
int magic_stream(struct evbuffer *buffer, int fd, struct magic_result *result,
	const char **error_reason);

/* Open path or return STDIN for "-". */
int open_input(const char *path);

#endif
