#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "sorenrasmussenai"
__doc__ = r"""
           """

import contextlib
import io
import os
import random
import re
import socket
import threading
import time
import urllib.parse

import imageio
import numpy

try:
    import IPython.display

    __IPYTHON_DISPLAY__ = True
except:
    __IPYTHON_DISPLAY__ = False

__all__ = ["StreamServer"]


class StreamServer:
    def __init__(
        self,
        host=None,
        port=5000,
        next_free_port=True,
        nb_output=True,
        printaddr=True,
        secret=None,
        fmt="bgr",
        encoder="JPEG",
        JPEG_quality=75,
        PNG_compression=1,
    ):
        """

    :param host:
    :param port:
    :param next_free_port:
    :param nb_output:
    :param printaddr:
    :param secret:
    :param fmt:
    :param encoder:
    :param JPEG_quality:
    :param PNG_compression:
    """
        if host is None:
            self.host = "localhost"
        elif host == "GLOBAL":
            self.host = self.__get_global_ip()
        else:
            self.host = host
        if secret is None:
            self.secret = self.__random_str__(12)
        else:
            self.secret = self.__filter_str__(secret)

        self.fmt = fmt
        self.port = port
        self.connection_threads = []
        self.server_thread = None
        self.next_free_port = next_free_port
        self.encoder = encoder
        self.JPEG_quality = JPEG_quality
        self.PNG_compression = PNG_compression
        self.nb_output = nb_output
        self.printaddr = printaddr

        self.url = ""

        self.__ev = threading.Event()
        self.__frame = b""
        self.__terminate = True

    def __filter_str__(self, s):
        regex = re.compile("[^a-zA-Z0-9,\.\_\-]")
        return regex.sub("", s)

    def __random_str__(self, l=12):
        return "".join(
            [
                random.choice(
                    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789"
                )
                for i in range(l)
            ]
        )

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def __get_global_ip(self):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
            s.connect(("1.1.1.1", 0))
            return s.getsockname()[0]

    def __init_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(0.1)
        while self.port < 65535:
            try:
                self.sock.bind((self.host, self.port))
                break
            except OSError as e:
                if e.errno == 98 and self.next_free_port == True:
                    self.port += 1
                else:
                    self.sock.close()
                    self.sock = None
                    raise e
        else:
            self.sock.close()
            self.sock = None
            raise IOError("No port available.")
        self.url = "http://" + self.host + ":" + str(self.port) + "/" + self.secret

    def start(self):
        self.__terminate = False
        self.__init_sock()
        self.server_thread = threading.Thread(target=self.listen, daemon=True)
        self.server_thread.start()

        if self.printaddr:
            print(f"Serving at {self.url}?q=viewer")
        if self.nb_output:
            if __IPYTHON_DISPLAY__ == False:
                print("Warning: IPython.display not available.")
            img = IPython.display.Image(url=self.url)
            IPython.display.display(img)

    def stop(self):
        self.__terminate = True
        try:
            self.server_thread.join()
        except:
            pass
        self.server_thread = None
        self.connection_threads = []

    def listen(self):
        self.sock.listen(5)
        while not self.__terminate:
            try:
                conn, address = self.sock.accept()
            except socket.timeout:
                continue
            conn.settimeout(None)
            t = threading.Thread(
                target=self.connection,
                args=(conn, address, threading.currentThread()),
                daemon=True,
            )
            self.connection_threads.append(t)
            t.start()
        self.sock.close()
        self.sock = None

    def send(self, conn, data):
        data = bytes(data)
        data_len = len(data)
        counter = 0
        while counter < data_len:
            try:
                n = conn.send(data[counter:])
                if n == 0:
                    raise IOError("Connection broken")
            except Exception as e:
                return False
            counter += n
        return True

    def set_frame(self, frame, fmt=None):
        if type(frame) == numpy.ndarray:
            if fmt is None:
                fmt = self.fmt

            # BGR(A) to RGB(A)
            if fmt.lower() == "bgr" and len(frame.shape) == 3:
                frame = frame.copy()
                tmp = frame[:, :, 0].copy()
                frame[:, :, 0] = frame[:, :, 2].copy()
                frame[:, :, 2] = tmp
                del tmp

            b = io.BytesIO()
            if self.encoder == "PNG":
                imageio.imwrite(
                    b,
                    frame,
                    format="PNG-PIL",
                    optimize=False,
                    compress_level=self.PNG_compression,
                )
            else:
                imageio.imwrite(b, frame, format="JPEG-PIL", quality=self.JPEG_quality)

            b.seek(0)
            frame = b.read()
        self.__frame = bytes(frame)
        self.__ev.set()
        self.__ev.clear()

    def connection(self, conn, address, parent):
        bufsize = 1024

        # Read request
        request = b""
        while parent.is_alive():
            try:
                request += conn.recv(bufsize)
            except:
                conn.close()
                return
            if b"\r\n\r\n" in request:
                break
        request = request.split(b"\r\n")[:-2]
        # Bad request?
        # regex = re.compile('^GET \/'+re.escape(self.secret)+'((\?[a-zA-Z]*(=[a-zA-Z0-9]*)? )| )HTTP\/1\.(
        # 0|1)$')
        # if not regex.match(request[0].decode()):
        pr = urllib.parse.urlparse(request[0][5:-9].decode())
        if (
            (request[0][:5] != b"GET /")
            or (request[0][-9:-1] != b" HTTP/1.")
            or (pr.path != self.secret)
        ):
            conn.close()
            return

        # Handle params
        params = urllib.parse.parse_qs(pr.query)
        if "q" in params.keys():
            query = params["q"][0]
        else:
            query = None

        if query == "ping":
            header = (
                "HTTP/1.0 200 OK\r\n"
                + "Content-Type: text/html\r\n"
                + "Access-Control-Allow-Origin: *\r\n"
                + "Connection: keep-alive\r\n\r\n"
            )
            ret = self.send(conn, header.encode())
            while ret and parent.is_alive():
                ret = self.send(conn, b"pong\r\n")
                time.sleep(0.25)
            conn.close()
            return

        elif query == "viewer":
            header = (
                "HTTP/1.0 200 OK\r\n"
                + "Content-Type: text/html\r\n"
                + "Connection: close\r\n\r\n"
            )
            self.send(conn, header.encode())
            path = os.path.join(os.path.dirname(__file__), "viewer_mini.html")
            with open(path, "r") as f:
                html = f.read()
            html = html.replace("{URL}", self.url)
            self.send(conn, html.encode())
            conn.close()
            return

        else:
            # Send header
            header = (
                "HTTP/1.0 200 OK\r\n"
                + "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                + "Cache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, "
                "max-age=0\r\n" + "Connection: close\r\n\r\n"
            )
            ret = self.send(conn, header.encode())
            if not ret:
                conn.close()
                return

            # Contents
            frame_header = b"\r\n--frame\r\nContent-Type: image/jpeg\r\n\r\n"
            ret &= self.send(conn, frame_header)
            while ret and parent.is_alive():
                if self.__ev.wait(0.25):
                    ret &= self.send(conn, self.__frame + frame_header)
            conn.close()
            return
