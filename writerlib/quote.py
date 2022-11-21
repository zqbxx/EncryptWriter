from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QTextFrameFormat, QIntValidator, QColor, QTextCursor
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QGridLayout, QPushButton, QTextEdit

from .settings import getIcon
from .widgets import getBorderWidgets, getBackgroundColorWidgets, getMarginWidgets, checkLock


class Quote(QDialog):

    okClicked = Signal()

    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self._parentWidget:QTextEdit = parent
        self.currentQuoteFormat:QTextFrameFormat = None
        self.initUI()

    def initUI(self):

        self.setWindowIcon(getIcon('quote'))
        self.setWindowTitle("设置引用格式")
        borderWidthLabel, borderWidthValue, self.borderWidth = getBorderWidgets(1)
        borderWidthValue.setAlignment(Qt.AlignmentFlag.AlignRight)

        bgColorLabel, bgColorText, self.bgColorBtn = getBackgroundColorWidgets(QColor(255, 255, 240))

        marginLabels, marginEditors = getMarginWidgets(5, 5, 5, 5)
        topMarginLabel, rightMarginLabel, bottomMarginLabel, leftMarginLabel = marginLabels
        self.topMarginEditor, self.rightMarginEditor, self.bottomMarginEditor, self.leftMarginEditor = marginEditors

        paddingLabel = QLabel('内边距')
        self.paddingEditor = QLineEdit("5")
        self.paddingEditor.setValidator(QIntValidator(0, 300))

        layout = QGridLayout()

        layout.addWidget(bgColorLabel, 0, 0)
        layout.addWidget(self.bgColorBtn, 0, 1)
        layout.addWidget(bgColorText, 0, 2, 1, 2)

        layout.addWidget(borderWidthLabel, 1, 0)
        layout.addWidget(borderWidthValue, 1, 1)
        layout.addWidget(self.borderWidth, 1, 2, 1,2)

        layout.addWidget(topMarginLabel, 2, 0)
        layout.addWidget(self.topMarginEditor, 2, 1)
        layout.addWidget(leftMarginLabel, 2, 2)
        layout.addWidget(self.leftMarginEditor, 2, 3)
        layout.addWidget(bottomMarginLabel, 3, 0)
        layout.addWidget(self.bottomMarginEditor, 3, 1)
        layout.addWidget(rightMarginLabel, 3, 2)
        layout.addWidget(self.rightMarginEditor, 3, 3)

        layout.addWidget(paddingLabel, 4, 0, 1, 1)
        layout.addWidget(self.paddingEditor, 4, 1, 1, 1)

        okButton = QPushButton("确定")
        okButton.clicked.connect(self.ok)
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(self.cancel)

        layout.addWidget(okButton, 5, 0, 1, 2)
        layout.addWidget(cancelButton, 5, 2, 1, 2)

        self.setGeometry(300, 300, 200, 100)
        self.setLayout(layout)

    def setCurrentFormat(self, frameFormat: QTextFrameFormat):
        self.currentQuoteFormat = frameFormat

    def updateValue(self):
        self.borderWidth.setValue(self.currentQuoteFormat.border())
        self.bgColorBtn.setColor(self.currentQuoteFormat.background().color())
        self.topMarginEditor.setText(str(self.currentQuoteFormat.topMargin()))
        self.rightMarginEditor.setText(str(self.currentQuoteFormat.rightMargin()))
        self.bottomMarginEditor.setText(str(self.currentQuoteFormat.bottomMargin()))
        self.leftMarginEditor.setText(str(self.currentQuoteFormat.leftMargin()))
        self.paddingEditor.setText(str(self.currentQuoteFormat.padding()))

    @checkLock
    def ok(self):

        isInsert = True if self.currentQuoteFormat is None else False

        cursor: QTextCursor = self._parentWidget.textCursor()
        frameFormat = QTextFrameFormat() if isInsert else self.currentQuoteFormat
        frameFormat.setBorder(self.borderWidth.value())
        frameFormat.setBackground(self.bgColorBtn.color())
        frameFormat.setBorderBrush(Qt.BrushStyle.SolidPattern)
        frameFormat.setLeftMargin(float(self.leftMarginEditor.text()))
        frameFormat.setRightMargin(float(self.rightMarginEditor.text()))
        frameFormat.setTopMargin(float(self.topMarginEditor.text()))
        frameFormat.setBottomMargin(float(self.bottomMarginEditor.text()))
        frameFormat.setPadding(float(self.paddingEditor.text()))
        cursor.insertFrame(frameFormat) if isInsert else cursor.currentFrame().setFormat(frameFormat)
        self.close()

    def cancel(self):
        self.close()