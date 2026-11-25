"""THE WORLD — Wednesday, 25 November 2026: the day in 38 stories.

This is the entrypoint for the make.fun news-image-20261125 bounty.
The front page itself is the bundled file ``frontpage.png`` in this same
directory (a 1024x1024 broadsheet: four oil tankers hit mines in the
Strait of Hormuz leads, with 34 more stories, a numbers strip and a
region breakdown). The program's only job is to make sure that image
is a whole, valid PNG inside the competition's limits, and then to
write it out as the entry image.

No network, no third-party packages: everything here is the standard
library. The output goes to ``$MAKEFUN_OUTPUT_DIR/entry.png`` when
that variable is set (the grader sets it), otherwise to
``/output/entry.png``. Running it twice produces identical bytes.
"""

import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1024 * 1024          # the competition's 1 MiB cap
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def fail(message):
    """Print a plain error to stderr and stop with a non-zero exit."""
    print("main.py: error: " + message, file=sys.stderr)
    sys.exit(1)


def check_png(raw):
    """Walk the PNG and confirm it is whole and within the limits.

    Returns the (width, height) from the IHDR chunk. Raises SystemExit
    (via fail) on the first problem found, naming what went wrong.
    """
    if len(raw) > MAX_BYTES:
        fail("frontpage.png is %d bytes, over the 1 MiB limit" % len(raw))
    if len(raw) < 8 or raw[:8] != PNG_MAGIC:
        fail("frontpage.png does not start with the PNG signature")

    pos = 8
    width = height = None
    saw_image_data = False
    saw_end = False

    while pos < len(raw):
        if pos + 8 > len(raw):
            fail("frontpage.png ends in the middle of a chunk header")
        chunk_len = struct.unpack(">I", raw[pos:pos + 4])[0]
        chunk_type = raw[pos + 4:pos + 8]
        data_start = pos + 8
        data_end = data_start + chunk_len
        if data_end + 4 > len(raw):
            fail("chunk %r claims %d bytes but the file ends first"
                 % (chunk_type.decode("latin-1"), chunk_len))

        chunk_data = raw[data_start:data_end]
        stored_crc = struct.unpack(">I", raw[data_end:data_end + 4])[0]
        real_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if stored_crc != real_crc:
            fail("chunk %r has a bad checksum"
                 % chunk_type.decode("latin-1"))

        if chunk_type == b"IHDR":
            if chunk_len != 13:
                fail("IHDR chunk is %d bytes, expected 13" % chunk_len)
            width, height = struct.unpack(">II", chunk_data[:8])
        elif chunk_type == b"IDAT":
            saw_image_data = True
        elif chunk_type == b"IEND":
            saw_end = True
            pos = data_end + 4
            break

        pos = data_end + 4

    if width is None:
        fail("frontpage.png has no IHDR chunk")
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        fail("frontpage.png is %dx%d, expected %dx%d"
             % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT))
    if not saw_image_data:
        fail("frontpage.png has no image data (no IDAT chunk)")
    if not saw_end:
        fail("frontpage.png has no IEND chunk")
    if pos != len(raw):
        fail("frontpage.png has %d trailing bytes after IEND"
             % (len(raw) - pos))

    return width, height


def main():
    here = Path(__file__).resolve().parent
    source = here / "frontpage.png"
    if not source.is_file():
        fail("bundled image not found: %s" % source)

    raw = source.read_bytes()
    width, height = check_png(raw)
    digest = hashlib.sha256(raw).hexdigest()

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    target = out_dir / "entry.png"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    except OSError as exc:
        fail("could not write %s: %s" % (target, exc))

    # Read the file back and confirm what landed on disk is exactly the
    # image we checked: a short write or a full disk must never silently
    # produce a corrupt entry, and the grader runs this twice and compares.
    written = target.read_bytes()
    if len(written) != len(raw):
        fail("written entry.png is %d bytes, expected %d"
             % (len(written), len(raw)))
    if hashlib.sha256(written).hexdigest() != digest:
        fail("written entry.png does not match frontpage.png")

    print("wrote %s (%dx%d, %d bytes, sha256 %s) — verified identical"
          % (target, width, height, len(raw), digest))


if __name__ == "__main__":
    main()
