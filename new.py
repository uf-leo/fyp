"""
In this example, we demonstrate how to create simple camera viewer using Opencv3 and PyQt5
Author: Berrouba.A
Last edited: 21 Feb 2018
"""

# import system module
import sys
import os
import datetime
import ctypes
import mysql.connector

# import some PyQt5 modules
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QWidget, QTableWidgetItem
from PyQt5.QtWidgets import QWidget, QFrame
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from PyQt5 import uic

# import Opencv module
import cv2
import numpy as np
import pytesseract
import re
import datetime
from modules.finalocr import detect


counter =0
detected_plates=[]
plate_number = ""
date = str(datetime.datetime.now().date())
table_name = f"log_{date.replace('-', '_')}"
plate_filename = ""
driver_filename = ""
roi = None
imgRoi = None

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vrs")
class MainWindow(QMainWindow):
    # class constructor
    def __init__(self):
        # call QWidget constructor
        super(MainWindow, self).__init__()

        uic.loadUi(r"resources/ui/main_window.ui", self)
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        self.tabWidget.setCurrentWidget(self.tabWidget.findChild(QWidget, "Detect"))

        # create a timer
        self.timer = QTimer()
        # set timer timeout callback function
        self.timer.timeout.connect(self.viewCam)
        # set control_bt callback clicked  function
        self.handle_btn.clicked.connect(self.controlTimer)
        self.exit_btn.clicked.connect(sys.exit)

        self.driver_image.setStyleSheet("border: 2px solid black;")
        self.number_plate_image.setStyleSheet("border: 2px solid black;")
        self.cam_label.setStyleSheet("border: 2px solid black;")        

        self.whT = 320
        self.confThreshold = 0.8
        self.nmsThreshold = 0.2
        self.minArea = 300
        count=0

        # Database connection
        self.connection = mysql.connector.connect(
            user="root",
            password = "916519umer",
            host="localhost",
            database = "mysql"
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER UNSIGNED AUTO_INCREMENT PRIMARY KEY, plate_number varchar(20), driver_picture varchar(255), created_at varchar(255), vehical_status varchar(3))")
        self.fill_log_table()
        #### LOAD MODEL
        ## Coco Names
        classesFile = r"resources/models/obj.names"
        self.classNames = []
        with open(classesFile, 'rt') as f:
            self.classNames = f.read().rstrip('\n').split('\n')
        print(self.classNames)
        ## Model Files
        modelConfiguration = r"resources/models/yolov4-obj.cfg"
        modelWeights = r"resources/models/yolov4-obj_final.weights"
        self.net = cv2.dnn.readNetFromDarknet(modelConfiguration,modelWeights)
        self.nFaceCascade = cv2.CascadeClassifier(r"resources/models/haarcascade_frontalface_alt.xml")
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    def findObjects(self, outputs, img):
        global counter, detected_plates, plate_filename, plate_number, driver_filename, imgRoi, roi
        hT, wT, cT = img.shape
        bbox = []
        classIds = []
        confs = []
        for output in outputs:
            for det in output:
                scores = det[5:]
                classId = np.argmax(scores)
                confidence = scores[classId]
                if confidence > self.confThreshold:
                    w, h = int(det[2] * wT), int(det[3] * hT)
                    x, y = int((det[0] * wT) - w / 2), int((det[1] * hT) - h / 2)
                    bbox.append([x, y, w, h])
                    classIds.append(classId)
                    confs.append(float(confidence))

        indices = cv2.dnn.NMSBoxes(bbox, confs, self.confThreshold, self.nmsThreshold)

        for i in indices:
            i = i[0]
            box = bbox[i]
            x, y, w, h = box[0], box[1], box[2], box[3]
            # print(x,y,w,h)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)
            cv2.putText(img, f'{self.classNames[classIds[i]].upper()} {int(confs[i] * 100)}%',
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            roi=img[y-5:y+h+5, x-5:x+w+5]
            time = str(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            filename='temp/image-{}.jpg'.format(time)
            try:
                cv2.imwrite(filename, roi)
            except:
                print("there")
                print("Unable to detect")
            plate_number = detect(filename)

            if len(plate_number)>4:
                if not plate_number in detected_plates[-5:]:
                    print(plate_number)
                    detected_plates.append(plate_number)
                    # time = str(datetime.datetime.now().strftime("%Y%m%d%H%M"))
                    # print(time)
                    plate_filename = 'output/{}-plate.jpg'.format(plate_number)
                    counter += 1
                # detected_plates = detected_plates[:5]
                cv2.putText(img, str(plate_number),
                        (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

                nFaces = self.nFaceCascade.detectMultiScale(img, 1.1, 10)
                for (x, y, w, h) in nFaces:
                    area = w * h
                    if x < int(603 / 2) - w / 2:
                        if area > self.minArea:
                            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)
                            cv2.putText(img, "face", (x, y - 5),
                                        cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)
                            imgRoi = img[y:y + h, x:x + w]
                            driver_filename = 'output/{}-driver.jpg'.format(plate_number)

                if counter == 1:
                    try:
                        if plate_filename:
                            cv2.imwrite(plate_filename, roi)
                        if driver_filename:
                            cv2.imwrite(driver_filename, imgRoi)
                        else:
                            driver_filename = "Couldn't detect driver"

                        pixmap = QPixmap(plate_filename)
                        self.number_plate_image.setScaledContents(True)
                        self.number_plate_image.setPixmap(pixmap)
                        self.plate_number_edit_box.setPlainText(plate_number)

                        pixmap = QPixmap(driver_filename)
                        self.driver_image.setScaledContents(True)
                        self.driver_image.setPixmap(pixmap)
                        self.cursor.execute(
                            f"INSERT INTO {table_name} (id, plate_number, driver_picture, created_at, vehical_status) VALUES (NULL, %s, %s, %s, %s)",
                            (plate_number, driver_filename, datetime.datetime.now(), "IN"))
                        self.connection.commit()
                        self.fill_log_table()
                        driver_filename = ""
                        counter = 0
                    except:
                        print("Unable to detect!")



    # view camera
    def viewCam(self):
        ret, image = self.cap.read()
        blob = cv2.dnn.blobFromImage(image, 1 / 255, (self.whT, self.whT), [0, 0, 0], 1, crop=False)
        self.net.setInput(blob)
        layersNames = self.net.getLayerNames()
        outputNames = [(layersNames[i[0] - 1]) for i in self.net.getUnconnectedOutLayers()]
        outputs = self.net.forward(outputNames)
        self.findObjects(outputs, image)

        
        # convert image to RGB format
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
      
        img = QImage(image, image.shape[1], image.shape[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        # show image in img_label
        self.cam_label.setPixmap(pix)        

    # start/stop timer
    def controlTimer(self):
        # if timer is stopped
        if not self.timer.isActive():
            # create video capture
            self.cap = cv2.VideoCapture('demo.mp4')
            self.cap.set(3, 603)
            self.cap.set(4, 420)
            self.cap.set(10, 100)
            # start timer
            self.timer.start(20)
            # update control_bt text
            self.handle_btn.setText("Stop")
        # if timer is started
        else:
            # stop timer
            self.timer.stop()
            # release video capture
            self.cap.release()
            # update control_bt text
            self.handle_btn.setText("Start")

    def fill_log_table(self):
        query = self.cursor.execute(f"select * from {table_name}")
        data = self.cursor.fetchall()
        # print(data)
        self.tableWidget.setRowCount(0)
        self.tableWidget.insertRow(0)

        for index, row in enumerate(data):
            for column, item in enumerate(row):
                if column == 0:
                    self.tableWidget.setItem(index, column, QTableWidgetItem(str(index+1)))
                else:
                    self.tableWidget.setItem(index, column, QTableWidgetItem(str(item)))
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)  


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
