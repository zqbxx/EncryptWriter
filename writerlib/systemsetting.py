from PySide6.QtWidgets import QDialog, QLabel, QSpinBox, QCheckBox, QGridLayout, QPushButton, QMessageBox
from keymanager.key import set_key_timeout

from .settings import getIcon
from .widgets import checkLock


class SysSettingEditor(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self.parent = parent
        self.initUI()

    def initUI(self):

        self.setWindowIcon(getIcon('sysSetting'))
        self.setWindowTitle('系统设置')

        timeoutLabel = QLabel('密钥超时时间(秒)')
        self.timeoutInput = QSpinBox(self)
        self.timeoutInput.setRange(1, 1000)
        self.timeoutInput.setValue(self.parent.systemSetting.keyTimeout)

        self.autoLockDoc = QCheckBox('密钥超时后锁定文档', self)
        self.autoLockDoc.setChecked(self.parent.systemSetting.autoLockDoc)
        self.resetTimeoutOnSelect = QCheckBox('选择文本、光标位置变化时重置超时时间', self)
        self.resetTimeoutOnSelect.setChecked(self.parent.systemSetting.resetTimeoutOnSelect)

        layout = QGridLayout()
        rowIndex = 0
        layout.addWidget(timeoutLabel, rowIndex, 0)
        layout.addWidget(self.timeoutInput, rowIndex, 1)

        rowIndex += 1
        layout.addWidget(self.autoLockDoc, rowIndex, 0, 1, 2)

        rowIndex += 1
        layout.addWidget(self.resetTimeoutOnSelect, rowIndex, 0, 1, 2)

        self.buttonOk = QPushButton('保存')
        self.buttonOk.clicked.connect(self.ok)
        self.buttonCancel = QPushButton('取消')
        self.buttonCancel.clicked.connect(self.cancel)

        rowIndex += 1
        layout.addWidget(self.buttonOk, rowIndex, 0)
        layout.addWidget(self.buttonCancel, rowIndex, 1)

        self.setGeometry(300, 300, 200, 100)
        self.setLayout(layout)

    @checkLock
    def ok(self):
        self.parent.systemSetting.keyTimeout = self.timeoutInput.value()
        self.parent.systemSetting.autoLockDoc = self.autoLockDoc.isChecked()
        self.parent.systemSetting.resetTimeoutOnSelect = self.resetTimeoutOnSelect.isChecked()
        self.parent.systemSetting.write()
        set_key_timeout(self.parent.systemSetting.keyTimeout)
        self.close()

    def cancel(self):
        self.close()