from PySide6.QtCore import Qt
from PySide6.QtGui import QTextTableFormat, QColor, QTextFrameFormat, QTextLength, QIntValidator
from PySide6.QtWidgets import QMessageBox, QDialog, QLabel, QSpinBox, QPushButton, QGridLayout, QTextEdit, QSlider, \
    QLineEdit

from ext.widgets import ColorButton
from settings import getIcon


class Table(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.parent:QTextEdit = parent
        self.currentTableFormat: QTextTableFormat = None
         
        self.initUI()
 
    def initUI(self):

        self.setWindowIcon(getIcon('table'))

        # Rows
        rowsLabel = QLabel("Rows: ",self)
        
        self.rows = QSpinBox(self)

        # Columns
        colsLabel = QLabel("Columns",self)
        
        self.cols = QSpinBox(self)

        # Cell spacing (distance between cells)
        spaceLabel = QLabel("Cell spacing",self)
        
        self.space = QSpinBox(self)

        # Cell padding (distance between cell and inner text)
        padLabel = QLabel("Cell padding",self)

        self.pad = QSpinBox(self)
        
        self.pad.setValue(10)

        bgColorLabel = QLabel("背景色", self)
        self.bgColorBtn = ColorButton(color=QColor(255, 255, 240))
        bgColorText = QLabel(self.bgColorBtn.color().name(), self)
        self.bgColorBtn.colorChanged.connect(lambda c: bgColorText.setText(c.name()))

        borderwidthLabel = QLabel("边框宽度", self)
        borderWidthValue = QLabel("1", self)
        self.borderwidth = QSlider()
        self.borderwidth.setValue(1)
        self.borderwidth.setSingleStep(1)
        self.borderwidth.setMaximum(10)
        self.borderwidth.setMinimum(0)
        self.borderwidth.setOrientation(Qt.Horizontal)
        self.borderwidth.setTickInterval(1)
        self.borderwidth.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.borderwidth.valueChanged.connect(lambda : borderWidthValue.setText(str(self.borderwidth.value())))

        topMarginLabel = QLabel("上边距", self)
        leftMarginLabel = QLabel("左边距", self)
        rightMarginLabel = QLabel("右边距", self)
        bottomMarginLabel = QLabel("下边距", self)

        marginEditors = [QLineEdit("20"), QLineEdit("20"), QLineEdit("20"), QLineEdit("20") ]
        for editor in marginEditors:
            validator = QIntValidator()
            validator.setRange(0, 300)
            editor.setValidator(validator)
            editor.setText("5")
        self.topMargin, self.leftMargin, self.rightMargin, self.bottomMargin = marginEditors

        # Button
        insertButton = QPushButton("Insert",self)
        insertButton.clicked.connect(self.insert)

        # Layout
        layout = QGridLayout()

        layout.addWidget(rowsLabel,0,0)
        layout.addWidget(self.rows,0,1)

        layout.addWidget(colsLabel,0,2)
        layout.addWidget(self.cols,0,3)

        layout.addWidget(padLabel,2,0)
        layout.addWidget(self.pad,2,1)
        
        layout.addWidget(spaceLabel,2,2)
        layout.addWidget(self.space,2,3)

        layout.addWidget(bgColorLabel, 4, 0)
        layout.addWidget(self.bgColorBtn, 4, 1,1,1)
        layout.addWidget(bgColorText, 4, 2)

        layout.addWidget(borderwidthLabel, 5, 0)
        layout.addWidget(borderWidthValue, 5, 1)
        layout.addWidget(self.borderwidth, 5, 2, 1, 2)

        layout.addWidget(topMarginLabel, 6, 0)
        layout.addWidget(self.topMargin, 6, 1)
        layout.addWidget(leftMarginLabel, 6, 2)
        layout.addWidget(self.leftMargin, 6, 3)
        layout.addWidget(bottomMarginLabel, 7, 0)
        layout.addWidget(self.bottomMargin, 7, 1)
        layout.addWidget(rightMarginLabel, 7, 2)
        layout.addWidget(self.rightMargin, 7, 3)

        layout.addWidget(insertButton,8,0,1,2)

        self.setWindowTitle("Insert Table")
        self.setGeometry(300,300,300,200)
        self.setLayout(layout)

    def setCurrentFormat(self, tableFormat: QTextTableFormat):
        self.currentTableFormat = tableFormat

    def updateValue(self):
        tableFormat = self.currentTableFormat
        self.pad.setValue(tableFormat.cellPadding())
        self.space.setValue(tableFormat.cellSpacing())
        self.borderwidth.setValue(tableFormat.border())
        self.topMargin.setText(str(tableFormat.topMargin()))
        self.leftMargin.setText(str(tableFormat.leftMargin()))
        self.rightMargin.setText(str(tableFormat.rightMargin()))
        self.bottomMargin.setText(str(tableFormat.bottomMargin()))

        self.bgColorBtn.setEnabled(False)
        self.rows.setEnabled(False)
        self.cols.setEnabled(False)

    def insert(self):

        isInsert = True if self.currentTableFormat is None else False

        cursor = self.parent.textCursor()

        # Get the configurations
        rows = self.rows.value()

        cols = self.cols.value()

        if (not rows or not cols) and isInsert:

            popup = QMessageBox(QMessageBox.Warning,
                                      "Parameter error",
                                      "Row and column numbers may not be zero!",
                                      QMessageBox.Ok,
                                      self)
            popup.show()

        else:

            padding = self.pad.value()

            space = self.space.value()

            # Set the padding and spacing
            fmt = QTextTableFormat() if self.currentTableFormat is None else self.currentTableFormat

            fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
            fmt.setBorderCollapse(True)
            fmt.setWidth(QTextLength(QTextLength.PercentageLength, 100))

            if self.pad.isEnabled():
                fmt.setCellPadding(self.pad.value())
            if self.space.isEnabled():
                fmt.setCellSpacing(self.space.value())
            if self.borderwidth.isEnabled():
                fmt.setBorder(self.borderwidth.value())
            if self.topMargin.isEnabled():
                fmt.setTopMargin(float(self.topMargin.text()))
            if self.leftMargin.isEnabled():
                fmt.setLeftMargin(float(self.leftMargin.text()))
            if self.rightMargin.isEnabled():
                fmt.setRightMargin(float(self.rightMargin.text()))
            if self.bottomMargin.isEnabled():
                fmt.setBottomMargin(float(self.bottomMargin.text()))

            if isInsert:
                cursor.insertTable(rows, cols, fmt)
                width = int(100 / cols)
                columnWidthConstraints = []
                for i in range(self.cols.value()):
                    columnWidthConstraints.append(QTextLength(QTextLength.PercentageLength, width))
                columnWidthConstraints[self.cols.value() - 1] = QTextLength(QTextLength.PercentageLength, 100 - width * (cols - 1))
                fmt.setColumnWidthConstraints(columnWidthConstraints)
                cursor.currentTable().setFormat(fmt)
            else:
                cursor.currentTable().setFormat(fmt)

            if self.bgColorBtn.isEnabled():
                t = cursor.currentTable()
                for i in range(t.rows()):
                    for j in range(t.columns()):
                        cell = t.cellAt(i, j)
                        cellFormat = cell.format()
                        cellFormat.setBackground(self.bgColorBtn.color())
                        cell.setFormat(cellFormat)

            self.close()
