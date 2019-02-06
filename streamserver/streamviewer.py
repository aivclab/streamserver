import contextlib
import io
import os
import random
import re
import socket
import ssl as libssl
import sys
import threading
import time
import urllib.parse
from pathlib import Path


import imageio
import numpy as np

try:
    import IPython.display

    __IPYTHON_DISPLAY__ = True
except:
    __IPYTHON_DISPLAY__ = False

__all__ = ['StreamServer','run_streamserver']


def generate_openssl_ssl_cert(base_path, key_path, pem_path):
    ret = os.system(f'openssl req -nodes -new -x509 -keyout {key_path} -out {pem_path} -subj "/" -days 10000')
    assert ret == 0, 'Could not create SSL cert'
    print(f'*** Created self-signed SSL cert in {base_path}. Consider swapping it with a real cert.')


class StreamServer():
    def __init__(self,
                 host=None,
                 port=5000,
                 ssl=True,
                 next_free_port=True,
                 nb_output=True,
                 print_addr=True,
                 secret=None,
                 fmt='bgr',
                 encoder='JPEG',
                 JPEG_quality=75,
                 PNG_compression=1):
        if host is None:
            self.host = 'localhost'
        elif host == 'GLOBAL':
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
        self.print_addr = print_addr

        self.ssl = ssl
        if self.ssl:
            base_path = Path(__file__).parent
            key_path = base_path / 'cert.key'
            pem_path = base_path / 'cert.pem'
            if (key_path.exists() == False) or (pem_path.exists() == False):
                generate_openssl_ssl_cert(base_path, key_path, pem_path)

            self.ssl_context = libssl.SSLContext(libssl.PROTOCOL_SSLv23)
            self.ssl_context.load_cert_chain(pem_path, key_path)

        self.url = ''

        self.__ev = threading.Event()
        self.__ev.clear()

        self.set_frame(np.zeros((1, 1, 3), dtype=np.uint8))
        #        self.__frame = b''
        self.__terminate = True

    def __filter_str__(self, s):
        regex = re.compile('[^a-zA-Z0-9,\.\_\-]')
        return regex.sub('', s)

    def __random_str__(self, l=12):
        return ''.join(
            [random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789') for i in range(l)])

    def __del__(self):
        self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def __get_global_ip(self):
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
            s.connect(('1.1.1.1', 0))
            return s.getsockname()[0]

    def __init_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(.1)
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
            raise IOError('No port available.')
        if self.ssl:
            self.ssl_sock = self.ssl_context.wrap_socket(self.sock, server_side=True)
            self.url = 'https://' + self.host + ':' + str(self.port) + '/' + self.secret
        else:
            self.ssl_sock = self.sock
            self.url = 'http://' + self.host + ':' + str(self.port) + '/' + self.secret

    def start(self):
        self.__terminate = False
        self.__init_sock()
        self.server_thread = threading.Thread(target=self.listen, daemon=True)
        self.server_thread.start()

        if self.print_addr:
            print(f'Serving at {self.url}?q=viewer')
        if self.nb_output:
            if not __IPYTHON_DISPLAY__:
                print('Warning: IPython.display not available.')
            img = IPython.display.Image(url=self.url)
            if bool(getattr(sys, 'ps1', sys.flags.interactive)):
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
        self.ssl_sock.listen(5)
        while not self.__terminate:
            try:
                conn, address = self.ssl_sock.accept()
            except socket.timeout:
                continue
            conn.settimeout(None)
            self.connection_threads = [t for t in self.connection_threads if t.is_alive()]
            self.connection_threads.append(
                threading.Thread(target=self.connection, args=(conn, address, threading.currentThread()),
                                 daemon=True))
            self.connection_threads[-1].start()

        self.ssl_sock.close()
        #        self.sock.close()
        self.sock = None
        self.ssl_sock = None

    def send(self, conn, d):
        d = bytes(d)
        l = len(d)
        c = 0
        while c < l:
            try:
                n = conn.send(d[c:])
                if n == 0:
                    raise IOError('Connection broken')
            except:
                return False
            c += n
        return True

    def set_frame(self, frame, fmt=None):
        if isinstance(frame, np.ndarray):
            if fmt is None:
                fmt = self.fmt

            # BGR(A) to RGB(A)
            if fmt.lower() == 'bgr' and len(frame.shape) == 3:
                frame = frame.copy()
                tmp = frame[:, :, 0].copy()
                frame[:, :, 0] = frame[:, :, 2].copy()
                frame[:, :, 2] = tmp
                del tmp

            b = io.BytesIO()
            if self.encoder == 'PNG':
                imageio.imwrite(b, frame, format='PNG-PIL', optimize=False, compress_level=self.PNG_compression)
            else:
                imageio.imwrite(b, frame, format='JPEG-PIL', quality=self.JPEG_quality)

            b.seek(0)
            frame = b.read()
        self.__frame = bytes(frame)
        self.__ev.set()
        self.__ev.clear()

    def connection(self, conn, address, parent):
        buffer_size = 1024

        # Read request
        request = b''
        while parent.is_alive():
            try:
                recv = conn.recv(buffer_size)
                if len(recv) > 0:
                    request += recv
                else:
                    conn.close()
                    return
            except:
                conn.close()
                return
            if b'\r\n\r\n' in request:
                break
        request = request.split(b'\r\n')[:-2]
        # Bad request?
        # regex = re.compile('^GET \/'+re.escape(self.secret)+'((\?[a-zA-Z]*(=[a-zA-Z0-9]*)? )| )HTTP\/1\.(
        # 0|1)$')
        # if not regex.match(request[0].decode()):
        if len(request) == 0:
            conn.close()
            return
        pr = urllib.parse.urlparse(request[0][5:-9].decode())
        if (request[0][:5] != b'GET /') or (request[0][-9:-1] != b' HTTP/1.') or (pr.path != self.secret):
            conn.close()
            return

        # Handle params
        params = urllib.parse.parse_qs(pr.query)
        if 'q' in params.keys():
            query = params['q'][0]
        else:
            query = None

        if query == 'ping':
            header = ('HTTP/1.0 200 OK\r\n'
                      'Content-Type: text/html\r\n'
                      'Access-Control-Allow-Origin: *\r\n'
                      'Connection: keep-alive\r\n\r\n')
            ret = self.send(conn, header.encode())
            while ret and parent.is_alive():
                ret = self.send(conn, b'pong\r\n')
                if ret == 0:
                    break
                time.sleep(.25)
            conn.close()
            return

        elif query == 'viewer':
            header = ('HTTP/1.0 200 OK\r\n'
                      'Content-Type: text/html\r\n'
                      'Connection: close\r\n\r\n')
            self.send(conn, header.encode())
            path = os.path.join(os.path.dirname(__file__), 'viewer_mini.html')
            with open(path, 'r') as f:
                html = f.read()
            html = html.replace('{URL}', self.url)
            self.send(conn, html.encode())
            conn.close()
            return

        else:
            # Send header
            header = ('HTTP/1.0 200 OK\r\n'
                      'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n'
                      'Cache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, '
                      'max-age=0\r\n'
                      'Connection: close\r\n\r\n')
            ret = self.send(conn, header.encode())
            if not ret:
                conn.close()
                return

            # Contents
            frame_header = str.encode(f'\r\n--frame\r\nContent-Type: image/{self.encoder.lower()}\r\n\r\n')
            ret &= self.send(conn, frame_header)

            while ret and parent.is_alive():
                if self.__ev.wait(1) and ret:
                    ret &= self.send(conn, self.__frame + frame_header)
                else:
                    ret &= self.send(conn, self.__frame + frame_header)
            conn.close()
            return

def run_streamserver():
    from .samples.ss_cv2 import main
    main()

if __name__ == '__main__':
    run_streamserver()