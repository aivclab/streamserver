import socket as _socket
import threading as _threading
import multiprocessing as _multiprocessing
import contextlib as _contextlib
import numpy as _np
import signal as _signal
try:
    import IPython.display as _IPD
    __IPYTHON_DISPLAY__ = True
except:
    __IPYTHON_DISPLAY__ = False
try:
    import cv2 as _cv2
    __OPENCV__ = True
except:
    __OPENCV__ = False
#import io
#import PIL.Image

__all__ = ["StreamServer"]


class StreamServer():
    def __init__(self,host=None,port=5000,next_free_port=True,quality=95, nb_output=True, printaddr=True):
        if host is None:
            self.host = 'localhost'
        elif host == 'GLOBAL':
            self.host = self.__get_global_ip()
        else:
            self.host = host
        
        self.port = port
        self.threads = []
        self.server_process = None
        self.next_free_port = next_free_port
        self.quality = quality
        self.nb_output = nb_output
        self.printaddr = printaddr
        
        self.__ns = _multiprocessing.Manager().Namespace()
        self.__ns.value = b''
        self.__ev = _multiprocessing.Event()
    
    def __del__(self):
        self.stop()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
    
    def __get_global_ip(self):
        with _contextlib.closing(_socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)) as s:
            s.connect(('1.1.1.1', 0))
            return s.getsockname()[0]
    
    def __init_sock(self):
        self.sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        
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
        self.server_process = _multiprocessing.Process(target=self.listen,daemon=True)
        self.server_process.start()
        url = 'http://'+self.host+':'+str(self.port)
        if self.printaddr:
            print("Serving at "+url)
        if self.nb_output:
            if __IPYTHON_DISPLAY__ == False:
                print("Warning: IPython.display not available.")
            img = _IPD.Image(url=url)
            _IPD.display(img)
    
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
        _signal.signal(_signal.SIGINT, _signal.SIG_IGN) 
        self.sock.listen(5)
        while True:
            conn, address = self.sock.accept()
            t = _threading.Thread(target=self.connection, args=(conn,address),daemon=True)
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
    
    def set_frame(self,frame):
        if type(frame) == _np.ndarray:
            if not __OPENCV__:
                raise ValueError("OpenCV module not loaded. Install OpenCV or use pre-encoded JPEGs.")
            ret,jpeg = _cv2.imencode('.jpg',frame,[int(_cv2.IMWRITE_JPEG_QUALITY),self.quality])
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
        if request[:14] != b'GET / HTTP/1.1':
            #raise RuntimeError("Bad request")
            conn.close()
            return
        
        #Send header
        header  = 'HTTP/1.0 200 OK\r\n' +\
                  'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n' +\
                  'Cache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0\r\n' +\
                  'Connection: close\r\n' +\
                  '\r\n'
        self.send(conn,header.encode())

        #Contents
        ret = True
        frame_header = b'\r\n--frame\r\nContent-Type: image/jpeg\r\n\r\n'
        ret &= self.send(conn,frame_header)
        while ret:
            self.__ev.wait()
            ret &= self.send(conn,self.__ns.value + frame_header)
        
        conn.close()
