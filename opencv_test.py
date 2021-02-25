import numpy as np
import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from VideoAnnotator import Ui_MainWindow


cap = cv2.VideoCapture('lab0.mp4')

while(cap.isOpened()):
    ret, frame = cap.read()
    
    if cv2.waitKey(10) & 0xFF == ord('q') or not ret:
        break    

    cv2.imshow('frame', frame)


cap.release()
cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
