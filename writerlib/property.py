from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QPushButton, QGridLayout, QLabel, QLineEdit, QCheckBox

from .textedit import TextEdit
from .settings import getIcon
from .widgets import checkLock


class PropertyEditor(QDialog):

    propertySaved = Signal()

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self._parentWidget = parent
        self.initUI()

    def initUI(self):

        self.setWindowIcon(getIcon('property'))
        self.setWindowTitle("文档属性")

        layout = QGridLayout()
        self.inputs: List[QLineEdit] = list()
        properties = self._parentWidget.documentProperty
        for i, (k, v) in enumerate(properties.items()):

            label = QLabel(v['display'])
            input = QLineEdit(v['value'])
            input.setProperty('name', k)
            if v['internal']:
                input.setEnabled(False)
            else:
                self.inputs.append(input)
            layout.addWidget(label, i, 0)
            layout.addWidget(input, i, 1, 1, 3)

        self.encryptDocumentCheckBox = QCheckBox('保存为加密文档')
        self.encryptDocumentCheckBox.setChecked(self._parentWidget.isEncryptDocument)
        layout.addWidget(self.encryptDocumentCheckBox, len(properties.items()), 1, 1, 2)

        okButton = QPushButton("确定")
        okButton.clicked.connect(self.ok)
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(self.cancel)

        layout.addWidget(okButton, len(properties.items())+1, 2)
        layout.addWidget(cancelButton, len(properties.items())+1, 3)

        self.setGeometry(300, 300, 450, 100)
        self.setLayout(layout)

    @checkLock
    def ok(self):
        for input in self.inputs:
            name = input.property('name')
            value = input.text()
            self._parentWidget.documentProperty[name]['value'] = value
        self._parentWidget.isEncryptDocument = self.encryptDocumentCheckBox.isChecked()
        self.propertySaved.emit()
        self.close()

    def cancel(self):
        self.close()