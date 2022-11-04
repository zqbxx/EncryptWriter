import base64
from pathlib import Path
from typing import Optional

import PySide6.QtCore
from PySide6 import QtCore, QtGui
from PySide6.QtGui import QImage, QTextImageFormat
from PySide6.QtWidgets import QTextEdit, QApplication
from io import BytesIO

import imghdr


class TextEdit(QTextEdit):

    def dropEvent(self, e: PySide6.QtGui.QDropEvent) -> None:
        source = e.mimeData()
        if source.hasImage() or source.hasUrls():
            self.insertRichContentFromMimeData(source)
            return
        else:
            return super().dropEvent(e)

    def canInsertFromMimeData(self, source: PySide6.QtCore.QMimeData) -> bool:
        return source.hasImage() or source.hasUrls() or super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source: PySide6.QtCore.QMimeData) -> None:
        if not self.insertRichContentFromMimeData(source):
            return super().insertFromMimeData(source)

    def insertRichContentFromMimeData(self, source: PySide6.QtCore.QMimeData) -> None:
        if source.hasImage():
            img = source.imageData()
            self.dropImage(img)
            return True
        elif source.hasUrls():
            for u in source.urls():
                if u.isLocalFile():
                    i = QImage(u.toLocalFile())
                    self.dropImage(i)
            return True
        return False

    def dropImage(self, image: QImage):
        image_bytes = self.qImageToBytes(image)
        self.insertImageInFile(image_bytes)

    def qImageToBytes(self, image: QImage):
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        bio = BytesIO(ba)
        return bio.getvalue()

    def getImageType(self, image_bytes):
        f = BytesIO()
        f.write(image_bytes)
        f.seek(0)
        imgType = imghdr.what(f)
        f.close()
        return imgType

    def insertImageInFile(self, image_bytes):
        imgType = self.getImageType(image_bytes)
        base64text = "".join(['data:image/', imgType, ';base64,', base64.b64encode(image_bytes).decode('utf-8')])
        imageFormat = QTextImageFormat()
        imageFormat.setName(base64text)
        image = QImage()
        image.loadFromData(image_bytes)
        imageFormat.setWidth(image.width())
        imageFormat.setHeight(image.height())
        self.textCursor().insertImage(imageFormat)



