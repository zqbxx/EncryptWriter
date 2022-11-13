from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QDialog

from settings import getIcon


class WordCount(QDialog):
    def __init__(self,parent = None):
        QDialog.__init__(self, parent)

        self.parent = parent
         
        self.initUI()
 
    def initUI(self):

        self.setWindowIcon(getIcon('wordCount'))

        # Word count in selection
        currentLabel = QLabel("当前选中",self)
        currentLabel.setStyleSheet("font-weight:bold; font-size: 15px;")

        currentWordsLabel = QLabel("词: ", self)
        currentSymbolsLabel = QLabel("符号: ",self)
        
        self.currentWords = QLabel(self)
        self.currentSymbols = QLabel(self)

        # Total word/symbol count
        totalLabel = QLabel("总计",self)
        totalLabel.setStyleSheet("font-weight:bold; font-size: 15px;")

        totalWordsLabel = QLabel("词: ", self)
        totalSymbolsLabel = QLabel("符号: ",self)

        self.totalWords = QLabel(self)
        self.totalSymbols = QLabel(self)

        # Layout
        
        layout = QGridLayout(self)

        layout.addWidget(currentLabel,0,0)
        
        layout.addWidget(currentWordsLabel,1,0)
        layout.addWidget(self.currentWords,1,1)

        layout.addWidget(currentSymbolsLabel,2,0)
        layout.addWidget(self.currentSymbols,2,1)

        spacer = QWidget()
        spacer.setFixedSize(0,5)

        layout.addWidget(spacer,3,0)

        layout.addWidget(totalLabel,4,0)

        layout.addWidget(totalWordsLabel,5,0)
        layout.addWidget(self.totalWords,5,1)

        layout.addWidget(totalSymbolsLabel,6,0)
        layout.addWidget(self.totalSymbols,6,1)

        self.setWindowTitle("文字统计")
        self.setGeometry(300,300,200,200)
        self.setLayout(layout)

    def getText(self):

        # Get the text currently in selection
        text = self.parent.text.textCursor().selectedText()

        # Split the text to get the word count
        words = str(len(text.split()))

        # And just get the length of the text for the symbols
        # count
        symbols = str(len(text))

        self.currentWords.setText(words)
        self.currentSymbols.setText(symbols)

        # For the total count, same thing as above but for the
        # total text
        
        text = self.parent.text.toPlainText()

        words = str(len(text.split()))
        symbols = str(len(text))

        self.totalWords.setText(words)
        self.totalSymbols.setText(symbols)
