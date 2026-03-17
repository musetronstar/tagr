#include <errno.h>
#include <event2/buffer.h>
#include <fcntl.h>
#include <magic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "tagd-filemagic.h"

enum {
	READ_CHUNK_SIZE = 4096
};

static const size_t MAX_SNIFF_BYTES = 8650;

void free_magic_result(struct magic_result *result) {
	if (result == NULL)
		return;

	free(result->mime_type);
	free(result->charset);
	free(result->description);
	result->mime_type = NULL;
	result->charset = NULL;
	result->description = NULL;
	result->bytes_examined = 0;
	result->identity_known = false;
}

static char *xstrdup(const char *s) {
	size_t len;
	char *copy;

	if (s == NULL)
		return NULL;

	len = strlen(s);
	copy = malloc(len + 1);
	if (copy == NULL)
		return NULL;

	memcpy(copy, s, len + 1);
	return copy;
}

static int set_result_from_magic(struct magic_result *result, const char *description) {
	char *copy;
	char *sep;
	char *charset;
	char *mime_type_copy;
	char *charset_copy;
	char *description_copy;

	copy = xstrdup(description);
	if (copy == NULL)
		return -1;

	sep = strstr(copy, "; charset=");
	if (sep == NULL) {
		free(copy);
		errno = EINVAL;
		return -1;
	}

	*sep = '\0';
	charset = sep + strlen("; charset=");

	mime_type_copy = xstrdup(copy);
	charset_copy = xstrdup(charset);
	description_copy = xstrdup(description);
	free(copy);

	if (mime_type_copy == NULL || charset_copy == NULL || description_copy == NULL) {
		free(mime_type_copy);
		free(charset_copy);
		free(description_copy);
		return -1;
	}

	free(result->mime_type);
	free(result->charset);
	free(result->description);

	result->mime_type = mime_type_copy;
	result->charset = charset_copy;
	result->description = description_copy;

	return 0;
}

static bool magic_identity_known(const struct magic_result *result) {
	if (result->mime_type == NULL || result->charset == NULL)
		return false;

	if (strcmp(result->mime_type, "application/octet-stream") == 0)
		return false;

	if (strcmp(result->mime_type, "text/plain") == 0 &&
	    strcmp(result->charset, "binary") == 0)
		return false;

	return true;
}

static int classify_buffer(magic_t cookie, struct evbuffer *buffer, struct magic_result *result,
	const char **error_reason) {
	size_t length;
	unsigned char *data;
	const char *description;

	length = evbuffer_get_length(buffer);
	if (length == 0) {
		*error_reason = "empty input";
		errno = EINVAL;
		return -1;
	}

	data = evbuffer_pullup(buffer, -1);
	if (data == NULL) {
		*error_reason = "evbuffer_pullup failed";
		return -1;
	}

	description = magic_buffer(cookie, data, length);
	if (description == NULL) {
		*error_reason = magic_error(cookie);
		return -1;
	}

	if (set_result_from_magic(result, description) != 0) {
		*error_reason = "unable to parse libmagic MIME description";
		return -1;
	}

	result->bytes_examined = length;
	result->identity_known = magic_identity_known(result);
	return 0;
}

int magic_stream(struct evbuffer *buffer, int fd, struct magic_result *result,
	const char **error_reason) {
	magic_t cookie;
	ssize_t nread;

	cookie = magic_open(MAGIC_MIME);
	if (cookie == NULL) {
		*error_reason = "magic_open failed";
		return -1;
	}

	if (magic_load(cookie, NULL) != 0) {
		*error_reason = magic_error(cookie);
		magic_close(cookie);
		return -1;
	}

	for (;;) {
		nread = evbuffer_read(buffer, fd, READ_CHUNK_SIZE);
		if (nread < 0) {
			*error_reason = "read failed";
			magic_close(cookie);
			return -1;
		}

		if (evbuffer_get_length(buffer) > 0) {
			if (classify_buffer(cookie, buffer, result, error_reason) != 0) {
				magic_close(cookie);
				return -1;
			}

			if (result->identity_known)
				break;
		}

		if (nread == 0)
			break;

		if (evbuffer_get_length(buffer) >= MAX_SNIFF_BYTES)
			break;
	}

	magic_close(cookie);

	if (evbuffer_get_length(buffer) == 0) {
		*error_reason = "empty input";
		errno = EINVAL;
		return -1;
	}

	if (result->mime_type == NULL || result->charset == NULL) {
		*error_reason = "unable to identify stream";
		errno = EINVAL;
		return -1;
	}

	return 0;
}

int open_input(const char *path) {
	if (path == NULL || strcmp(path, "-") == 0)
		return STDIN_FILENO;

	return open(path, O_RDONLY);
}

#ifndef TAGD_FILEMAGIC_NO_MAIN
int main(int argc, char **argv) {
	const char *path;
	int fd;
	int exit_code;
	struct evbuffer *buffer;
	struct magic_result result;
	const char *error_reason;

	path = "-";
	if (argc > 2) {
		fprintf(stderr, "usage: %s [PATH|-]\n", argv[0]);
		return 2;
	}
	if (argc == 2)
		path = argv[1];

	fd = open_input(path);
	if (fd < 0) {
		fprintf(stderr, "%s: %s\n", path, strerror(errno));
		return 1;
	}

	buffer = evbuffer_new();
	if (buffer == NULL) {
		fprintf(stderr, "evbuffer_new: %s\n", strerror(errno));
		if (fd != STDIN_FILENO)
			close(fd);
		return 1;
	}

	memset(&result, 0, sizeof(result));
	error_reason = NULL;
	exit_code = magic_stream(buffer, fd, &result, &error_reason);
	if (exit_code != 0) {
		if (error_reason == NULL)
			error_reason = "unknown error";

		if (errno != 0)
			fprintf(stderr, "%s: %s\n", error_reason, strerror(errno));
		else
			fprintf(stderr, "%s\n", error_reason);
		exit_code = 1;
	} else {
		printf("%s: %s; charset=%s\n", path, result.mime_type, result.charset);
	}

	free_magic_result(&result);
	evbuffer_free(buffer);
	if (fd != STDIN_FILENO)
		close(fd);

	return exit_code;
}
#endif
