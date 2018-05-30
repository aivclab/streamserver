import socket
import threading
import multiprocessing
import contextlib
import numpy as np
import signal
import base64
import random
import re
import urllib.parse
import io
import imageio
import os

try:
    import IPython.display
    __IPYTHON_DISPLAY__ = True
except:
    __IPYTHON_DISPLAY__ = False

__all__ = ["StreamServer"]


class StreamServer():
    def __init__(self,host=None,port=5000,next_free_port=True, nb_output=True, printaddr=True, secret=None, fmt='bgr', encoder="JPEG", JPEG_quality=75, PNG_compression=1):
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
        self.threads = []
        self.server_process = None
        self.next_free_port = next_free_port
        self.encoder = encoder
        self.JPEG_quality = JPEG_quality
        self.PNG_compression = PNG_compression
        self.nb_output = nb_output
        self.printaddr = printaddr
        
        self.__ns = multiprocessing.Manager().Namespace()
        self.__ns.value = b''
        self.__ev = multiprocessing.Event()
    
    def __filter_str__(self,s):
        regex = re.compile('[^a-zA-Z0-9,\.\_\-]')
        return regex.sub('',s)
    
    def __random_str__(self,l=12):
        return ''.join([random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789') for i in range(l)])
    
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
    
    def start(self):
        self.__init_sock()
        self.server_process = multiprocessing.Process(target=self.listen,daemon=True)
        self.server_process.start()
        url = 'http://'+self.host+':'+str(self.port)+'/'+self.secret
        if self.printaddr:
            print("Serving at "+url)
        if self.nb_output:
            if __IPYTHON_DISPLAY__ == False:
                print("Warning: IPython.display not available.")
            img = IPython.display.Image(url=url)
            IPython.display.display(img)
    
    def stop(self):
        try:
            self.sock.close()
        except:
            pass
        try:
            self.server_process.terminate()
            self.server_process.join()
        except:
            pass
        self.sock = None
        self.server_process = None
    
    def listen(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN) 
        self.sock.listen(5)
        while True:
            conn, address = self.sock.accept()
            t = threading.Thread(target=self.connection, args=(conn,address),daemon=True)
            self.threads.append(t)
            t.start()
            
    def send(self,conn,d):
        d = bytes(d)
        l = len(d)
        c = 0
        while c < l:
            try:
                n = conn.send(d[c:])
                if n == 0:
                    raise IOError("Connection broken")
            except:
                return False
            c += n
        return True
    
    def set_frame(self,frame,fmt=None):
        if type(frame) == np.ndarray:
            if fmt is None:
                fmt = self.fmt
            
            #BGR(A) to RGB(A)
            if fmt.lower() == "bgr" and len(frame.shape) == 3:
                frame = frame.copy()
                tmp = frame[:,:,0].copy()
                frame[:,:,0] = frame[:,:,2].copy()
                frame[:,:,2] = tmp
                del tmp
            
            b = io.BytesIO()
            if self.encoder == "PNG":
                imageio.imwrite(b,frame,format="PNG-PIL",optimize=False,compress_level=self.PNG_compression)
            else:
                imageio.imwrite(b,frame,format="JPEG-PIL",quality=self.JPEG_quality)

            b.seek(0)
            jpeg = b.read()
            #ret,jpeg = cv2.imencode('.jpg',frame,[int(cv2.IMWRITE_JPEG_QUALITY),self.quality])
        else:
            jpeg = frame
        self.__ns.value = bytes(jpeg)
        self.__ev.set()
        self.__ev.clear()
    
    def connection(self, conn, address):
        bufsize = 1024
        
        #Read request
        request = b''
        while True:
            request += conn.recv(bufsize)
            if b'\r\n\r\n' in request:
                break
        request = request.split(b'\r\n')[:-2]
        #Bad request?
        #regex = re.compile('^GET \/'+re.escape(self.secret)+'((\?[a-zA-Z]*(=[a-zA-Z0-9]*)? )| )HTTP\/1\.(0|1)$')
        #if not regex.match(request[0].decode()):
        pr = urllib.parse.urlparse(request[0][5:-9].decode())
        if (request[0][:5] != b'GET /') or (request[0][-9:-1] != b' HTTP/1.') or (pr.path != self.secret):
            conn.close()
            return
       
        #Handle params
        params = urllib.parse.parse_qs(pr.query)
        if 'q' in params.keys():
            query = params['q'][0]
        else:
            query = None
        
        if query == 'ping':
            header = 'HTTP/1.0 200 OK\r\n' +\
                     'Content-Type: text/html\r\n' +\
                     'Access-Control-Allow-Origin: *\r\n' +\
                     'Connection: close\r\n\r\n'
            self.send(conn,header.encode())
            conn.close()
        
        elif query == 'viewer':
            header = 'HTTP/1.0 200 OK\r\n' +\
                     'Content-Type: text/html\r\n' +\
                     'Connection: close\r\n\r\n'
            self.send(conn,header.encode())
            path = os.path.join(os.path.dirname(__file__), 'viewer_mini.html')
            with open(path,'r') as f:
                html = f.read()
            html = html.replace('  ',' ')
            url = 'http://'+self.host+':'+str(self.port)+'/'+self.secret
            html = html.replace('{URL}',url)
            self.send(conn,html.encode())
            conn.close()

            
            
        
        #Send header
        header  = 'HTTP/1.0 200 OK\r\n' +\
                  'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n' +\
                  'Cache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0\r\n' +\
                  'Connection: close\r\n\r\n'
        self.send(conn,header.encode())

        #Contents
        ret = True
        frame_header = b'\r\n--frame\r\nContent-Type: image/jpeg\r\n\r\n'
        ret &= self.send(conn,frame_header)
        while ret:
            self.__ev.wait()
            ret &= self.send(conn,self.__ns.value + frame_header)
        
        conn.close()
