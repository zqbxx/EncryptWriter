import base64

from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator, QImage, QTextImageFormat
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QGridLayout, QLineEdit, QCheckBox

from settings import getIcon


class Image(QDialog):

    okClicked = Signal(QTextImageFormat)

    def __init__(self, imageFormat:QTextImageFormat, parent = None):
        QDialog.__init__(self, parent)

        self.parent = parent
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

        self.width.textEdited.connect(lambda: self.height.setText(str(round(float(self.width.text()) / self.imageRatio, 2))) if self.keepratio.isChecked() else None)
        self.height.textEdited.connect(lambda: self.width.setText(str(round(float(self.height.text()) * self.imageRatio,2))) if self.keepratio.isChecked() else None)

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

    def ok(self):
        newWidth = float(self.width.text())
        newHeight = float(self.height.text())
        self.imageFormat.setWidth(newWidth)
        self.imageFormat.setHeight(newHeight)
        self.okClicked.emit(self.imageFormat)
        self.close()

    def cancel(self):
        self.close()