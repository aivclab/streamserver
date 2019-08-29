#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'cnheider'


def main():
    import cv2
    import streamserver

    cap = cv2.VideoCapture(0)

    ret, _ = cap.read()
    assert ret == True

    with streamserver.StreamServer(JPEG_quality=75, host='localhost', port=5000) as ss:
        while cap.isOpened():
            ret, frame = cap.read()
            ss.set_frame(frame)
            wk = cv2.waitKey(20)
            if wk == ord('q'):
                break
    cap.release()


if __name__ == '__main__':
    main()
