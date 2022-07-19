from pathlib import Path

import pytest

from sync import determine_actions, sync


def test_when_a_file_exists_in_src_but_not_dest(tmp_path):
    src_hashes = {"hash1": "fn1"}
    dst_hashes = {}
    actions = determine_actions(src_hashes, dst_hashes, Path("/src"), Path("/dst"))

    assert list(actions) == [("copy", Path("/src/fn1"), Path("/dst/fn1"))]

def test_when_a_file_has_been_renamed_in_the_source(tmp_path):
    src_hashes = {"hash1": "fn1"}
    dst_hashes = {"hash1": "fn2"}
    actions = determine_actions(src_hashes, dst_hashes, Path("/src"), Path("/dst"))

    assert list(actions) == [("move", Path("/dst/fn2"), Path("/dst/fn1"))]