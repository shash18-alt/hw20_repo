#!/usr/bin/env python3

import os
import zlib
from collections import deque

GIT_DIR = ".git"


def read_object(sha):
    """Read and decompress a git object"""
    path = os.path.join(GIT_DIR, "objects", sha[:2], sha[2:])

    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        compressed = f.read()

    data = zlib.decompress(compressed)

    # split header: "type size\0content"
    null_index = data.find(b"\x00")
    header = data[:null_index]
    content = data[null_index + 1:]

    obj_type = header.decode().split()[0]
    return obj_type, content.decode(errors="ignore")


def find_head_commit():
    """Get HEAD commit hash"""
    ref_path = os.path.join(GIT_DIR, "HEAD")

    with open(ref_path, "r") as f:
        ref = f.read().strip()

    # symbolic ref
    if ref.startswith("ref:"):
        ref_file = os.path.join(GIT_DIR, ref.split(" ")[1])
        with open(ref_file) as f:
            return f.read().strip()

    return ref


def parse_commit(content):
    """Parse commit object"""
    lines = content.split("\n")

    parents = []
    message_lines = []
    author = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("parent "):
            parents.append(line.split()[1])

        elif line.startswith("author "):
            author = line

        elif line == "":
            message_lines = lines[i + 1:]
            break

        i += 1

    message = message_lines[0] if message_lines else ""

    return parents, author, message


def mini_git_log():
    head = find_head_commit()

    visited = set()
    queue = deque([head])

    commits = []

    while queue:
        commit_sha = queue.popleft()
        if not commit_sha or commit_sha in visited:
            continue

        visited.add(commit_sha)

        obj = read_object(commit_sha)
        if not obj:
            continue

        obj_type, content = obj
        if obj_type != "commit":
            continue

        parents, author, message = parse_commit(content)

        commits.append((commit_sha, message))

        for p in parents:
            queue.append(p)

    # print like git log --oneline
    for sha, msg in commits:
        print(f"{sha[:7]} {msg}")


if __name__ == "__main__":
    mini_git_log()
