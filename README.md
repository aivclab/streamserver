# multipart image HTTP streaming server.

## Install:
```
pip install git+ssh://git@bitbucket-server.alexandra.dk:7999/~soren.rasmussen/streamserver.git
```

## Example:
```
import cv2
import streamserver
cap = cv2.VideoCapture(0)

ret,_ = cap.read()
assert ret == True

with streamserver.StreamServer(JPEG_quality=75,host='localhost',port=5000) as ss:
    while cap.isOpened():
        ret,frame = cap.read()
        ss.set_frame(frame)
        wk = cv2.waitKey(20)
        if wk == ord('q'):
            break
cap.release()
```

#TODO:
* Multiple streams on same server
