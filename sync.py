"""
Aim: Replicate a directory
Rules:
    1 - if a file exists in the source dir and not in the destination dir, copy the file over
    2 - if the file exists in the source dir, but has a different name than in the destinations dir, rename the destination file to match
    3 - if the file exists in the destination dir but not in the source dir, remove it

1 & 2 - simply compare two lists of paths
3 - need to use hash to compare files

New method
- Create a dict of hashes for both the source and destinations
- Separate out the what we do to how we do it: when comparing we should produce commands like ("ACTION", "source", "dest") where ACTION could be copy or delete etc

This now lets us test the actual core, not the code that writes the files. We can write test cases for given these source and dest hash dicts, what are the commands?
Core code had no dependencies on external state.
Then we can use integration tests for the actual end-to-end flow, i.e. check things are actually written/deleted to a dir.
"""

from typing import Callable, Protocol
import hashlib
import os
import shutil
from pathlib import Path


BLOCKSIZE = 65536


def hash_file(path: Path) -> str:
    """Function for hashing a file."""
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def reader(root: str) -> str:
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    
    return hashes


class FileSystem(Protocol):
    def copy(self, src, dest) -> None: ...
    def move(self, src, dest) -> None: ...
    def delete(self, src, dest) -> None: ...


def sync(reader: Callable, filesystem: FileSystem, source_root: Path, dest_root: Path):
    """Function for replicating source directory in a destination directory.
    
    Function now explicitly depends on reader and filesystem to make edge-to-edge testing easier (dependency injection/IoC)
    reader: produces file dictionary
    filesystem: for applying changes
    """

    # str func required: may need refactoring
    source_hashes = reader(str(source_root))
    dest_hashes = reader(str(dest_root))

    # converting path to str: probably needs refactoring
    for sha, fn in source_hashes.items():
        if sha not in dest_hashes:  # file in source but not dest: copy
            sourcepath = source_root / fn
            destpath = dest_root / fn
            filesystem.copy(sourcepath, destpath)  # copy
        
        elif dest_hashes[sha] != fn:  # identical file is source and dest, but named diff in source: rename/move
            oldpath = dest_root / dest_hashes[sha]
            newpath = dest_root / fn
            filesystem.move(oldpath, newpath) # rename
    
    for sha, fn in dest_hashes.items():
        if sha not in source_hashes:  # file in dest but not source: delete
            filesystem.delete(dest_root / fn)
