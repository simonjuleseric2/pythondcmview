
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QImage, QPainter, QPalette, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy, QProgressBar)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
import pydicom as dc
import numpy as np
import qimage2ndarray
import os
import glob
from os.path import isfile, join
from pydicom.filereader import InvalidDicomError

class dcmViewer(QMainWindow):
    def __init__(self):
        super(dcmViewer, self).__init__()

        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Simon DCM Viewer")
        self.resize(700, 700)
        self.slice=0
        self.UID_t= ['1.2.840.10008.5.1.4.1.1.2', '1.2.840.10008.5.1.4.1.1.2.1']
        self.round_factor=3
        self.lst_dcm_vol=[]
        #self.progress = QProgressBar(self)
        #self.progress.setGeometry(200, 80, 250, 20)

    def open(self):
        #fileName, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", 'C:/Users/sburg/ttt/test/a10')

        if fileName:

            #yourQImage=qimage2ndarray.array2qimage(yournumpyarray)

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

            #x=dc.read_file(onlyfiles[0]).Columns
            #y=dc.read_file(onlyfiles[0]).Rows
            z=len(onlyfiles)
            onlyfiles.sort()
            self.lst_dcm_vol=onlyfiles
            '''volume = np.empty((x,y,z))
            #slices=[]
            i=0
            for f in onlyfiles:

                ds=dc.read_file(f[1])
                slice_xy=ds.pixel_array
                volume[:, :, i]=slice_xy
                #slices.append(round(float(ds.ImagePositionPatient[2]), self.round_factor))
                i=i+1

            '''

            self.slice=round(len(lst_dcm)/2)

            img_path=onlyfiles[self.slice][1]
            img=dc.read_file(img_path).pixel_array
            #img=volume[:, :, self.slice]

            #img[img == -2000] = 0 #remove corners set to -2000 UH
            #normalise to 0-255
            img=(img-np.min(img))
            img=img/np.max(img)*255
            image=qimage2ndarray.array2qimage(img)


            if image.isNull():
                QMessageBox.information(self, "Image Viewer",
                        "Error while loading %s." % fileName)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.printAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def wheelEvent(self, ev):

        deltaZ=ev.angleDelta()
        deltaZ=deltaZ.y()/120

        self.slice=self.slice+int(deltaZ)
        img_path=self.lst_dcm_vol[self.slice][1]

        img=dc.read_file(img_path).pixel_array
        img=(img-np.min(img))
        img=img/np.max(img)*255
        image=qimage2ndarray.array2qimage(img)

        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        self.scaleFactor = 1.0

        self.printAct.setEnabled(True)
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()

        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()



    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def about(self):
        QMessageBox.about(self, "")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)

        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P",
                enabled=False, triggered=self.print_)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-",
                enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
                checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow)

        self.aboutAct = QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QAction("About &Qt", self,
                triggered=QApplication.instance().aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    dcmViewer = dcmViewer()
    dcmViewer.show()
sys.exit(app.exec_())
