from kuristo.ui import truncate_or_pad


def test_truncate_or_pad_shorter():
    # Length of "hello" is 5. Max length is 8. Should be right-padded to 8.
    assert truncate_or_pad("hello", 8) == "hello   "
    assert len(truncate_or_pad("hello", 8)) == 8


def test_truncate_or_pad_equal():
    # Length of "hello" is 5. Max length is 5. Should be unchanged.
    assert truncate_or_pad("hello", 5) == "hello"
    assert len(truncate_or_pad("hello", 5)) == 5


def test_truncate_or_pad_longer():
    # Length of "hello world" is 11. Max length is 8.
    # It should truncate to 5 characters and append "...", total length 8.
    assert truncate_or_pad("hello world", 8) == "hello..."
    assert len(truncate_or_pad("hello world", 8)) == 8


def test_truncate_or_pad_boundary():
    # Max length of 2 (less than 3)
    assert truncate_or_pad("hello", 2) == "he"
    assert len(truncate_or_pad("hello", 2)) == 2

    # Max length of 0
    assert truncate_or_pad("hello", 0) == ""
    assert len(truncate_or_pad("hello", 0)) == 0
