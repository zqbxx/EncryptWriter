import base64
import copy
from datetime import datetime
from pathlib import Path
from time import strftime, gmtime
from typing import Optional, Set, List

import PySide6.QtCore
from PySide6 import QtCore, QtGui
from PySide6.QtGui import QImage, QTextImageFormat, QTextCursor, Qt, QCursor, QTextTable, QTextTableCell
from PySide6.QtWidgets import QTextEdit, QApplication
from io import BytesIO

import imghdr

from ext.doc import DocFile, DocInfoBlock, DocBody, DocHead
from settings import document_properties


class Selection:

    def __init__(self, start=0, end=0):
        self.start = start
        self.end = end

    def __str__(self):
        return 'start: ' + str(self.start) + ' end: ' + str(self.end)


class TextEdit(QTextEdit):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget]) -> None:
        super().__init__(parent)
        self.documentProperty = copy.deepcopy(document_properties)
        self.addCreateTime()
        self.encryptDocument = False

    def mouseMoveEvent(self, e: PySide6.QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(e)
        # TODO 改变鼠标形状
        # cursor = self.cursorForPosition(e.pos())
        # format = cursor.charFormat()
        # if format.isImageFormat():
        #     self.viewport().setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # else:
        #     self.viewport().setCursor(QCursor(Qt.CursorShape.IBeamCursor))

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

    def getSelection(self) -> Selection:
        cursor = self.textCursor()
        selection = Selection()
        if cursor.hasSelection():
            selection.start = cursor.selectionStart()
            selection.end = cursor.selectionEnd()
        return selection

    def setSelection(self, selection: Selection):
        if selection.start != -1 and selection.end != -1:
            cursor = self.textCursor()
            cursor.setPosition(selection.start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(selection.end, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)

    def getSelectedCellCoordinate(self, cursor:QTextCursor=None):
        # qt实现了selectedTableCells方法，但是pyside6中没有
        firstRow = -1
        firstColumn = -1
        numRows = -1
        numColumns = -1
        if cursor is None:
            cursor = self.textCursor()
        table = cursor.currentTable()
        if table:
            selectStart = cursor.selectionStart()
            selectEnd = cursor.selectionEnd()
            selectStartCell = table.cellAt(selectStart)
            selectEndCell = table.cellAt(selectEnd)
            firstRow = selectStartCell.row()
            firstColumn = selectStartCell.column()
            numRows = selectEndCell.row() + selectEndCell.rowSpan() - firstRow
            numColumns = selectEndCell.column() + selectEndCell.columnSpan() - firstColumn
        return firstRow, firstColumn, numRows, numColumns

    def getTableCells(self, t:QTextTable, firstRow, firstColumn, numRows, numColumns):
        cells:List[List[QTextTableCell]] = list()
        for rowIndex in range(firstRow, firstRow + numRows):
            row:List[QTextTableCell] = list()
            cells.append(row)
            for colIndex in range(firstColumn, firstColumn + numColumns):
                cell = t.cellAt(rowIndex, colIndex)
                row.append(cell)
        return cells

    def docfromBytes(self, fileData:bytes) -> (str, dict):

        docFile = DocFile.fromBytes(fileData)

        properties = {}
        for block in docFile.docInfoBlock:
            properties[block.name.decode('utf-8')] = block.value.decode('utf-8')

        html = docFile.docBody.content.decode('utf-8')

        return html, properties

    def docToBytes(self, html: str, properties:dict) -> bytes:

        df = DocFile()

        docBody = DocBody()
        docBody.content = html.encode('utf-8')

        infoList:List[DocInfoBlock] = list()
        for name, value in properties.items():
            block = DocInfoBlock()
            block.name = name.encode('utf-8')
            block.value = value.encode('utf-8')
            infoList.append(block)

        head = DocHead()
        head.docBodyLen = len(docBody.content)
        head.docType = DocHead.DocType.Writer
        head.docInfoBlockLen = [i.getByteLen() for i in infoList]

        df.docHead = head
        df.docBody = docBody
        df.docInfoBlock = infoList

        return df.toByteIO().getvalue()

    def updateEditTime(self):
        dt = datetime.now()
        self.documentProperty['editDatetime']['value'] = dt.strftime('%Y-%m-%d %H:%M:%S.%f') + ' ' + strftime('%z %Z', gmtime())

    def addCreateTime(self):
        dt = datetime.now()
        self.documentProperty['createDatetime']['value'] = dt.strftime('%Y-%m-%d %H:%M:%S.%f') + ' ' + strftime('%z %Z', gmtime())

    @staticmethod
    def documentPropertyToDict(dp: dict):
        result: dict = dict()
        for k, v in dp.items():
            result[k] = v['value']
        return result

    @staticmethod
    def dictToDocumentProperty(d:dict, documentProperty:dict):
        for k, v in d.items():
            documentProperty[k]['value'] = v
        return documentProperty