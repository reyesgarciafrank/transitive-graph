from tbcl.log_parser import clean_log_bytes, parse_log_text


def test_clean_log_bytes_removes_nulls():
    text = clean_log_bytes(b"ab\x00cd")
    assert text == "abcd"


def test_parse_log_text_extracts_failures_and_summary():
    raw = """[ERROR] com.example.FooTest.testBar:42 fail\n[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0\nat org.lib.X.y(X.java:1)"""
    parsed = parse_log_text(raw)
    assert len(parsed["failing_tests"]) == 1
    assert parsed["failing_tests"][0].full_name == "com.example.FooTest#testBar"
    assert parsed["surefire"].tests_run == 5
    assert parsed["stack_frames"][0]["class"] == "org.lib.X"
