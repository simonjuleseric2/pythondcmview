
import numpy as np

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, QTimer
#from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider

from PyQt5.QtWidgets import (QHBoxLayout, QAction, QApplication, QWidget, QVBoxLayout, QFileDialog, QLabel, QGridLayout,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy, QProgressBar, QSlider, QSplitter, QPushButton)

from pyqtgraph import ImageView
import pydicom as dc
import qimage2ndarray
import os
import glob
from os.path import isfile, join
from pydicom.filereader import InvalidDicomError

class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.slice=0
        self.UID_t= ['1.2.840.10008.5.1.4.1.1.2', '1.2.840.10008.5.1.4.1.1.2.1']
        self.round_factor=3
        self.lst_dcm_vol=[]
        self.setWindowTitle("DCM Viewer")

        self.central_widget = QWidget()
        self.button_frame = QPushButton('Load Volume', self.central_widget)
        self.image_view =  QtGui.QLabel(self)

        img_path='image1.dcm'
        img=dc.read_file(img_path).pixel_array
        img=(img-np.min(img))
        img=img/np.max(img)*255
        image=qimage2ndarray.array2qimage(img)

        self.image_view.setBackgroundRole(QtGui.QPalette.Base)
        self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setValue(0)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_frame)

        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.slider)
        self.setCentralWidget(self.central_widget)
##

        #self.scrollArea = QScrollArea()
        #self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        #self.scrollArea.setWidget(self.image_view)
        #self.setCentralWidget(self.scrollArea)
        #self.createActions()

        self.button_frame.clicked.connect(self.open)
        self.slider.valueChanged.connect(self.navigate_slices)


    def open(self):
        #fileName, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", 'K:/RAO_Physik/Research/1_FUNCTIONAL IMAGING/7_Immunoradiomics/crc/1_data/dicom/3_dcm_sorted_2/CT/T0/')

        if fileName:

            directory_name=os.path.dirname(fileName)

            lst_dcm=glob.glob(directory_name+'/*.dcm')
            listDicomProblem=[]
            onlyfiles = []

            volume_ini=False

            #self.progress = QProgressBar(self)
            #self.progress.setGeometry(200, 80, 250, 20)
            #self.completed = 0

            for f in lst_dcm:

                #self.completed += 1
                #self.progress.setValue(self.completed)
                #QApplication.processEvents()

                try:
                    if isfile(f) and dc.read_file(f).SOPClassUID in self.UID_t: #read only dicoms of certain modality
                        onlyfiles.append((round(float(dc.read_file(f).ImagePositionPatient[2]), self.round_factor), f)) #sort files by slice position
                        if volume_ini==False:
                            x=dc.read_file(f).Columns
                            y=dc.read_file(f).Rows
                            volume_ini=True

                except InvalidDicomError: #not a dicom file
                    listDicomProblem.append(name+' '+f)
                    pass

            z=len(onlyfiles)
            onlyfiles.sort()
            self.lst_dcm_vol=onlyfiles
            self.slider.setRange(0,len(onlyfiles)-1)
            self.slice=round(len(lst_dcm)/2)
            self.slider.setValue(self.slice)
            #self.sliderMoved(self.slice)

            img_path=onlyfiles[self.slice][1]
            img=dc.read_file(img_path).pixel_array

            img=(img-np.min(img))
            img=img/np.max(img)*255
            image=qimage2ndarray.array2qimage(img)


            if image.isNull():
                QMessageBox.information(self, "Image Viewer",
                        "Error while loading %s." % fileName)
                return

            self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))############################################################################
            #self.scaleFactor = 0.5

            #self.printAct.setEnabled(True)
            #self.fitToWindowAct.setEnabled(True)
            #self.updateActions()

            #if not self.fitToWindowAct.isChecked():
            #    self.image_view.adjustSize()


    def navigate_slices(self, value):
        #print(value)
        self.slice = self.slider.value()
        #print(self.slice)
        img_path=self.lst_dcm_vol[self.slice][1]
        img=dc.read_file(img_path).pixel_array

        img=(img-np.min(img))
        img=img/np.max(img)*255
        image=qimage2ndarray.array2qimage(img)
        self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))

    def wheelEvent(self, ev):

        deltaZ=ev.angleDelta()
        deltaZ=deltaZ.y()/120

        self.slice=self.slice+int(deltaZ)
        img_path=self.lst_dcm_vol[self.slice][1]
        self.slider.setValue(self.slice)

        img=dc.read_file(img_path).pixel_array
        img=(img-np.min(img))
        img=img/np.max(img)*255
        image=qimage2ndarray.array2qimage(img)

        self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))
    


if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
app.exit(app.exec_())
