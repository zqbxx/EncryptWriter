#PYQT5 PyQt4’s QtGui module has been split into PyQt5’s QtGui, QtPrintSupport and QtWidgets modules

import re

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QDialog, QPushButton, QRadioButton, QTextEdit, QGridLayout

from settings import getIcon


class Find(QDialog):
    def __init__(self, parent = None):
        
        QDialog.__init__(self, parent)

        self.parent = parent

        self.lastStart = 0

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

    def find(self):

        # Grab the parent's text
        text = self.parent.text.toPlainText()

        # And the text to find
        query = self.findField.toPlainText()

        if self.normalRadio.isChecked():

            # Use normal string search to find the query from the
            # last starting position
            self.lastStart = text.find(query,self.lastStart + 1)

            # If the find() method didn't return -1 (not found)
            if self.lastStart >= 0:

                end = self.lastStart + len(query)
                
                self.moveCursor(self.lastStart,end)

            else:

                # Make the next search start from the begining again
                self.lastStart = 0
                
                self.parent.text.moveCursor(QTextCursor.End)

        else:

            # Compile the pattern
            pattern = re.compile(query)

            # The actual search
            match = pattern.search(text,self.lastStart + 1)

            if match:

                self.lastStart = match.start()
                
                self.moveCursor(self.lastStart,match.end())

            else:

                self.lastStart = 0
                
                # We set the cursor to the end if the search was unsuccessful
                self.parent.text.moveCursor(QTextCursor.End)

    def replace(self):

        # Grab the text cursor
        cursor = self.parent.text.textCursor()

        # Security
        if cursor.hasSelection():

            # We insert the new text, which will override the selected
            # text
            cursor.insertText(self.replaceField.toPlainText())

            # And set the new cursor
            self.parent.text.setTextCursor(cursor)

    def replaceAll(self):

        self.lastStart = 0

        self.find()

        # Replace and find until self.lastStart is 0 again
        while self.lastStart:
            self.replace()
            self.find()

    def moveCursor(self,start,end):

        # We retrieve the QTextCursor object from the parent's QTextEdit
        cursor = self.parent.text.textCursor()

        # Then we set the position to the beginning of the last match
        cursor.setPosition(start)

        # Next we move the Cursor by over the match and pass the KeepAnchor parameter
        # which will make the cursor select the the match's text
        cursor.movePosition(QTextCursor.Right,QTextCursor.KeepAnchor,end - start)

        # And finally we set this new cursor as the parent's 
        self.parent.text.setTextCursor(cursor)
