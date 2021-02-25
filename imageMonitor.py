#Written by DocPhill99 https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1

from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QSlider, QHBoxLayout, QGridLayout, QPushButton
from PyQt5.QtGui import QPixmap
from math import log2, ceil
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np


class VideoThread(QThread):                         #needs to be modularized. Able to make new and destroy while SourceMonitor is running
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cap = cv2.VideoCapture("lab0.mp4")
        self.ret, self.cv_img = self.cap.read()
        self.interrupt = False
        self.frameNum = 0

    def updateFrame(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frameNum)
        self.ret, self.cv_img = self.cap.read()

    def run(self):
        while self._run_flag:
            if self.interrupt:
                self.updateFrame()
                self.interrupt = False
            if self.ret:
                self.change_pixmap_signal.emit(self.cv_img)
                self.ret = False

        # shut down capture system
        self.cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class SourceMonitor(QWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel()

        # create a slider to control frame
        self.trackBar = QSlider(Qt.Horizontal)
        # create a slider to control zoom of original slider
        self.zoomBar = QSlider(Qt.Vertical)

        # create labels for the first and last tick marks
        self.minTrackLbl = QLabel()
        self.maxTrackLbl = QLabel()
        hboxLbls = QHBoxLayout()
        hboxLbls.addWidget(self.minTrackLbl)
        hboxLbls.addStretch(1)
        hboxLbls.addWidget(self.maxTrackLbl)

        gridNav = QGridLayout()
        gridNav.addWidget(self.trackBar, 0, 0)
        gridNav.addLayout(hboxLbls, 1, 0)
        gridNav.addWidget(self.zoomBar, 0, 1, 2, 1)

        #create buttons for playback functionality
        self.playBtn = QPushButton()
        self.pauseBtn = QPushButton()
        self.seekBtn = QPushButton()
        hboxBtns = QHBoxLayout()
        hboxBtns.addStretch(1)
        hboxBtns.addWidget(self.playBtn)
        hboxBtns.addWidget(self.pauseBtn)
        hboxBtns.addWidget(self.seekBtn)
        hboxBtns.addStretch(1)
        
        # create a vertical box layout and add the image and text labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        vbox.addLayout(gridNav)
        vbox.addLayout(hboxBtns)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        

        self.setUpVideoThread()
        self.setUpZoomBar()
        
    def trackInterrupt(self, frameNum):
        self.thread.interrupt = True
        self.thread.frameNum = frameNum
        self.textLabel.setText(str(frameNum))

    def zoomInterrupt(self):     #calculates new parameters to pass into setUpTrackBar
        pos = self.trackBar.value()
        zoomValue = self.zoomBar.value()
        frameMax = self.zoomList[-1]
        range = self.zoomList[zoomValue]
        if pos < range/2: min, max = 0, range
        elif pos > frameMax - range/2: min, max = frameMax - range, frameMax
        else: min, max = pos - range//2, pos + range//2
        self.setUpTrackBar(min, max, pos)

    def setUpVideoThread(self):                 #Maybe later take in param of filename
        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
    
    def setUpZoomBar(self):
        #math to calculate suitable zoom frames
        frameCount = int(self.thread.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        m = ceil(log2(frameCount/10))
        self.zoomList = [10 * 2**x for x in range(0, m)]
        self.zoomList.append(frameCount-1)

        # set characteristics of zoomBar
        self.zoomBar.setMinimum(0)
        self.zoomBar.setMaximum(m)
        self.zoomBar.setTickInterval(1)
        self.zoomBar.setSliderPosition(m)
        self.zoomBar.setTickPosition(QSlider.TicksRight)
        self.zoomBar.valueChanged.connect(self.zoomInterrupt)
        self.setUpTrackBar(0, self.zoomList[-1], 0)

    def setUpTrackBar(self, min, max, pos):
        #stuff that is independent of zoomBar
        self.trackBar.setTickInterval(10)
        self.trackBar.setSliderPosition(pos)
        self.trackBar.valueChanged.connect(lambda x: self.trackInterrupt(self.trackBar.value()))
        self.trackBar.setTickPosition(QSlider.TicksBelow)

        #customize trackBar to fit our needs
        self.trackBar.setMinimum(min)
        self.trackBar.setMaximum(max)
        self.trackInterrupt(pos)

        #initialize trackLabels
        self.minTrackLbl.setText(str(min))
        self.maxTrackLbl.setText(str(max))

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = SourceMonitor()
    a.show()
    sys.exit(app.exec_())