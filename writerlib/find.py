import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QDialog, QPushButton, QRadioButton, QTextEdit, QGridLayout, QMessageBox

from .settings import getIcon
from .textedit import Selection, TextEdit
from .widgets import checkLock


class Find(QDialog):
    def __init__(self, parent = None):
        
        QDialog.__init__(self, parent)

        self.parentWidget = parent

        self.lastStart = 0
        self.lastSearchResult = Selection(-1, -1)

        self.initUI()
 
    def initUI(self):

        self.setWindowIcon(getIcon('find'))

        # Button to search the document for something
        findButton = QPushButton("查找",self)
        findButton.clicked.connect(self.find)

        # Button to replace the last finding
        replaceButton = QPushButton("替换",self)
        replaceButton.clicked.connect(self.replace)

        # Button to remove all findings
        allButton = QPushButton("替换所有",self)
        allButton.clicked.connect(self.replaceAll)

        # Normal mode - radio button
        self.normalRadio = QRadioButton("普通",self)

        # Regular Expression Mode - radio button
        regexRadio = QRadioButton("正则",self)

        # The field into which to type the query
        self.findField = QTextEdit(self)
        self.findField.resize(250,50)

        # The field into which to type the text to replace the
        # queried text
        self.replaceField = QTextEdit(self)
        self.replaceField.resize(250,50)
        
        layout = QGridLayout()

        layout.addWidget(self.findField,1,0,1,4)
        layout.addWidget(self.normalRadio,2,2)
        layout.addWidget(regexRadio,2,3)
        layout.addWidget(findButton,2,0,1,2)
        
        layout.addWidget(self.replaceField,3,0,1,4)
        layout.addWidget(replaceButton,4,0,1,2)
        layout.addWidget(allButton,4,2,1,2)

        self.setGeometry(300,300,360,250)
        self.setWindowTitle("查找和替换")
        self.setLayout(layout)

        # By default the normal mode is activated
        self.normalRadio.setChecked(True)

    @checkLock
    def find(self):

        # Grab the parent's text
        text = self.parentWidget.text.toPlainText()
        textEdit: TextEdit = self.parentWidget.text
        document = textEdit.document()

        query = self.findField.toPlainText()

        currentSelection = textEdit.getSelection()
        if self.lastStart == -1:
            self.lastStart = 0
        elif currentSelection == self.lastSearchResult:
            self.lastStart = currentSelection.end
        else:
            self.lastStart = currentSelection.start

        if self.normalRadio.isChecked():
            cursor = document.find(query, self.lastStart)
        else:
            cursor = document.find(QRegularExpression(query), self.lastStart)

        selection = Selection(cursor.selectionStart(), cursor.selectionEnd())
        self.lastStart = cursor.selectionEnd()

        if selection.start == -1 and selection.end == -1:
            QMessageBox.information(self, '信息', '已搜索到文档末尾，没有找到更多的搜索结果')
            textEdit.setSelection(Selection(0, 0))
            self.lastStart = -1
        else:
            textEdit.setSelection(selection)
            self.lastStart = selection.end

        self.lastSearchResult = selection

    @checkLock
    def replace(self):

        # Grab the text cursor
        cursor:QTextCursor = self.parentWidget.text.textCursor()

        # Security
        if cursor.hasSelection():

            selection = Selection(cursor.selectionStart(), cursor.selectionEnd())
            if selection == self.lastSearchResult:
                cursor.insertText(self.replaceField.toPlainText())
            return

    @checkLock
    def replaceAll(self):

        self.lastStart = 0

        self.find()

        while self.lastStart != -1:
            self.replace()
            self.find()

    @checkLock
    def moveCursor(self,start,end):

        # We retrieve the QTextCursor object from the parent's QTextEdit
        cursor = self.parentWidget.text.textCursor()

        # Then we set the position to the beginning of the last match
        cursor.setPosition(start)

        # Next we move the Cursor by over the match and pass the KeepAnchor parameter
        # which will make the cursor select the the match's text
        cursor.movePosition(QTextCursor.Right,QTextCursor.KeepAnchor,end - start)

        # And finally we set this new cursor as the parent's 
        self.parentWidget.text.setTextCursor(cursor)
