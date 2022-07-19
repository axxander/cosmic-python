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

from fileinput import filename
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


def read_paths_and_hashes(root: str) -> str:
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    
    return hashes

def determine_actions(src_hashes, dst_hashes, src_folder, dst_folder):
    for sha, fn in src_hashes.items():
        # file missing in destination: copy
        if sha not in dst_hashes:  # file in src but not in dest
            sourcepath = Path(src_folder) / fn
            destpath = Path(dst_folder) / fn
            yield "copy", sourcepath, destpath
        
        # file in destination, but named something different from source: rename
        elif dst_hashes[sha] != fn:  # same file in src and dest but named differently in dest
            oldestpath = Path(dst_folder) / dst_hashes[sha]  # current filename
            newestpath = Path(dst_folder) / fn  # new filename
            yield "move", oldestpath, newestpath

    # file in destination but no in source: delete
    for sha, filename in dst_hashes.items():
        if sha not in src_hashes:  # file in dest does not exist in source and is NOT a same file with diff name
            yield "delete", dst_folder / filename

def sync(source, dest):
    """Function for replicating source directory in a destination directory."""

    # imperative shell step 1, gather inputs
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    # step 2: call functional core: we can test this code independently of a file system!
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step 3, apply outputs
    for action, *paths in actions:
        if action == "copy":
            shutil.copyfile(*paths)
        if action == "move":
            shutil.move(*paths)
        if action == "delete":
            os.remove(paths[0])
