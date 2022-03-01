# mjpg_streamer-yolov5
基于python3.8部署mjpg-streamer服务器，结合yolov5算法实现目标检测
# 第一步：
进入src目录，pip install -r requirements
# 第二步：
运行stream-yolo.py（默认打开笔记本摄像头，可通过修改with Camera(output, 640, 480, 25,url=0) as camera代码中的url来修改url地址
# 第三步：
默认访问地址：http://ip:8000/stream.mjpg
可自行修改访问地址，代码内有注释
# 其他yolov5模型地址：
链接：https://pan.baidu.com/s/1Nb83yVvww520FbRhaHnaKw 
提取码：e10h
