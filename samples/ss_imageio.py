#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import suppress

from imageio.core import Format

__author__ = "Christian Heider Nielsen"
__doc__ = r"""Broken at the moment"""


def main():
    import imageio
    import streamserver

    reader: Format.Reader = imageio.get_reader("<video0>")

    with suppress(KeyboardInterrupt):
        with streamserver.StreamServer(
            JPEG_quality=75, host="localhost", port=5000
        ) as ss:
            for im in reader:
                ss.set_frame(im)

    reader.close()


if __name__ == "__main__":
    main()
