#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = "Christian Heider Nielsen"


def main():
    import imageio
    from streamserver.server import StreamServer

    reader = imageio.get_reader("<video0>")

    try:
        with StreamServer(JPEG_quality=75, host="localhost", port=5000) as ss:
            for im in reader:
                ss.set_frame(im)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
