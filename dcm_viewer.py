
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtWidgets import (QHBoxLayout, QAction, QApplication, QWidget, QVBoxLayout, QFileDialog, QLabel, QGridLayout,
        QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy, QProgressBar, QSlider, QSplitter, QPushButton)
import pydicom as dc
import qimage2ndarray
import os
import glob
from os.path import isfile, join
from pydicom.filereader import InvalidDicomError
from skimage import color
from skimage.draw import polygon
import cv2
from PIL import Image, ImageDraw, ImageFont

class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.slice=0
        self.UID_t= ['1.2.840.10008.5.1.4.1.1.2', '1.2.840.10008.5.1.4.1.1.2.1']
        self.RS_UID = ['1.2.840.10008.5.1.4.1.1.481.3', 'RT Structure Set Storage']
        self.round_factor=3
        self.lst_dcm_vol=[]
        self.setWindowTitle("DCM Viewer")

        self.central_widget = QWidget()
        self.button_frame = QPushButton('Load Volume', self.central_widget)
        self.image_view =  QLabel(self)
        self.roi_slices=[]
        self.mask=[]
        self.contours=[]
        self.slices=[]
        self.volume_shape=[]
        self.dcm_volume=np.zeros((50, 50, 200), np.uint8)
        self.dispay_dim=(512, 512)

        img=Image.new('RGB', self.dispay_dim, color=(10, 10, 10))
        img=np.array(img)
        img=qimage2ndarray.array2qimage(img)

        self.image_view.setBackgroundRole(QtGui.QPalette.Base)
        self.image_view.setPixmap(QtGui.QPixmap.fromImage(img))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setValue(0)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.button_frame)

        self.layout.addWidget(self.image_view)
        self.layout.addWidget(self.slider)
        self.setCentralWidget(self.central_widget)

        self.button_frame.clicked.connect(self.open)
        self.slider.valueChanged.connect(self.navigate_slices)
        self.Roi_volume=False

    def open(self):
        #fileName, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        #fileName, _ = QFileDialog.getOpenFileName(self, "Open File", 'K:/RAO_Physik/Research/1_FUNCTIONAL IMAGING/7_Immunoradiomics/crc/1_data/dicom/resized_img/CT_linear_3_75/CT/T0/10/')
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", os.getcwd())

        if fileName:

            directory_name=os.path.dirname(fileName)
            lst_dcm=glob.glob(directory_name+'/*.dcm')
            listDicomProblem=[]
            onlyfiles = []
            volume_ini=False
            z_positions=[]
            print(lst_dcm)
            for f in lst_dcm:

                try:
                    if isfile(f):
                        if dc.read_file(f).SOPClassUID in self.UID_t: #read only dicoms of certain modality
                            zz=dc.read_file(f).ImagePositionPatient[2]
                            onlyfiles.append((round(float(zz), self.round_factor), f)) #sort files by slice position
                            z_positions.append(round(float(zz), self.round_factor))
                        elif dc.read_file(f).SOPClassUID in self.RS_UID:
                            rs_name=f
                            self.Roi_volume=True

                        if volume_ini==False:
                            x=dc.read_file(f).Columns
                            y=dc.read_file(f).Rows
                            volume_ini=True

                except InvalidDicomError:
                    pass


            onlyfiles.sort()
            z_positions.sort()
            slice0=dc.read_file(onlyfiles[0][1])
            self.volume_shape=[slice0.Rows, slice0.Columns, len(onlyfiles)]
            if self.Roi_volume:
                structure=dc.read_file(rs_name)
                self.contours = []


                for i in range(len(structure.ROIContourSequence)):
                    #if structure.StructureSetROISequence[i].ROIName in ['V1a', 'V2a', 'V3a']:
                    self.contour = {}
                    self.contour['color'] = structure.ROIContourSequence[i].ROIDisplayColor
                    self.contour['number'] = structure.StructureSetROISequence[i].ROINumber
                    self.contour['name'] = structure.StructureSetROISequence[i].ROIName
                    self.contour['contours'] = [s.ContourData for s in structure.ROIContourSequence[i].ContourSequence]
                    self.contours.append(self.contour)

                self.mask, colors = self.get_mask(self.contours, slice0, z_positions)
                x, y, z=np.where(self.mask>0)
                self.roi_slices=np.unique(z)
                self.roi_slices=np.unique(z)

            self.lst_dcm_vol=onlyfiles
            x, y, z=np.where(self.mask>0)
            self.roi_slices=np.unique(z)

            self.dcm_volume=np.zeros((self.volume_shape[0], self.volume_shape[1], 3, len(onlyfiles)), dtype=np.uint8)
            for i in range(0, len(onlyfiles)):
                #print(onlyfiles[i][1])
                img=dc.read_file(onlyfiles[i][1]).pixel_array
                img[img == -2000] = 0
                img=img/np.max(img)*255
                #print(onlyfiles[i][0])
                if i in self.roi_slices:
                    img2=self.stack_img_mask(img, self.mask[:, :, i])
                else:
                    #img2=np.dstack((img, img, img))
                    img2=self.stack_img(img)
                self.dcm_volume[:, :, :, i]=img2

            self.lst_dcm_vol=onlyfiles
            self.slider.setRange(0,len(onlyfiles)-1)
            self.slice=round(len(lst_dcm)/2)
            self.slider.setValue(self.slice)

            image=self.dcm_volume[:, :, :, self.slice]
            image=cv2.resize(image, self.dispay_dim, interpolation = cv2.INTER_CUBIC)
            image=qimage2ndarray.array2qimage(image)

            if image.isNull():
                QMessageBox.information(self, "Image Viewer",
                        "Error while loading %s." % fileName)
                return

            self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))


    def navigate_slices(self, value):
        self.slice = self.slider.value()
        #img_path=self.lst_dcm_vol[self.slice][1]
        img2=self.dcm_volume[:, :, :, self.slice]
        image=cv2.resize(img2, self.dispay_dim, interpolation = cv2.INTER_CUBIC)
        image=qimage2ndarray.array2qimage(image)
        self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))

    def wheelEvent(self, ev):

        deltaZ=ev.angleDelta()
        deltaZ=deltaZ.y()/120
        self.slice=self.slice+int(deltaZ)
        if self.slice>len(self.lst_dcm_vol)-1:
            self.slice=self.slice-len(self.lst_dcm_vol)

        img2=self.dcm_volume[:, :, :, self.slice]
        image=cv2.resize(img2, self.dispay_dim, interpolation = cv2.INTER_CUBIC)
        image=qimage2ndarray.array2qimage(image)
        self.image_view.setPixmap(QtGui.QPixmap.fromImage(image))
        self.slider.setValue(self.slice)

    def get_mask(self, contours, slice0, z):
        #z array of z positions
        pos_r = slice0.ImagePositionPatient[1]
        spacing_r = slice0.PixelSpacing[1]
        pos_c = slice0.ImagePositionPatient[0]
        spacing_c = slice0.PixelSpacing[0]
        label = np.zeros(self.volume_shape, dtype=np.uint8)
        for con in contours:
            for c in con['contours']:
                nodes = np.array(c).reshape((-1, 3))
                assert np.amax(np.abs(np.diff(nodes[:, 2]))) == 0

                z_index = z.index(nodes[0, 2])
                r = (nodes[:, 1] - pos_r) / spacing_r
                c = (nodes[:, 0] - pos_c) / spacing_c
                rr, cc = polygon(r, c)
                label[rr, cc, z_index] = 1

        colors = tuple(np.array([con['color'] for con in contours]) / 255.0)
        return label, colors

    def stack_img_mask(self, img_slice, mask_slice):
        alpha = 0.6
        shape=np.shape(img_slice)
        color_mask = np.zeros((shape[0], shape[1], 3))
        color_mask[:, :, 0] = mask_slice

        img_color = np.dstack((img_slice, img_slice, img_slice))
        img_hsv = color.rgb2hsv(img_color)
        color_mask_hsv = color.rgb2hsv(color_mask)
        img_hsv[..., 0] = color_mask_hsv[..., 0]
        img_hsv[..., 1] = color_mask_hsv[..., 1] * alpha

        return color.hsv2rgb(img_hsv)

    def stack_img(self, img_slice):
        shape=np.shape(img_slice)
        img_color = np.dstack((img_slice, img_slice, img_slice))
        img_hsv = color.rgb2hsv(img_color)

        return color.hsv2rgb(img_hsv)


if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
app.exit(app.exec_())
