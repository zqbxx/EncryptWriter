# -*- coding: utf-8 -*-
import os

from keymanager.dialogs import KeyMgrDialog
from keymanager.encryptor import encrypt_data, decrypt_data
from keymanager.key import KEY_CHECKER as key_checker, start_check_key_thread, KEY_CACHE as key_cache, \
    add_key_invalidate_callback, add_current_keystatus

from settings import getIcon

os.environ['QT_API'] = 'PySide6'
import qtawesome as qta
import sys
from pathlib import Path

from PySide6 import QtPrintSupport, QtCore
from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QIcon, QContextMenuEvent, Qt, QImage, QTextCharFormat, QFont, QTextCursor, \
    QTextListFormat, QTextDocument, QTextImageFormat, QTextFrameFormat, QTextBlockFormat, QTextBlock, QBrush, QColor
from PySide6.QtWidgets import QMainWindow, QFontComboBox, QSpinBox, QMessageBox, QMenu, QTextEdit, QFileDialog, QDialog, \
    QColorDialog, QApplication, QPushButton

from ext import datetime, table, wordcount, image, emo, textedit
from ext.find import Find


class Main(QMainWindow):

    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent)

        self.filename = ""

        self.changesSaved = True

        self.emoji_browser: emo.IconBrowser = None
        self.tablePropertyEditor: table.Table = None

        self.initUI()


    def initToolbar(self):

        self.newAction = QAction(getIcon('new'), "New", self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.setStatusTip("Create a new document from scratch.")
        self.newAction.triggered.connect(self.new)

        self.openAction = QAction(getIcon('open'), "Open file", self)
        self.openAction.setStatusTip("Open existing document")
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.open)

        self.saveAction = QAction(getIcon('save'), "Save", self)
        self.saveAction.setStatusTip("Save document")
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.save)

        self.printAction = QAction(getIcon('print'), "Print document", self)
        self.printAction.setStatusTip("Print document")
        self.printAction.setShortcut("Ctrl+P")
        self.printAction.triggered.connect(self.printHandler)

        self.previewAction = QAction(getIcon('preview'), "Page view", self)
        self.previewAction.setStatusTip("Preview page before printing")
        self.previewAction.setShortcut("Ctrl+Shift+P")
        self.previewAction.triggered.connect(self.preview)

        self.keyMgrAction = QAction(getIcon('keyMgr'), '密钥管理', self)
        self.keyMgrAction.setStatusTip("创建、添加删除密钥")
        self.keyMgrAction.setShortcut("Ctrl+Shift+K")
        self.keyMgrAction.triggered.connect(self.keyManager)

        self.findAction = QAction(getIcon('find'), "Find and replace", self)
        self.findAction.setStatusTip("Find and replace words in your document")
        self.findAction.setShortcut("Ctrl+F")
        self.findAction.triggered.connect(Find(self).show)

        self.cutAction = QAction(getIcon('cut'), "Cut to clipboard", self)
        self.cutAction.setStatusTip("Delete and copy text to clipboard")
        self.cutAction.setShortcut("Ctrl+X")
        self.cutAction.triggered.connect(self.text.cut)

        self.copyAction = QAction(getIcon('copy'), "Copy to clipboard", self)
        self.copyAction.setStatusTip("Copy text to clipboard")
        self.copyAction.setShortcut("Ctrl+C")
        self.copyAction.triggered.connect(self.text.copy)

        self.pasteAction = QAction(getIcon('paste'), "Paste from clipboard", self)
        self.pasteAction.setStatusTip("Paste text from clipboard")
        self.pasteAction.setShortcut("Ctrl+V")
        self.pasteAction.triggered.connect(self.text.paste)

        self.undoAction = QAction(getIcon('undo'), "Undo last action", self)
        self.undoAction.setStatusTip("Undo last action")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.text.undo)

        self.redoAction = QAction(getIcon('redo'), "Redo last undone thing", self)
        self.redoAction.setStatusTip("Redo last undone thing")
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.triggered.connect(self.text.redo)

        dateTimeAction = QAction(getIcon('dateTime'), "Insert current date/time", self)
        dateTimeAction.setStatusTip("Insert current date/time")
        dateTimeAction.setShortcut("Ctrl+D")
        dateTimeAction.triggered.connect(datetime.DateTime(self).show)

        wordCountAction = QAction(getIcon('wordCount'), "See word/symbol count", self)
        wordCountAction.setStatusTip("See word/symbol count")
        wordCountAction.setShortcut("Ctrl+W")
        wordCountAction.triggered.connect(self.wordCount)

        tableAction = QAction(getIcon('table'), "Insert table", self)
        tableAction.setStatusTip("Insert table")
        tableAction.setShortcut("Ctrl+T")
        tableAction.triggered.connect(self.tablePropertyEditor.show)

        imageAction = QAction(getIcon('image'), "Insert image", self)
        imageAction.setStatusTip("Insert image")
        imageAction.setShortcut("Ctrl+Shift+I")
        imageAction.triggered.connect(self.insertImage)

        bulletAction = QAction(getIcon('bullet'), "Insert bullet List", self)
        bulletAction.setStatusTip("Insert bullet list")
        bulletAction.setShortcut("Ctrl+Shift+B")
        bulletAction.triggered.connect(self.bulletList)

        numberedAction = QAction(getIcon('numbered'), "Insert numbered List", self)
        numberedAction.setStatusTip("Insert numbered list")
        numberedAction.setShortcut("Ctrl+Shift+L")
        numberedAction.triggered.connect(self.numberList)

        sourceCode = QAction(getIcon('code'), "复制代码", self)
        sourceCode.triggered.connect(self.copySourceCode)

        emojiAction = QAction(getIcon('emoji'), "插入表情", self)
        emojiAction.triggered.connect(self.openEmoji)

        quoteAction = QAction(getIcon('quote'), "插入引用", self)
        quoteAction.triggered.connect(self.quote)

        self.toolbar = self.addToolBar("Options")

        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.saveAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.previewAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.cutAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.pasteAction)
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.findAction)
        self.toolbar.addAction(dateTimeAction)
        self.toolbar.addAction(wordCountAction)
        self.toolbar.addAction(tableAction)
        self.toolbar.addAction(imageAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(bulletAction)
        self.toolbar.addAction(numberedAction)

        self.addToolBarBreak()
        self.toolbar.addAction(emojiAction)
        self.toolbar.addAction(quoteAction)
        self.toolbar.addAction(sourceCode)

    def initFormatbar(self):

        fontBox = QFontComboBox(self)
        fontBox.currentFontChanged.connect(self.font)

        fontSize = QSpinBox(self)

        # Will display " pt" after each value
        fontSize.setSuffix(" pt")

        fontSize.valueChanged.connect(lambda size: self.text.setFontPointSize(size))

        fontSize.setValue(14)

        defaultFont = fontBox.currentFont()
        defaultFont.setPointSize(14)
        self.text.document().setDefaultFont(defaultFont)

        fontColor = QAction(getIcon('fontColor'),"Change font color",self)
        fontColor.triggered.connect(self.fontColorChanged)

        boldAction = QAction(getIcon('bold'),"Bold",self)
        boldAction.triggered.connect(self.bold)

        italicAction = QAction(getIcon('italic'),"Italic",self)
        italicAction.triggered.connect(self.italic)

        underlAction = QAction(getIcon('underl'),"Underline",self)
        underlAction.triggered.connect(self.underline)

        strikeAction = QAction(getIcon('strike'),"Strike-out",self)
        strikeAction.triggered.connect(self.strike)

        superAction = QAction(getIcon('super'),"Superscript",self)
        superAction.triggered.connect(self.superScript)

        subAction = QAction(getIcon('sub'), "Subscript",self)
        subAction.triggered.connect(self.subScript)

        alignLeft = QAction(getIcon('alignLeft'),"Align left",self)
        alignLeft.triggered.connect(self.alignLeft)

        alignCenter = QAction(getIcon('alignCenter'),"Align center",self)
        alignCenter.triggered.connect(self.alignCenter)

        alignRight = QAction(getIcon('alignRight'),"Align right",self)
        alignRight.triggered.connect(self.alignRight)

        alignJustify = QAction(getIcon('alignJustify'),"Align justify",self)
        alignJustify.triggered.connect(self.alignJustify)

        indentAction = QAction(getIcon('indent'),"Indent Area",self)
        indentAction.setShortcut("Ctrl+Tab")
        indentAction.triggered.connect(self.indent)

        dedentAction = QAction(getIcon('dedent'),"Dedent Area",self)
        dedentAction.setShortcut("Shift+Tab")
        dedentAction.triggered.connect(self.dedent)

        backColor = QAction(getIcon('backColor'),"Change background color",self)
        backColor.triggered.connect(self.highlight)

        self.formatbar = self.addToolBar("Format")

        self.formatbar.addWidget(fontBox)
        self.formatbar.addWidget(fontSize)

        self.formatbar.addSeparator()

        self.formatbar.addAction(fontColor)
        self.formatbar.addAction(backColor)

        self.formatbar.addSeparator()

        self.formatbar.addAction(boldAction)
        self.formatbar.addAction(italicAction)
        self.formatbar.addAction(underlAction)
        self.formatbar.addAction(strikeAction)
        self.formatbar.addAction(superAction)
        self.formatbar.addAction(subAction)

        self.formatbar.addSeparator()

        self.formatbar.addAction(alignLeft)
        self.formatbar.addAction(alignCenter)
        self.formatbar.addAction(alignRight)
        self.formatbar.addAction(alignJustify)

        self.formatbar.addSeparator()

        self.formatbar.addAction(indentAction)
        self.formatbar.addAction(dedentAction)

    def initMenubar(self):

        menubar = self.menuBar()

        file = menubar.addMenu("File")
        edit = menubar.addMenu("Edit")
        view = menubar.addMenu("View")

        # Add the most important actions to the menubar

        file.addAction(self.newAction)
        file.addAction(self.openAction)
        file.addAction(self.saveAction)
        file.addAction(self.printAction)
        file.addAction(self.previewAction)
        file.addAction(self.keyMgrAction)

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.copyAction)
        edit.addAction(self.pasteAction)
        edit.addAction(self.findAction)

        # Toggling actions for the various bars
        toolbarAction = QAction("Toggle Toolbar",self)
        toolbarAction.triggered.connect(self.toggleToolbar)

        formatbarAction = QAction("Toggle Formatbar",self)
        formatbarAction.triggered.connect(self.toggleFormatbar)

        statusbarAction = QAction("Toggle Statusbar",self)
        statusbarAction.triggered.connect(self.toggleStatusbar)

        view.addAction(toolbarAction)
        view.addAction(formatbarAction)
        view.addAction(statusbarAction)

    def initUI(self):

        self.text = textedit.TextEdit(self)
        self.rootFrame = self.text.textCursor().currentFrame()
        self.text.document().setDocumentMargin(20)
        self.text.document().contentsChanged.connect(lambda: key_cache.get_cur_key().key if key_cache.get_cur_key() is not None and not key_cache.get_cur_key().timeout else None)

        # Set the tab stop width to around 33 pixels which is
        # more or less 8 spaces
        self.text.setTabStopDistance(33)

        self.tablePropertyEditor = table.Table(self.text)

        self.initToolbar()
        self.initFormatbar()
        self.initMenubar()

        self.setCentralWidget(self.text)

        # Initialize a statusbar for the window
        self.statusbar = self.statusBar()
        self.initStatusBar()

        # If the cursor position changes, call the function that displays
        # the line and column number
        self.text.cursorPositionChanged.connect(self.cursorPosition)

        # We need our own context menu for tables
        self.text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text.customContextMenuRequested.connect(self.context)

        self.text.textChanged.connect(self.changed)

        self.setGeometry(100,100,1030,800)
        self.setWindowTitle("Writer")
        self.setWindowIcon(QIcon("icons/icon.png"))

    def initStatusBar(self):
        btn = QPushButton('', self)
        btn.setFlat(True)
        unlock = qta.icon('ei.unlock', options=[{'color': '#006600'}])
        lock = qta.icon('ei.lock', options=[{'color': '#660033'}])
        add_current_keystatus(lambda key: btn.setIcon(unlock if key is not None and not key.timeout else lock))
        self.statusbar.addPermanentWidget(btn)

    def changed(self):
        self.changesSaved = False

    def closeEvent(self,event):

        if self.changesSaved:

            event.accept()

        else:
        
            popup = QMessageBox(self)

            popup.setIcon(QMessageBox.Warning)
            
            popup.setText("The document has been modified")
            
            popup.setInformativeText("Do you want to save your changes?")
            
            popup.setStandardButtons(QMessageBox.Save   |
                                      QMessageBox.Cancel |
                                      QMessageBox.Discard)
            
            popup.setDefaultButton(QMessageBox.Save)

            answer = popup.exec()

            if answer == QMessageBox.Save:
                if not self.save():
                    event.ignore()

            elif answer == QMessageBox.Discard:
                event.accept()

            else:
                event.ignore()

    def context(self,pos):

        charFormat = self.text.currentCharFormat()
        if charFormat.isImageFormat():
            menu = QMenu(self)
            image_format = charFormat.toImageFormat()
            def showImageSetting():
                imageSetting = image.Image(image_format, self)
                imageSetting.okClicked.connect(lambda f:self.text.setCurrentCharFormat(f))
                imageSetting.exec()
                imageSetting.destroy()

            def imageSaveAs():
                selectedImage = image.Image.retriveRawImage(image_format)
                filename:str = QFileDialog.getSaveFileName(self, '图片另存为', './', '图像(*.png)')[0]
                if filename:
                    if not filename.lower().endswith('.png'):
                        filename += '.png'
                    if not selectedImage.save(filename, 'png'):
                        QMessageBox.warning(self, '保存图片失败', '保存图片失败')


            imageSettingAction = QAction(qta.icon('mdi.resize'), "调整图片大小", self)
            imageSettingAction.triggered.connect(showImageSetting)
            menu.addAction(imageSettingAction)

            imageExportAction = QAction(qta.icon('msc.save-as'), "图片另存为", self)
            imageExportAction.triggered.connect(imageSaveAs)
            menu.addAction(imageExportAction)

            pos = self.mapToGlobal(pos)

            # Add pixels for the tool and formatbars, which are not included
            # in mapToGlobal(), but only if the two are currently visible and
            # not toggled by the user

            if self.toolbar.isVisible():
                pos.setY(pos.y() + 45)

            if self.formatbar.isVisible():
                pos.setY(pos.y() + 45)
            menu.move(pos)
            menu.exec()

            # image_format = charFormat.toImageFormat()
            # image_format.setWidth(image_format.width()*0.9)
            # image_format.setHeight(image_format.width()*0.9)
            # self.text.setCurrentCharFormat(image_format)
            return

        # Grab the cursor
        cursor = self.text.textCursor()

        currentFrame = cursor.currentFrame()
        if currentFrame != self.text.document().rootFrame():
            print('child frame')

        # Grab the current table, if there is one
        table = cursor.currentTable()

        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:

            menu = QMenu(self)

            appendRowAction = QAction("Append row",self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))

            appendColAction = QAction("Append column",self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))


            removeRowAction = QAction("Remove row",self)
            removeRowAction.triggered.connect(self.removeRow)

            removeColAction = QAction("Remove column",self)
            removeColAction.triggered.connect(self.removeCol)


            insertRowAction = QAction("Insert row",self)
            insertRowAction.triggered.connect(self.insertRow)

            insertColAction = QAction("Insert column",self)
            insertColAction.triggered.connect(self.insertCol)


            mergeAction = QAction("Merge cells",self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))

            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)


            splitAction = QAction("Split cells",self)

            cell = table.cellAt(cursor)

            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:

                splitAction.triggered.connect(lambda: table.splitCell(cell.row(),cell.column(),1,1))

            else:
                splitAction.setEnabled(False)

            propertyAction = QAction("修改表格格式", self)
            propertyAction.triggered.connect(self.modifyTableProperty)

            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)

            menu.addSeparator()

            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)

            menu.addSeparator()

            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)

            menu.addSeparator()

            menu.addAction(mergeAction)
            menu.addAction(splitAction)

            menu.addSeparator()

            menu.addAction(propertyAction)

            # Convert the widget coordinates into global coordinates
            pos = self.mapToGlobal(pos)

            # Add pixels for the tool and formatbars, which are not included
            # in mapToGlobal(), but only if the two are currently visible and
            # not toggled by the user

            if self.toolbar.isVisible():
                pos.setY(pos.y() + 45)

            if self.formatbar.isVisible():
                pos.setY(pos.y() + 45)
                
            # Move the menu to the new position
            menu.move(pos)

            menu.show()

        else:

            event = QContextMenuEvent(QContextMenuEvent.Mouse,QPoint())

            self.text.contextMenuEvent(event)

    def removeRow(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's row
        table.removeRows(cell.row(),1)

    def removeCol(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Delete the cell's column
        table.removeColumns(cell.column(),1)

    def insertRow(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertRows(cell.row(),1)

    def insertCol(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()

        # Get the current cell
        cell = table.cellAt(cursor)

        # Insert a new row at the cell's position
        table.insertColumns(cell.column(),1)


    def toggleToolbar(self):

        state = self.toolbar.isVisible()

        # Set the visibility to its inverse
        self.toolbar.setVisible(not state)

    def toggleFormatbar(self):

        state = self.formatbar.isVisible()

        # Set the visibility to its inverse
        self.formatbar.setVisible(not state)

    def toggleStatusbar(self):

        state = self.statusbar.isVisible()

        # Set the visibility to its inverse
        self.statusbar.setVisible(not state)

    def new(self):

        spawn = Main()

        spawn.show()

    def open(self):

        current_key = key_cache.get_cur_key()

        if current_key is None:
            QMessageBox.critical(self, '密钥错误', '没有激活的密钥')
            return

        if current_key.timeout:
            QMessageBox.critical(self, '密钥错误', '密钥超时')
            return

        # Get filename and show only .writer files
        #PYQT5 Returns a tuple in PyQt5, we only need the filename
        self.filename = QFileDialog.getOpenFileName(self, 'Open File',".","(*.writer)")[0]

        if self.filename:
            encrypt_content = Path(self.filename).read_bytes()
            content = decrypt_data(current_key.key, encrypt_content)
            self.text.setText(content.decode('utf-8'))

    def save(self):

        current_key = key_cache.get_cur_key()

        if current_key is None:
            QMessageBox.critical(self, '密钥错误', '没有激活的密钥')
            return False

        if current_key.timeout:
            QMessageBox.critical(self, '密钥错误', '密钥超时')
            return False

        # Only open dialog if there is no filename yet
        #PYQT5 Returns a tuple in PyQt5, we only need the filename
        if not self.filename:
          self.filename = QFileDialog.getSaveFileName(self, 'Save File')[0]

        if self.filename:
            
            # Append extension if not there yet
            if not self.filename.endswith(".writer"):
              self.filename += ".writer"

            content = self.text.toHtml().encode('utf-8')
            key_data = current_key.key
            encrypt_content = encrypt_data(key_data, content)
            Path(self.filename).write_bytes(encrypt_content)

            self.changesSaved = True
            return True
        return False

    def preview(self):

        # Open preview dialog
        preview = QtPrintSupport.QPrintPreviewDialog()

        # If a print is requested, open print dialog
        preview.paintRequested.connect(lambda p: self.text.print_(p))

        preview.exec_()

    def keyManager(self):
        kmd = KeyMgrDialog()
        kmd.exec()
        kmd.destroy()

    def printHandler(self):

        # Open printing dialog
        dialog = QtPrintSupport.QPrintDialog()

        if dialog.exec_() == QDialog.Accepted:
            self.text.document().print_(dialog.printer())

    def cursorPosition(self):

        cursor = self.text.textCursor()

        # Mortals like 1-indexed things
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()

        self.statusbar.showMessage("Line: {} | Column: {}".format(line,col))

    def wordCount(self):

        wc = wordcount.WordCount(self)

        wc.getText()

        wc.show()

    def insertImage(self):

        # Get image file name
        #PYQT5 Returns a tuple in PyQt5
        filename = QFileDialog.getOpenFileName(self, 'Insert image',".","Images (*.png *.xpm *.jpg *.bmp *.gif)")[0]

        if filename:
            
            # Create image object
            image_bytes = Path(filename).read_bytes()
            image = QImage()
            image.loadFromData(image_bytes)

            # Error if unloadable
            if image.isNull():

                popup = QMessageBox(QMessageBox.Critical,
                                          "Image load error",
                                          "Could not load image file!",
                                          QMessageBox.Ok,
                                          self)
                popup.show()

            else:
                self.text.dropImage(image)

    def fontColorChanged(self):

        # Get a color from the text dialog
        color = QColorDialog.getColor()

        # Set it as the new text color
        self.text.setTextColor(color)

    def highlight(self):

        color = QColorDialog.getColor()

        self.text.setTextBackgroundColor(color)

    def modifyTableProperty(self):
        self.tablePropertyEditor.setCurrentFormat(self.text.textCursor().currentTable().format())
        self.tablePropertyEditor.updateValue()
        self.tablePropertyEditor.show()

    def copySourceCode(self):
        #self.text.insertHtml('<h1>标题一</h1>')
        self.text.textCursor().beginEditBlock()
        text = self.text.textCursor().selectedText()
        self.text.textCursor().insertHtml('<h1>' + text + '</h1>')
        self.text.textCursor().endEditBlock()
        self.text.textCursor().insertHtml('<code>var i = "1"</code>')
        self.text.textCursor().insertHtml('<cite>fffffffffffffffffffffffffffff</cite>')
        # textList = self.text.textCursor().currentList()
        # textListCnt = textList.count()
        # for i in range(textListCnt):
        #     block = textList.item(i)
        #     print(block.text())
        #print(self.text.textCursor().selection().toHtml())

        #self.text.insertHtml('<h3>标题三</h3>')
        text = self.text.toHtml()
        print(text)

    def openEmoji(self):

        if self.emoji_browser is None:
            self.emoji_browser = emo.IconBrowser()
            self.emoji_browser.emojiSelected.connect(lambda char: self.text.textCursor().insertText(char))

        if self.emoji_browser.isVisible():
            return

        self.emoji_browser.show()

    def quote(self):
        frameFormat = QTextFrameFormat()
        frameFormat.setBorder(1)
        frameFormat.setBackground(QColor(255, 255, 240))
        frameFormat.setBorderBrush(Qt.BrushStyle.SolidPattern)
        frameFormat.setLeftMargin(20)
        frameFormat.setRightMargin(20)
        frameFormat.setTopMargin(20)
        frameFormat.setBottomMargin(20)
        frameFormat.setPadding(20)
        self.text.textCursor().insertFrame(frameFormat)

    def font(self, font:QFont):
        currentFont = self.text.currentFont()
        currentFont.setFamily(font.family())
        currentFont.setStyleName()
        self.text.setCurrentFont(currentFont)

    def bold(self):

        if self.text.fontWeight() == QFont.Bold:

            self.text.setFontWeight(QFont.Normal)

        else:

            self.text.setFontWeight(QFont.Bold)

    def italic(self):

        state = self.text.fontItalic()

        self.text.setFontItalic(not state)

    def underline(self):

        state = self.text.fontUnderline()

        self.text.setFontUnderline(not state)

    def strike(self):

        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # And set the next char format
        self.text.setCurrentCharFormat(fmt)

    def superScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QTextCharFormat.AlignSuperScript)

        else:

            fmt.setVerticalAlignment(QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def subScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QTextCharFormat.AlignNormal:

            fmt.setVerticalAlignment(QTextCharFormat.AlignSubScript)

        else:

            fmt.setVerticalAlignment(QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def alignLeft(self):
        self.text.setAlignment(Qt.AlignLeft)

    def alignRight(self):
        self.text.setAlignment(Qt.AlignRight)

    def alignCenter(self):
        self.text.setAlignment(Qt.AlignCenter)

    def alignJustify(self):
        self.text.setAlignment(Qt.AlignJustify)

    def indent(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's end
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QTextCursor.Up if diff > 0 else QTextCursor.Down

            # Iterate over lines (diff absolute value)
            for n in range(abs(diff) + 1):

                # Move to start of each line
                cursor.movePosition(QTextCursor.StartOfLine)

                # Insert tabbing
                cursor.insertText("\t")

                # And move back up
                cursor.movePosition(direction)

        # If there is no selection, just insert a tab
        else:

            cursor.insertText("\t")

    def handleDedent(self,cursor):

        cursor.movePosition(QTextCursor.StartOfLine)

        # Grab the current line
        line = cursor.block().text()

        # If the line starts with a tab character, delete it
        if line.startswith("\t"):

            # Delete next character
            cursor.deleteChar()

        # Otherwise, delete all spaces until a non-space character is met
        else:
            for char in line[:8]:

                if char != " ":
                    break

                cursor.deleteChar()

    def dedent(self):

        cursor = self.text.textCursor()

        if cursor.hasSelection():

            # Store the current line/block number
            temp = cursor.blockNumber()

            # Move to the selection's last line
            cursor.setPosition(cursor.anchor())

            # Calculate range of selection
            diff = cursor.blockNumber() - temp

            direction = QTextCursor.Up if diff > 0 else QTextCursor.Down

            # Iterate over lines
            for n in range(abs(diff) + 1):

                self.handleDedent(cursor)

                # Move up
                cursor.movePosition(direction)

        else:
            self.handleDedent(cursor)


    def bulletList(self):

        cursor = self.text.textCursor()

        # Insert bulleted list
        cursor.insertList(QTextListFormat.ListDisc)

    def numberList(self):

        cursor = self.text.textCursor()

        # Insert list with numbers
        cursor.insertList(QTextListFormat.ListDecimal)

def main():
    key_checker['timeout'] = 300
    start_check_key_thread()
    add_key_invalidate_callback(lambda key: print('key超时'))

    app = QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
