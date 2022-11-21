from time import strftime

from PySide6.QtWidgets import QDialog, QComboBox, QPushButton, QGridLayout

from .settings import getIcon


class DateTime(QDialog):
    def __init__(self,parent = None):
        QDialog.__init__(self, parent)

        self._parentWidget = parent

        self.formats = ["%Y-%m-%d %H:%M:%S",
                        "%Y/%m/%d %H:%M:%S",
                        "%Y/%m/%d",
                        "%H:%M:%S",
                        "%H:%M",
                        "%x",
                        "%X",
                        "%A, %d. %B %Y %H:%M",
                        "%A, %d. %B %Y",
                        "%d. %B %Y %H:%M",
                        "%d.%m.%Y %H:%M",
                        "%d. %B %Y",
                        "%d %m %Y",
                        "%d.%m.%Y",]
         
        self.initUI()
 
    def initUI(self):

        self.setWindowIcon(getIcon('dateTime'))
        self.box = QComboBox(self)

        for i in self.formats:
            self.box.addItem(strftime(i))

        insert = QPushButton("Insert",self)
        insert.clicked.connect(self.insert)
 
        cancel = QPushButton("Cancel",self)
        cancel.clicked.connect(self.close)
 
        layout = QGridLayout()

        layout.addWidget(self.box,0,0,1,2)
        layout.addWidget(insert,1,0)
        layout.addWidget(cancel,1,1)
        
        self.setGeometry(300,300,400,80)
        self.setWindowTitle("插入时间和日期")
        self.setLayout(layout)

    def insert(self):

        # Grab cursor
        cursor = self._parentWidget.text.textCursor()

        datetime = strftime(self.formats[self.box.currentIndex()])

        # Insert the comboBox's current text
        cursor.insertText(datetime)

        # Close the window
        self.close()
