#!/usr/bin/env python3
"""Emit the 25 November 2026 news front page as /output/entry.png.

The front page itself is drawn once and bundled with this repository as
frontpage.png: a crimson-masthead broadsheet summing up Wednesday
25 November 2026 in 38 stories — one lead story with a drawn scene, six
illustrated featured stories, a 28-item list with sources, a numbers
strip, region counts and a DATE CHECK footer. This program only verifies
that bundled image (a 1024x1024 PNG under the 1 MiB cap) and copies it
byte-for-byte to the output path, so repeated runs are identical and no
network is touched. Point ENTRY_OUTPUT elsewhere to test locally.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.join(HERE, "frontpage.png")
TARGET = os.environ.get("ENTRY_OUTPUT", "/output/entry.png")
SIZE_LIMIT = 1_048_576
EXPECTED = (1024, 1024)


def load_and_check(path):
    """Open the bundled page and refuse it unless it is a 1024x1024
    PNG inside the byte cap; returns its size in bytes."""
    from PIL import Image

    size = os.path.getsize(path)
    if size > SIZE_LIMIT:
        sys.exit(f"front page is {size} bytes, over the {SIZE_LIMIT} cap")
    with Image.open(path) as im:
        if im.format != "PNG":
            sys.exit(f"front page is {im.format}, expected PNG")
        if im.size != EXPECTED:
            sys.exit(f"front page is {im.size}, expected {EXPECTED}")
    return size


def emit():
    import hashlib

    os.makedirs(os.path.dirname(TARGET) or ".", exist_ok=True)
    load_and_check(BUNDLED)
    shutil.copyfile(BUNDLED, TARGET)
    load_and_check(TARGET)
    with open(BUNDLED, "rb") as f:
        want = hashlib.sha256(f.read()).hexdigest()
    with open(TARGET, "rb") as f:
        got = hashlib.sha256(f.read()).hexdigest()
    if want != got:
        sys.exit("output bytes differ from the bundled front page")


if __name__ == "__main__":
    emit()
