#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'cnheider'

def main():
    import imageio
    import streamserver


    reader = imageio.get_reader('<video0>')

    try:
        with streamserver.StreamServer(JPEG_quality=75, host='localhost', port=5000) as ss:
            for im in reader:
                ss.set_frame(im)
    except KeyboardInterrupt:
        pass



if __name__ == '__main__':
    main()
