import pytest

from sync import sync


def test_when_a_file_exists_in_src_but_not_dest(tmp_path):
    """Test that a file is copied from src to dest when the file does not exist in dest"""

    # create tmp dirs
    source = (tmp_path / "source")
    source.mkdir()
    dest = (tmp_path / "dest")
    dest.mkdir()

    # write to tml src dir
    content = "I am a very useful file"
    (source / "my-file").write_text(content)

    sync(source, dest)

    expected_path = dest / "my-file"
    assert expected_path.exists()
    assert expected_path.read_text() == content

def test_when_a_file_has_been_renamed_in_the_source(tmp_path):
    source = (tmp_path / "source")
    source.mkdir()
    dest = (tmp_path / "dest")
    dest.mkdir()

    content = "I am a file that was renamed"
    source_path = source / "source-filname"
    source_path.write_content(content)

    old_dest_path = dest / "dest-filename"
    expected_dest_path = dest / "source-filename"
    old_dest_path.write_content(content)

    sync(source, dest)

    assert old_dest_path.exists() is False
    assert expected_dest_path.read_text() == content