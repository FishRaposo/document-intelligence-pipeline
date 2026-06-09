from doc_pipeline.cleaners import clean_extracted_text


class TestCleaners:
    def test_removes_extra_whitespace(self):
        result = clean_extracted_text("hello   world")
        assert result == "hello world"

    def test_normalizes_newlines(self):
        result = clean_extracted_text("line1\n\n\nline2")
        assert result == "line1 line2"

    def test_trims_edges(self):
        result = clean_extracted_text("  \n  text  \n  ")
        assert result == "text"

    def test_removes_control_chars(self):
        result = clean_extracted_text("hello\tworld")
        assert "\t" not in result
        assert "hello" in result

    def test_empty_string(self):
        result = clean_extracted_text("")
        assert result == ""

    def test_only_whitespace(self):
        result = clean_extracted_text("   \n\n  ")
        assert result == ""

    def test_preserves_single_spaces(self):
        result = clean_extracted_text("hello world")
        assert result == "hello world"
