#include <cxxtest/TestSuite.h>
#include <sstream>

#include "tagdb.h"
#include "tagr.h"

typedef tagdb::flags_t tdb_flags_t;
typedef tagdb::session tdb_session_t;

class tagdb_tester : public tagdb::tagdb {
	typedef std::map<tagd::id_type, tagd::abstract_tag> tag_map;
	tag_map _db;

	void put_test_tag(
		const tagd::id_type& id,
		const tagd::id_type& sub,
		tagd::part_of_speech pos)
	{
		tagd::abstract_tag t(id, sub, pos);
		_db[t.id()] = t;
	}

	public:
		tagdb_tester() {
			put_test_tag(HARD_TAG_ENTITY, HARD_TAG_ENTITY, tagd::POS_TAG);
			put_test_tag(HARD_TAG_SUB, HARD_TAG_ENTITY, tagd::POS_SUB_RELATOR);
			put_test_tag("one", HARD_TAG_ENTITY, tagd::POS_TAG);
			put_test_tag("any", HARD_TAG_ENTITY, tagd::POS_TAG);
			put_test_tag("of", HARD_TAG_ENTITY, tagd::POS_SUB_RELATOR);
			this->code(tagd::TAGD_OK);
		}

		tagd::part_of_speech pos(const tagd::id_type& id, tdb_session_t * = nullptr, tdb_flags_t = 0) override {
			auto it = _db.find(id);
			if (it == _db.end())
				return tagd::POS_UNKNOWN;

			return it->second.pos();
		}

		tagd::code get(tagd::abstract_tag& t, const tagd::id_type& id, tdb_session_t * = nullptr, tdb_flags_t = 0) override {
			auto it = _db.find(id);
			if (it == _db.end())
				return this->ferror(tagd::TS_NOT_FOUND, "unknown tag: %s", id.c_str());

			t = it->second;
			return this->code(tagd::TAGD_OK);
		}

		tagd::code put(const tagd::abstract_tag& t, tdb_session_t * = nullptr, tdb_flags_t = 0) override {
			_db[t.id()] = t;
			return this->code(tagd::TAGD_OK);
		}

		tagd::code del(const tagd::abstract_tag& t, tdb_session_t * = nullptr, tdb_flags_t = 0) override {
			_db.erase(t.id());
			return this->code(tagd::TAGD_OK);
		}

		tagd::code query(tagd::tag_set&, const tagd::interrogator&, tdb_session_t * = nullptr, tdb_flags_t = 0) override {
			return tagd::TS_NOT_IMPLEMENTED;
		}

		bool exists(const tagd::id_type& id, tdb_flags_t = 0) override {
			return _db.find(id) != _db.end();
		}

		tagd::code dump(std::ostream& = std::cout) override {
			return tagd::TS_NOT_IMPLEMENTED;
		}
};

class Tester : public CxxTest::TestSuite {
	tagdb_tester *_tdb;
	TAGL::driver *_driver;

		std::string scan(const std::string& input) {
			std::ostringstream out;
			tagr_tokenizer tok(_driver, out);
			tok.scan((const unsigned char *) input.data(), input.size());
			return out.str();
		}

		std::string scan_and_print_trie(const std::string& input) {
			std::ostringstream out;
			tagr_tokenizer tok(_driver, out);
			tok.scan((const unsigned char *) input.data(), input.size());

			std::ostringstream trie_out;
			tok.print_trie(trie_out);
			return trie_out.str();
		}

	public:
		void setUp() {
			_tdb = new tagdb_tester();
			_driver = new TAGL::driver(_tdb);
			_driver->own_session(_tdb->new_session());
		}

		void tearDown() {
			delete _driver;
			delete _tdb;
		}

		void test_unknown_token_from_stdin() {
			TS_ASSERT_EQUALS(scan("dog\n"), "dog\tTOK_UNKNOWN\n");
		}

		void test_known_tokens() {
			TS_ASSERT_EQUALS(
				scan("one any of\n"),
				"one\tTOK_TAG\n"
				"any\tTOK_TAG\n"
				"of\tTOK_SUB_RELATOR\n"
			);
		}

		void test_trie_value_stores_offsets() {
			trie_value v;

			v.add_offset(0);
			v.add_offset(4);
			v.add_offset(8);

			TS_ASSERT_EQUALS(v.offset_count, 3U);
			TS_ASSERT_EQUALS(v.offsets[0], 0U);
			TS_ASSERT_EQUALS(v.offsets[1], 4U);
			TS_ASSERT_EQUALS(v.offsets[2], 8U);
		}

		void test_print_trie_shows_repeated_token_offsets() {
			TS_ASSERT_EQUALS(
				scan_and_print_trie("one any any of\n"),
				                    "one any any of\n"
			);
		}

		void test_print_trie_keeps_prefix_and_longer_token() {
			_tdb->put(tagd::abstract_tag("a", HARD_TAG_ENTITY, tagd::POS_TAG));
			_tdb->put(tagd::abstract_tag("an", HARD_TAG_ENTITY, tagd::POS_TAG));

			TS_ASSERT_EQUALS(
				scan_and_print_trie("a an\n"),
				                    "a an\n"
			);
		}
};
