import os
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import QDialog, QLabel, QSlider, QLineEdit, QMessageBox

from writerlib.textedit import TextEdit


class ColorButton(QtWidgets.QPushButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    '''

    colorChanged = Signal(QColor)

    def __init__(self, *args, color:QColor=None, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self._default = color
        self.pressed.connect(self.onColorPicker)

        # Set the initial/default state.
        self.setColor(self._default)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("ColorButton {background-color: %s;}" % self._color.name())
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        dlg = QtWidgets.QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(self._color)

        if dlg.exec_():
            self.setColor(dlg.currentColor())

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.setColor(self._default)

        return super(ColorButton, self).mousePressEvent(e)


def getBackgroundColorWidgets(backgourndColor: QColor) -> [QLabel, QLabel, ColorButton]:
    bgColorLabel = QLabel("背景色")
    bgColorBtn = ColorButton(color=backgourndColor)
    bgColorText = QLabel(bgColorBtn.color().name())
    bgColorBtn.colorChanged.connect(lambda c: bgColorText.setText(c.name()))
    return bgColorLabel, bgColorText, bgColorBtn


def getBorderWidgets(borderWidth: int) -> [QLabel, QLabel, QSlider]:
    borderwidthLabel = QLabel("边框宽度")
    borderWidthValue = QLabel(str(borderWidth))
    borderwidth = QSlider()
    borderwidth.setValue(borderWidth)
    borderwidth.setSingleStep(1)
    borderwidth.setMaximum(10)
    borderwidth.setMinimum(0)
    borderwidth.setOrientation(Qt.Horizontal)
    borderwidth.setTickInterval(1)
    borderwidth.setTickPosition(QSlider.TickPosition.TicksAbove)
    borderwidth.setValue(borderWidth)
    borderwidth.valueChanged.connect(lambda: borderWidthValue.setText(str(borderwidth.value())))
    return borderwidthLabel, borderWidthValue, borderwidth


def getMarginWidgets(topMargin: int, rightMargin: int, bottomMargin: int, leftMargin: int)-> [List[QLabel], List[QLineEdit]]:

    marginLabels = [QLabel("上边距"), QLabel("右边距"), QLabel("下边距"), QLabel("左边距")]
    marginEditors = [QLineEdit(str(topMargin)), QLineEdit(str(rightMargin)), QLineEdit(str(bottomMargin)), QLineEdit(str(leftMargin))]
    for editor in marginEditors:
        validator = QIntValidator()
        validator.setRange(0, 300)
        editor.setValidator(validator)

    return marginLabels, marginEditors


#TODO QWidgetAction


def checkLock(callback):
    def f(*args, **kwargs):
        self = args[0]

        parent = None

        if '_parentWidget' in self.__dict__:
            parent = self._parentWidget
        elif 'parent' in self.__dict__:
            try:
                parent = self.parent
            except:
                parent = self.parent()
        else:
            return None

        if isinstance(parent, TextEdit):
            parent = parent._parentWidget

        if parent.isDocumentLocked():
            QMessageBox.warning(parent, '警告', '锁定状态无法进行操作')
            return None
        r = callback(*args, **kwargs)
        return r
    return f

def checkLockFunc(parent):
    if parent.isDocumentLocked():
        QMessageBox.warning(parent, '警告', '锁定状态无法进行操作')
        return False
    return True