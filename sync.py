"""
Aim: Replicate a directory
Rules:
    1 - if a file exists in the source dir and not in the destination dir, copy the file over
    2 - if the file exists in the source dir, but has a different name than in the destinations dir, rename the destination file to match
    3 - if the file exists in the destination dir but not in the source dir, remove it

1 & 2 - simply compare two lists of paths
3 - need to use hash to compare files
"""

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


def sync(source, dest):
    """Function for replicating source directory in a destination directory."""

    # walk the source dir and build a dict of filename: hash of file
    source_hashes = {}
    for folder, _, files in os.walk(source):
        for fn in files:
            source_hashes[hash_file(Path(folder) / fn)] = fn  # Path("hello") / "world" == Path("hello/world")

    seen = set()

    for folder, _, files in os.walk(dest):
        for fn in files:
            dest_path = Path(folder) / fn
            dest_hash = hash_file(dest_path)
            seen.add(dest_hash)

            if dest_hash not in source_hashes:  # file in dest but not source: delete
                dest_path.remove()
            elif dest_hash in source_hashes and fn != source_hashes[dest_hash]:  # same file different name: rename file
                shutil.move(dest_path, Path(folder) / source_hashes[dest_hash])

    for src_hash, fn in source_hashes.items():
        if src_hash not in seen:  # file in source not found in dest: copy to dest
            shutil.copy(Path(source) / fn, Path(dest) / fn)
