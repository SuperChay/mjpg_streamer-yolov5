"""
访问地址默认http://ip:8000/stream.mjpg
"""
import logging
import socketserver
from threading import Condition, Thread
from PIL import Image
import cv2
import traceback
import io
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from yolo import yolov5
import threading


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, frame):
        with self.condition:
            self.frame = frame
            self.condition.notify_all()


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 自定义网站访问地址，修改self.path，默认http://ip:8000/stream.mjpg
        if self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                traceback.print_exc()
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Camera:
    def __init__(self, output, width, height, framerate, url):
        self.output = output
        self.width = width
        self.height = height
        self.framerate = framerate
        self.url = url

    def __enter__(self):
        # 相机或rtsp流打开路径，参数0表示打开笔记本的内置摄像头

        self.cap = cv2.VideoCapture(self.url)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.stop_capture = False
        self.thread = Thread(target=self.capture)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_capture = True
        self.thread.join()
        self.cap.release()

    def getIniVal(self, secname, keyname, defVal='', inifile='.\\para.ini'):
        alines = open(inifile, 'r', errors='ignore').readlines()
        findsec = 0
        for linec in alines:
            if linec.find('[' + secname + ']') >= 0:
                findsec = 1
            if linec.find(keyname + '=') >= 0 and findsec == 1:
                return linec[len(keyname) + 1:].strip()
        return defVal

    def capture(self):
        frame_duration = 1. / self.framerate
        while not self.stop_capture:
            start = time.time()
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 实例化一个yolov5对象
                yolonet = yolov5(modelpath='weights/yolov5x.onnx', confThreshold=0.3, nmsThreshold=0.5,
                                 objThreshold=0.3)
                srcimg = yolonet.detect(frame)
                img = Image.fromarray(srcimg)
                img.save(self.output, format='JPEG')
            elapsed = time.time() - start
            logging.debug("Frame acquisition time: %.2f" % elapsed)
            if elapsed < frame_duration:
                time.sleep(frame_duration - elapsed)

try:
    output = StreamingOutput()
    # 可以修改视频的fps，宽度和高度
    with Camera(output, 640, 480, 25,url=0) as camera:
        # 访问地址和端口
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
except KeyboardInterrupt:
    pass