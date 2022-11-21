import base64
import time
from typing import List, Union

import cv2
from PySide6.QtCore import Signal, QThread, QMutex, QUrl
from PySide6.QtGui import QDoubleValidator, QImage, QTextImageFormat, QCloseEvent, QPixmap, Qt, QAction
from PySide6.QtMultimedia import QMediaDevices, QCameraDevice
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QGridLayout, QLineEdit, QCheckBox, QComboBox, QInputDialog, \
    QHBoxLayout, QToolButton, QWidget, QVBoxLayout, QMessageBox, QSizePolicy

from .settings import getIcon, Settings
from .textedit import TextEdit
from .widgets import checkLock


class Image(QDialog):

    okClicked = Signal(QTextImageFormat)

    def __init__(self, imageFormat:QTextImageFormat, parent = None):
        QDialog.__init__(self, parent)
        self._parentWidget:TextEdit = parent

        self.imageFormat = imageFormat

        self.rawImage = Image.retriveRawImage(self.imageFormat)
        self.imageRatio = self.rawImage.width() / self.rawImage.height()

        self.initUI()

    @staticmethod
    def retriveRawImage(imageFormat:QTextImageFormat):
        base64data = imageFormat.name()[22:]
        imageData = base64.b64decode(base64data.encode('utf-8'))
        i = QImage()
        i.loadFromData(imageData)
        return i
 
    def initUI(self):

        self.setWindowIcon(getIcon('image'))
        widthLabel = QLabel("宽度: ",self)
        self.width = QLineEdit(self)
        widthValidator = QDoubleValidator(0.00, 99999.99, 2)
        widthValidator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.width.setValidator(widthValidator)
        self.width.setText(str(round(self.imageFormat.width(),2)))

        heightLabel = QLabel("长度",self)
        self.height = QLineEdit(self)
        heightValidator = QDoubleValidator(0.00, 99999.99, 2)
        heightValidator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.height.setValidator(heightValidator)
        self.height.setText(str(round(self.imageFormat.height(), 2)))

        self.width.textEdited.connect(self.updateHeight)
        self.height.textEdited.connect(self.updateWidth)

        self.keepratio = QCheckBox('保持宽高比')
        if abs(self.imageFormat.width() / self.imageFormat.height() - self.imageRatio) < 0.001:
            self.keepratio.setChecked(True)
        else:
            self.keepratio.setChecked(False)

        # Button
        okButton = QPushButton("确定", self)
        okButton.clicked.connect(self.ok)
        cancelButton = QPushButton("取消", self)
        cancelButton.clicked.connect(self.cancel)

        # Layout
        layout = QGridLayout()

        layout.addWidget(widthLabel,0,0)
        layout.addWidget(self.width, 0, 1)

        layout.addWidget(heightLabel,1,0)
        layout.addWidget(self.height,1,1)

        layout.addWidget(self.keepratio, 2, 1)

        layout.addWidget(okButton,3,0)
        layout.addWidget(cancelButton, 3, 1)

        self.setWindowTitle("设置图片")
        self.setGeometry(300,300,200,100)
        self.setLayout(layout)

    def updateHeight(self):
        if self.width.text().strip() == '':
            return
        if not self.keepratio.isChecked():
            return
        height = round(float(self.width.text()) / self.imageRatio, 2)
        self.height.setText(str(height))

    def updateWidth(self):
        if self.height.text().strip() == '':
            return
        if not self.keepratio.isChecked():
            return
        width = round(float(self.height.text()) * self.imageRatio, 2)
        self.width.setText(str(width))

    @checkLock
    def ok(self):
        newWidth = float(self.width.text())
        newHeight = float(self.height.text())
        self.imageFormat.setWidth(newWidth)
        self.imageFormat.setHeight(newHeight)
        self.okClicked.emit(self.imageFormat)
        self.close()

    def cancel(self):
        self.close()


class CameraListDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self._parentWidget = parent
        self.localCamList: List[QCameraDevice] = list()
        self.webcamList: List[dict] = list()
        self.initCameraList(local=True, web=True)
        self.initUI()

    def initCameraList(self, local=False, web=False):
        if local:
            self.localCamList: List[QCameraDevice] = QMediaDevices.videoInputs()
        if web:
            self.webcamList: List[dict] = list(self._parentWidget._parentWidget.systemSetting.webcams.values())

    def initUI(self):
        self.setWindowTitle('选择摄像头')
        self.setWindowIcon(getIcon('camera'))

        toolbarLayoutWidget = QWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Policy.Fixed)
        toolbarLayoutWidget.setSizePolicy(sizePolicy)
        toobarLayout = QHBoxLayout(toolbarLayoutWidget)
        toobarLayout.setSpacing(0)
        webcamAddButton = QToolButton(self)
        webcamAddButton.setIcon(getIcon('webcamAdd'))
        webcamAddButton.setText('添加网络摄像头')
        webcamAddButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        webcamAddButton.clicked.connect(self.openAddCameraDialog)
        toobarLayout.addWidget(webcamAddButton)

        self.webcamRemoveButton = QToolButton(self)
        self.webcamRemoveButton.setIcon(getIcon('webcamRemove'))
        self.webcamRemoveButton.setText('删除网络摄像头')
        self.webcamRemoveButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.webcamRemoveButton.clicked.connect(self.removeWebcam)
        toobarLayout.addWidget(self.webcamRemoveButton)

        webcamRefreshButton = QToolButton(self)
        webcamRefreshButton.setIcon(getIcon('camRefresh'))
        webcamRefreshButton.setText('刷新摄像头列表')
        webcamRefreshButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        webcamRefreshButton.clicked.connect(lambda : self.refreshCameraComboBox(local=True, web=True))
        toobarLayout.addWidget(webcamRefreshButton)

        self.webcamButton = QToolButton(self)
        self.webcamButton.setText('使用网络摄像头')
        self.webcamButton.setIcon(getIcon('webcam'))
        self.webcamButton.clicked.connect(self.openWebcamDialog)
        self.webcamButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toobarLayout.addWidget(self.webcamButton)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toobarLayout.addWidget(spacer)

        cameraLabel = QLabel('选择一个摄像头')
        self.cameraCombox = QComboBox(self)
        self.cameraCombox.currentIndexChanged.connect(self.cameraSelectChanged)
        self.refreshCameraComboBox()

        self.takePhoto = QPushButton('拍照', self)
        self.cancelButton = QPushButton("取消", self)

        self.takePhoto.clicked.connect(self.openTakePhotoDialog)
        self.cancelButton.clicked.connect(self.close)

        contentLayoutWidget = QWidget(self)
        layout = QGridLayout(contentLayoutWidget)

        layout.addWidget(toolbarLayoutWidget, 0, 0, 1, 4)
        layout.addWidget(cameraLabel, 1, 0, 1, 1)
        layout.addWidget(self.cameraCombox, 1, 1, 1, 3)
        layout.addWidget(self.takePhoto, 2, 2)
        layout.addWidget(self.cancelButton, 2, 3)

        self.setGeometry(300, 300, 300, 100)
        mainLayout = QVBoxLayout(self)

        mainLayout.addWidget(toolbarLayoutWidget, Qt.AlignmentFlag.AlignLeft)
        mainLayout.addWidget(contentLayoutWidget)
        self.setLayout(mainLayout)

    def cameraSelectChanged(self, index):
        if index == -1:
            self.webcamRemoveButton.setEnabled(False)
            return
        camera = self.getCameraByIndex(index)
        if type(camera) == dict:
            self.webcamRemoveButton.setEnabled(True)
        else:
            self.webcamRemoveButton.setEnabled(False)


    def insertImageToEditor(self, image: QImage):
        self._parentWidget.dropImage(image)
        self.hide()

    def getCameraByIndex(self, index):
        if index >= len(self.localCamList):
            return self.webcamList[index - len(self.localCamList)]
        else:
            return self.localCamList[index]

    def openTakePhotoDialog(self):
        selectedIndex = self.cameraCombox.currentIndex()
        if selectedIndex >= len(self.localCamList):
            webcam = self.webcamList[selectedIndex - len(self.localCamList)]
            url = QUrl(webcam['address'])
            url.setUserName(webcam['user'])
            if len(webcam['user']) > 0:
                value, ok = QInputDialog.getText(self, '输入设备密码', "", QLineEdit.EchoMode.Password)
                if not ok:
                    return
                url.setPassword(value)
            tp = TakePhotoDialog(url.toString(), None, self)
        else:
            tp = TakePhotoDialog(self.cameraCombox.currentIndex(), self.localCamList[self.cameraCombox.currentIndex()], self)
        tp.takePhotoDone.connect(self.insertImageToEditor)
        tp.exec()
        tp.destroy()

    def openWebcamDialog(self):
        value, ok = QInputDialog.getText(self, "输入网络摄像头地址", "格式：http(s)://username:password@ip:port/path", QLineEdit.Normal,
                                         "")
        if ok:
            tp = TakePhotoDialog(value, None, self)
            tp.takePhotoDone.connect(self.insertImageToEditor)
            tp.exec()
            tp.destroy()

    def openAddCameraDialog(self):
        dialog = AddCameraDialog(self)
        dialog.exec()
        dialog.destroy()
        self.refreshCameraComboBox(local=False, web=True)

    def removeWebcam(self):
        camera:dict = self.getCameraByIndex(self.cameraCombox.currentIndex())
        settings:Settings = self._parentWidget._parentWidget.systemSetting
        settings.removeWebcam(camera['name'])
        settings.write()
        self.refreshCameraComboBox(local=False, web=True)

    def refreshCameraComboBox(self, local=False, web=False):
        self.initCameraList(local, web)
        self.cameraCombox.clear()
        for i, cameraDevice in enumerate(self.localCamList):
            text = "Local  %d: %s" % (i, cameraDevice.description())
            self.cameraCombox.addItem(text)

        for j, cameraDevice in enumerate(self.webcamList):
            url = QUrl(cameraDevice['address'])
            if url.port() == -1:
                urlText = url.host()
            else:
                urlText = "%s:%d" % (url.host(), url.port())
            text = "Web  %d: %s %s" % (j, cameraDevice['name'], urlText)
            self.cameraCombox.addItem(text)


class AddCameraDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self._parentWidget = parent

        self.initUI()

    def initUI(self):
        self.setWindowTitle('添加网络摄像头')
        self.setWindowIcon(getIcon('webcamAdd'))
        nameLabel = QLabel('设备名', self)
        self.nameInput = QLineEdit(self)
        ipLabel = QLabel('设备网络地址', self)
        self.ipInput = QLineEdit(self)
        userLabel = QLabel("用户名")
        self.userInput = QLineEdit()
        passwdLabel = QLabel("密码")
        self.passwdInput = QLineEdit()
        self.passwdInput.setEchoMode(QLineEdit.EchoMode.Password)

        okButton = QPushButton('保存', self)
        okButton.clicked.connect(self.save)
        cancelButton = QPushButton('取消', self)
        cancelButton.clicked.connect(self.close)

        layout = QGridLayout()
        index = -1

        index += 1
        layout.addWidget(nameLabel, index, 0)
        layout.addWidget(self.nameInput, index, 1)

        index += 1
        layout.addWidget(ipLabel, index, 0)
        layout.addWidget(self.ipInput, index, 1)

        index += 1
        layout.addWidget(userLabel, index, 0)
        layout.addWidget(self.userInput, index, 1)

        index += 1
        layout.addWidget(passwdLabel, index, 0)
        layout.addWidget(self.passwdInput, index, 1)

        index += 1
        layout.addWidget(okButton, index, 0)
        layout.addWidget(cancelButton, index, 1)

        self.setLayout(layout)

    def save(self):
        name = self.nameInput.text().strip()
        address = self.ipInput.text().strip()
        user = self.userInput.text().strip()
        passwd = self.passwdInput.text().strip()

        if len(name) == 0 or len(address) == 0:
            popup = QMessageBox(QMessageBox.Warning,
                                "参数错误",
                                "设备名和地址都不能未空",
                                QMessageBox.Ok,
                                self)
            popup.show()
            return

        if not address.startswith('http'):
            popup = QMessageBox(QMessageBox.Warning,
                                "参数错误",
                                "设备地址必须以http开头",
                                QMessageBox.Ok,
                                self)
            popup.show()
            return
        url = QUrl(address)
        if not url.isValid():
            popup = QMessageBox(QMessageBox.Warning,
                                "参数错误",
                                "设备地址不是一个有效的地址",
                                QMessageBox.Ok,
                                self)
            popup.show()
            return

        main = self._parentWidget._parentWidget._parentWidget
        settings: Settings = main.systemSetting
        if settings.isWebcamExists(name):
            popup = QMessageBox(QMessageBox.Warning,
                                "参数错误",
                                "设备名已存在",
                                QMessageBox.Ok,
                                self)
            popup.show()
            return

        settings.addWebcam(name, {
            'name': name,
            'address': address,
            'user': user,
            'passwd': ''
        })
        settings.write()
        self.close()



class CameraThread(QThread):
    updatePixmap = Signal(QPixmap)
    updateInfo = Signal(str)
    openCameraError = Signal(str)

    def __init__(self, cameraId:Union[int, str], cameraDevice:QCameraDevice, parent=None) -> None:
        super().__init__(parent)
        self.cameraId = cameraId
        self.cameraDevice = cameraDevice
        self.cap = None
        self.active = True
        self.stopped = False
        self.flip = False
        self.lock = QMutex()

    def run(self):
        if self.cap is None:

            infoList = []
            timeformat = '%Y/%m/%d %H:%M:%S'
            if type(self.cameraId) == str and self.cameraDevice is None:

                infoList.append('%s %s' % (time.strftime(timeformat), '正在打开摄像头...'))
                self.updateInfo.emit('\n'.join(infoList))
                self.cap = cv2.VideoCapture(self.cameraId)

            else:

                infoList.append('%s %s' % (time.strftime(timeformat), '正在打开摄像头...'))
                self.updateInfo.emit('\n'.join(infoList))
                self.cap = cv2.VideoCapture(self.cameraId)

                resolution = self.cameraDevice.photoResolutions()[0]

                infoList.append('%s %s' % (time.strftime(timeformat), '正在设置宽度...'))
                self.updateInfo.emit('\n'.join(infoList))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution.width())

                infoList.append('%s %s' % (time.strftime(timeformat), '正在设置高度...'))
                self.updateInfo.emit('\n'.join(infoList))
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution.height())

            infoList.append('%s %s' % (time.strftime(timeformat), '检查摄像头是否打开成功'))
            self.updateInfo.emit('\n'.join(infoList))

            ret, frame = self.getFrame()
            if ret:
                infoList.append('%s %s' % (time.strftime(timeformat), '打开摄像头完毕'))
                self.updateInfo.emit('\n'.join(infoList))
            else:
                infoList.append('%s %s' % (time.strftime(timeformat), '打开摄像头失败'))
                self.updateInfo.emit('\n'.join(infoList))
                msg = ''
                if type(self.cameraId) == str and self.cameraDevice is None:
                    msg = '无法打开摄像头，请检查设备地址、用户名和密码是否正确'
                else:
                    msg = '无法打开摄像头，请检查摄像头是否已连接'
                self.openCameraError.emit(msg)
            time.sleep(1)

        while True:

            if self.stopped:
                return

            if not self.active:
                time.sleep(0.1)
                continue

            ret, frame = self.getFrame()

            if ret:
                image = self.frameToImage(frame)
                qt_image = self.imageToQImage(image)
                pic = qt_image.scaled(640, 640, Qt.AspectRatioMode.KeepAspectRatio)
                pixmap = QPixmap.fromImage(pic)
                self.updatePixmap.emit(pixmap)
            else:
                time.sleep(0.1)

    def getFrame(self):
        try:
            self.lock.lock()
            return self.cap.read()
        finally:
            self.lock.unlock()

    def frameToImage(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return cv2.flip(image, 1) if self.flip else image

    def imageToQImage(self, image):
        return QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888)

    def stop(self):
        try:
            self.lock.lock()
            self.stopped = True
            self.cap.release()
            self.cap = None
        finally:
            self.lock.unlock()


class TakePhotoDialog(QDialog):

    takePhotoDone = Signal(QImage)

    def __init__(self,  cameraId:Union[int, str], cameraDevice:QCameraDevice, parent):
        QDialog.__init__(self, parent)
        self._parentWidget = parent
        self.cameraThread = CameraThread(cameraId, cameraDevice)
        self.initUI()
        self.cameraThread.start()

    def initUI(self):
        self.resize(800, 600)

        self.videoFlip = QCheckBox("镜像", self)
        self.videoFlip.stateChanged.connect(self.videoFlipChecked)

        self.takePhotoButton = QPushButton('拍照', self)
        self.takePhotoButton.clicked.connect(self.take)

        self.cameraOutput = QLabel(self)
        self.cameraThread.updatePixmap.connect(self.cameraOutput.setPixmap)
        self.cameraThread.updateInfo.connect(self.cameraOutput.setText)
        self.cameraThread.openCameraError.connect(self.showMsg)

        layout = QGridLayout(self)
        layout.addWidget(self.cameraOutput, 0, 1, 3, 4)
        layout.addWidget(self.videoFlip, 4, 2, 1, 1)
        layout.addWidget(self.takePhotoButton, 4, 3, 1, 1)
        self.setLayout(layout)

    def showMsg(self, msg:str):
        QMessageBox.critical(self, '错误', msg, QMessageBox.StandardButton.Ok)

    def videoFlipChecked(self):
        self.cameraThread.flip = self.videoFlip.isChecked()

    def take(self):
        self.cameraThread.active = False
        ret, frame = self.cameraThread.getFrame()
        if ret:
            cv2image = self.cameraThread.frameToImage(frame)
            qtImage = self.cameraThread.imageToQImage(cv2image)
            self.takePhotoDone.emit(qtImage)
            self.close()

    def closeEvent(self, event: QCloseEvent):
        if self.cameraThread is not None:
            self.cameraThread.stop()
        event.accept()