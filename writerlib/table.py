from functools import partial
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextTableFormat, QColor, QTextFrameFormat, QTextLength, QIntValidator, QTextCursor, QAction
from PySide6.QtWidgets import QMessageBox, QDialog, QLabel, QSpinBox, QPushButton, QGridLayout, QTextEdit, QSlider, \
    QLineEdit, QToolButton, QColorDialog

from .settings import getIcon
from .textedit import TextEdit
from .widgets import ColorButton, checkLock, checkLockFunc


class TableEditor(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.parentWidget: QTextEdit = parent
        self.currentTableFormat: QTextTableFormat = None

        self.initUI()

    def initUI(self):

        self.setWindowIcon(getIcon('table'))

        # Rows
        rowsLabel = QLabel("行", self)

        self.rows = QSpinBox(self)
        self.rows.setValue(6)

        # Columns
        colsLabel = QLabel("列", self)

        self.cols = QSpinBox(self)
        self.cols.setValue(4)

        # Cell spacing (distance between cells)
        spaceLabel = QLabel("单元格间距", self)

        self.space = QSpinBox(self)

        # Cell padding (distance between cell and inner text)
        padLabel = QLabel("内边距", self)

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
        self.borderwidth.valueChanged.connect(lambda: borderWidthValue.setText(str(self.borderwidth.value())))

        topMarginLabel = QLabel("上边距", self)
        leftMarginLabel = QLabel("左边距", self)
        rightMarginLabel = QLabel("右边距", self)
        bottomMarginLabel = QLabel("下边距", self)

        marginEditors = [QLineEdit("20"), QLineEdit("20"), QLineEdit("20"), QLineEdit("20")]
        for editor in marginEditors:
            validator = QIntValidator()
            validator.setRange(0, 300)
            editor.setValidator(validator)
            editor.setText("5")
        self.topMargin, self.leftMargin, self.rightMargin, self.bottomMargin = marginEditors

        # Button
        insertButton = QPushButton("插入", self)
        insertButton.clicked.connect(self.insert)

        # Layout
        layout = QGridLayout()

        layout.addWidget(rowsLabel, 0, 0)
        layout.addWidget(self.rows, 0, 1)

        layout.addWidget(colsLabel, 0, 2)
        layout.addWidget(self.cols, 0, 3)

        layout.addWidget(padLabel, 2, 0)
        layout.addWidget(self.pad, 2, 1)

        layout.addWidget(spaceLabel, 2, 2)
        layout.addWidget(self.space, 2, 3)

        layout.addWidget(bgColorLabel, 4, 0)
        layout.addWidget(self.bgColorBtn, 4, 1, 1, 1)
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

        layout.addWidget(insertButton, 8, 0, 1, 2)

        self.setWindowTitle("插入表格")
        self.setGeometry(300, 300, 300, 200)
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

        self.bgColorBtn.setEnabled(True)
        self.rows.setEnabled(False)
        self.cols.setEnabled(False)

    @checkLock
    def insert(self):

        isInsert = True if self.currentTableFormat is None else False

        cursor: QTextCursor = self.parentWidget.textCursor()

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
            fmt = QTextTableFormat() if isInsert else self.currentTableFormat

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

            self.parentWidget.textCursor().beginEditBlock()
            if isInsert:
                cursor.insertTable(rows, cols, fmt)
            else:
                cursor.currentTable().setFormat(fmt)
            self.parentWidget.textCursor().endEditBlock()

            try:
                self.parentWidget.textCursor().joinPreviousEditBlock()
                if isInsert:
                    width = int(100 / cols)
                    columnWidthConstraints = []
                    for i in range(self.cols.value()):
                        columnWidthConstraints.append(QTextLength(QTextLength.Type.PercentageLength, width))
                    columnWidthConstraints[self.cols.value() - 1] = QTextLength(QTextLength.Type.PercentageLength,
                                                                                100 - width * (cols - 1))
                    fmt.setColumnWidthConstraints(columnWidthConstraints)
                    cursor.currentTable().setFormat(fmt)

                if self.bgColorBtn.isEnabled():
                    t = cursor.currentTable()
                    for i in range(t.rows()):
                        for j in range(t.columns()):
                            cell = t.cellAt(i, j)
                            cellFormat = cell.format()
                            cellFormat.setBackground(self.bgColorBtn.color())
                            cell.setFormat(cellFormat)
            finally:
                self.parentWidget.textCursor().endEditBlock()

            self.close()


class ColumnEditor(QDialog):

    lenType = 'lenType'

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.parentWidget: QTextEdit = parent
        self.initUI()

    def initUI(self):
        self.setWindowIcon(getIcon('tableColumn'))

        t = self.parentWidget.textCursor().currentTable()
        columns: List[QTextLength] = t.format().columnWidthConstraints()
        typeNames = {
            QTextLength.Type.PercentageLength: ['%', 'tabColPerWidth'],
            QTextLength.Type.FixedLength: ['px', 'tabColFixWidth'],
            QTextLength.Type.VariableLength: ['可变', 'tabColVarWidth']
        }
        actionIndex = 0

        layout = QGridLayout()
        self.columLength = []
        self.columType = []
        for index, column in enumerate(columns):

            length = column.rawValue()
            effectiveLength = column.value(1000000)
            type = column.type()
            columnLabel = QLabel('列 ' + str(actionIndex+1))
            valueInput = QLineEdit()
            valueInput.setText(str(length))
            toolButton = QToolButton()
            toolButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            self.columLength.append(valueInput)
            self.columType.append(toolButton)
            currentType = {}
            actions = []

            for actionIndex, (name, (value, icon)) in enumerate(typeNames.items()):
                action = QAction(getIcon(icon), value)
                action.setProperty(self.lenType, name)
                action.triggered.connect(partial(ColumnEditor.typeChanged,
                                                 action=action,
                                                 lineEdit=valueInput,
                                                 toolButton=toolButton))
                toolButton.addAction(action)
                actions.append(action)

                if name == type:
                    currentType = {'name': name, 'value': value, 'index': actionIndex}

            toolButton.setDefaultAction(actions[currentType['index']])
            valueInput.setProperty(self.lenType, currentType['value'])

            layout.addWidget(columnLabel, index, 0, 1, 1)
            layout.addWidget(valueInput, index, 1, 1, 2)
            layout.addWidget(toolButton, index, 3, 1, 1)

        insertButton = QPushButton("保存", self)
        insertButton.clicked.connect(self.save)

        layout.addWidget(insertButton, len(columns), 2, 1, 2)

        self.setWindowTitle("修改列宽")
        self.setGeometry(300, 300, 300, 200)
        self.setLayout(layout)

    @checkLock
    def save(self):
        t = self.parentWidget.textCursor().currentTable()

        format = t.format()
        if format.isTableFormat():
            print('table!')
        columns: List[QTextLength] = []
        for tb, le in zip(self.columType, self.columLength):
            type:QToolButton = tb
            length:QLineEdit = le
            column = QTextLength(type.defaultAction().property(self.lenType), float(length.text()))
            columns.append(column)
        format.setColumnWidthConstraints(columns)
        t.setFormat(format)

    @classmethod
    def typeChanged(cls, action: QAction, lineEdit: QLineEdit, toolButton:QToolButton):

        previousType = lineEdit.property(cls.lenType)
        currentType = action.property(cls.lenType)

        if currentType == previousType:
            return
        if currentType == QTextLength.Type.VariableLength:
            lineEdit.setEnabled(False)
        elif currentType == QTextLength.Type.PercentageLength:
            lineEdit.setEnabled(True)
        elif currentType == QTextLength.Type.FixedLength:
            lineEdit.setEnabled(True)

        lineEdit.setProperty(cls.lenType, action.property(cls.lenType))
        toolButton.setDefaultAction(action)


def setCellsBackgroundColor(text: TextEdit):
    firstRow, firstColumn, numRows, numColumns = text.getSelectedCellCoordinate()
    t = text.textCursor().currentTable()
    latestCell = t.cellAt(firstRow + numRows -1, firstColumn + numColumns - 1)

    dlg = QColorDialog(text)
    dlg.setCurrentColor(latestCell.format().background().color())
    if dlg.exec():
        if not checkLockFunc(text.parentWidget):
            return
        newColor = dlg.currentColor()
        text.textCursor().beginEditBlock()
        cells = text.getTableCells(t, firstRow, firstColumn, numRows, numColumns)
        for row in cells:
            for cell in row:
                format = cell.format()
                format.setBackground(newColor)
                cell.setFormat(format)
        text.textCursor().endEditBlock()
