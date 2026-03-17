#include <assert.h>
#include <errno.h>
#include <event2/buffer.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "tagd-filemagic.h"

static int is_text_charset(const char *charset) {
	return strcmp(charset, "us-ascii") == 0 || strcmp(charset, "utf-8") == 0;
}

static void test_open_input_dash_returns_stdin(void) {
	assert(open_input("-") == STDIN_FILENO);
	assert(open_input(NULL) == STDIN_FILENO);
}

static void test_open_input_file_round_trip(void) {
	static const char path[] = "../corpus/open-input.txt";
	static const char data[] = "alpha\n";
	int fd;
	char buf[sizeof(data)] = {0};
	ssize_t nread;

	fd = open(path, O_CREAT | O_TRUNC | O_WRONLY, 0644);
	assert(fd >= 0);
	assert(write(fd, data, sizeof(data) - 1) == (ssize_t)(sizeof(data) - 1));
	close(fd);

	fd = open_input(path);
	assert(fd >= 0);
	nread = read(fd, buf, sizeof(buf) - 1);
	assert(nread == (ssize_t)(sizeof(data) - 1));
	assert(strcmp(buf, data) == 0);
	close(fd);

	assert(unlink(path) == 0);
}

static void test_open_input_missing_file_fails(void) {
	errno = 0;
	assert(open_input("../corpus/does-not-exist") == -1);
	assert(errno == ENOENT);
}

static void test_free_magic_result_clears_fields(void) {
	struct magic_result result;

	memset(&result, 0, sizeof(result));
	result.mime_type = strdup("text/plain");
	result.charset = strdup("utf-8");
	result.description = strdup("text/plain; charset=utf-8");
	assert(result.mime_type != NULL);
	assert(result.charset != NULL);
	assert(result.description != NULL);
	result.bytes_examined = 12;
	result.identity_known = true;

	free_magic_result(&result);

	assert(result.mime_type == NULL);
	assert(result.charset == NULL);
	assert(result.description == NULL);
	assert(result.bytes_examined == 0);
	assert(result.identity_known == false);
}

static void write_all(int fd, const void *buf, size_t len) {
	const unsigned char *p = buf;
	size_t total = 0;
	ssize_t nwritten;

	while (total < len) {
		nwritten = write(fd, p + total, len - total);
		assert(nwritten >= 0);
		total += (size_t)nwritten;
	}
}

static int classify_bytes(const void *buf, size_t len, struct magic_result *result,
	const char **error_reason) {
	int fds[2];
	struct evbuffer *buffer;
	int rc;

	assert(pipe(fds) == 0);
	if (len > 0)
		write_all(fds[1], buf, len);
	close(fds[1]);

	buffer = evbuffer_new();
	assert(buffer != NULL);

	memset(result, 0, sizeof(*result));
	*error_reason = NULL;
	rc = magic_stream(buffer, fds[0], result, error_reason);

	evbuffer_free(buffer);
	close(fds[0]);
	return rc;
}

static void test_magic_stream_empty_input_fails(void) {
	struct magic_result result;
	const char *error_reason;

	errno = 0;
	assert(classify_bytes("", 0, &result, &error_reason) == -1);
	assert(error_reason != NULL);
	assert(strcmp(error_reason, "empty input") == 0);
	assert(errno == EINVAL);
	free_magic_result(&result);
}

static void test_magic_stream_text_plain(void) {
	static const char data[] = "hello world\n";
	struct magic_result result;
	const char *error_reason;

	assert(classify_bytes(data, sizeof(data) - 1, &result, &error_reason) == 0);
	assert(error_reason == NULL);
	assert(result.mime_type != NULL);
	assert(result.charset != NULL);
	assert(result.description != NULL);
	assert(strcmp(result.mime_type, "text/plain") == 0);
	assert(is_text_charset(result.charset));
	assert(strncmp(result.description, "text/plain; charset=", 20) == 0);
	assert(result.bytes_examined == sizeof(data) - 1);
	assert(result.identity_known == true);
	free_magic_result(&result);
}

static void test_magic_stream_binary_fallback(void) {
	static const unsigned char data[] = {0x00, 0x01, 0x02, 0x03};
	struct magic_result result;
	const char *error_reason;

	assert(classify_bytes(data, sizeof(data), &result, &error_reason) == 0);
	assert(error_reason == NULL);
	assert(strcmp(result.mime_type, "application/octet-stream") == 0);
	assert(strcmp(result.charset, "binary") == 0);
	assert(strcmp(result.description, "application/octet-stream; charset=binary") == 0);
	assert(result.bytes_examined == sizeof(data));
	assert(result.identity_known == false);
	free_magic_result(&result);
}

int main(void) {
	test_open_input_dash_returns_stdin();
	test_open_input_file_round_trip();
	test_open_input_missing_file_fails();
	test_free_magic_result_clears_fields();
	test_magic_stream_empty_input_fails();
	test_magic_stream_text_plain();
	test_magic_stream_binary_fallback();
	puts("ok");
	return 0;
}
