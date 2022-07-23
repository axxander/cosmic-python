import pytest

from pathlib import Path

from sync import sync

class FakeFileSystem(list):
    def copy(self, src, dest):
        self.append(('COPY', src, dest))

    def move(self, src, dest):
        self.append(('MOVE', src, dest))

    def delete(self, src, dest):
        self.append(('DELETE', dest))


def test_when_a_file_exists_in_src_but_not_dest():
    source = {"hash1": "fn1"}
    dest = {}
    filesystem = FakeFileSystem()

    reader = {"/source": source, "/dest": dest}  # fake reader
    sync(reader.pop, filesystem, Path("/source"), Path("/dest"))  # reader.pop gets the corresponding hash dict

    assert filesystem == [("COPY", Path("/source/fn1"), Path("/dest/fn1"))]


def test_when_a_file_has_been_renamed_in_the_source():
    source = {"hash1": "fn1"}
    dest = {"hash1": "fn2"}
    filesystem = FakeFileSystem()

    reader = {"/source": source, "/dest": dest}  # fake reader
    sync(reader.pop, filesystem, Path("/source"), Path("/dest"))  # reader.pop gets the corresponding hash dict

    assert filesystem == [("MOVE", Path("/dest/fn2"), Path("/dest/fn1"))]
