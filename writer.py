# -*- coding: utf-8 -*-
import os
import time
from functools import partial, lru_cache

import qtawesome as qta

import keymanager.encryptor
from keymanager.menus import activate_key, add_key, add_keymanager_menu, reload_key

from writerlib import emo, dt, textedit, table, image, wordcount, quote, systemsetting
from writerlib.find import Find
from writerlib.property import PropertyEditor
from writerlib.settings import getIcon, Settings, getIconOpt, getIconName, addDefaultColorToFontOptions
from writerlib.textedit import Selection

os.environ['QT_API'] = 'PySide6'
from keymanager.dialogs import KeyMgrDialog
from keymanager.encryptor import encrypt_data, decrypt_data
from keymanager.key import KEY_CHECKER as key_checker, start_check_key_thread, KEY_CACHE as key_cache, \
    add_key_invalidate_callback, add_current_keystatus_callback, Key, set_key_timeout

import sys
from pathlib import Path

from PySide6 import QtPrintSupport, QtGui
from PySide6.QtCore import QPoint, Signal, QMetaType
from PySide6.QtGui import QAction, QIcon, QContextMenuEvent, Qt, QImage, QTextCharFormat, QFont, QTextCursor, \
    QTextListFormat, QColor
from PySide6.QtWidgets import QMainWindow, QFontComboBox, QSpinBox, QMessageBox, QMenu, QFileDialog, QDialog, \
    QColorDialog, QApplication, QPushButton, QToolButton, QStackedLayout, QWidget, \
    QLabel, QSizePolicy, QProgressBar, QLCDNumber


def checkLock(callback):
    def f(*args, **kwargs):
        main:Main = args[0]
        if main.isDocumentLocked():
            QMessageBox.warning(main, '警告', '锁定状态无法进行操作')
            return None
        r = callback(*args, **kwargs)
        return r
    return f


class Main(QMainWindow):

    autoLockEditor = Signal(Key, bool)
    updateStatusbarIcon = Signal(Key)

    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent)

        self.filename = ""
        self.changesSaved = True
        self.defaultKeyMark = bytes()
        self.encryptedMark = bytes()

        self.encrypt_lock_text = ""  # 锁定时记录的加密文件内容

        self.emoji_browser: emo.IconBrowser = None

        self.systemSetting = Settings()
        self.initUI()
        self.autoLockEditor.connect(self.lock)
        self.updateStatusbarIcon.connect(self.updateStatusbarKeyIndicator)
        add_key_invalidate_callback(self.currentKeyAboutToTimeout)
        set_key_timeout(self.systemSetting.keyTimeout)


    def initToolbar(self):

        self.newAction = QAction(getIcon('new'), "新建", self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.setStatusTip("创建一个新的文档")
        self.newAction.triggered.connect(self.new)

        self.openAction = QAction(getIcon('open'), "打开", self)
        self.openAction.setStatusTip("打开一个已经存在的文档")
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.open)

        self.saveAction = QAction(getIcon('save'), "保存", self)
        self.saveAction.setStatusTip("保存文档")
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.save)

        self.closeAction = QAction(getIcon('close'), '关闭', self)
        self.closeAction.setStatusTip("关闭文档")
        self.closeAction.triggered.connect(self.closeDoc)

        self.lockAction = QAction(getIcon('unlock'), '未锁定', self)
        self.lockAction.setShortcut('锁定文档后，文档不能被编辑、保存和查看')
        self.lockAction.triggered.connect(self.lock)
        self.lockAction.setProperty('locked', False)
        self.lockAction.setProperty('alwaysEnabled', True)

        self.printAction = QAction(getIcon('print'), "打印", self)
        self.printAction.setStatusTip("打印文档")
        self.printAction.setShortcut("Ctrl+P")
        self.printAction.triggered.connect(self.printHandler)

        self.previewAction = QAction(getIcon('preview'), "预览", self)
        self.previewAction.setStatusTip("在打印前预览文档")
        self.previewAction.setShortcut("Ctrl+Shift+P")
        self.previewAction.triggered.connect(self.preview)

        self.sysSettingAction = QAction(getIcon('sysSetting'), '系统设置', self)
        self.sysSettingAction.setStatusTip('设置系统默认属性')
        self.sysSettingAction.triggered.connect(self.sysSetting)

        self.propertyAction = QAction(getIcon('property'), '文档属性', self)
        self.propertyAction.triggered.connect(self.editProperty)

        self.keyMgrAction = QAction(getIcon('keyMgr'), '密钥管理', self)
        self.keyMgrAction.setStatusTip("创建、添加删除密钥")
        self.keyMgrAction.setShortcut("Ctrl+Shift+K")
        self.keyMgrAction.triggered.connect(self.keyManager)

        self.findAction = QAction(getIcon('find'), "查找和替换", self)
        self.findAction.setStatusTip("在文档中查找和替换单词、词组")
        self.findAction.setShortcut("Ctrl+F")
        self.findAction.triggered.connect(Find(self).show)

        self.cutAction = QAction(getIcon('cut'), "剪切", self)
        self.cutAction.setStatusTip("将文档内容复制到剪贴板，然后在文档中删除")
        self.cutAction.setShortcut("Ctrl+X")
        self.cutAction.triggered.connect(self.text.cut)

        self.copyAction = QAction(getIcon('copy'), "复制", self)
        self.copyAction.setStatusTip("复制文档内容到剪贴板")
        self.copyAction.setShortcut("Ctrl+C")
        self.copyAction.triggered.connect(self.text.copy)

        self.pasteAction = QAction(getIcon('paste'), "粘贴", self)
        self.pasteAction.setStatusTip("从剪贴板中复制内容到文档中")
        self.pasteAction.setShortcut("Ctrl+V")
        self.pasteAction.triggered.connect(self.text.paste)

        self.undoAction = QAction(getIcon('undo'), "撤销", self)
        self.undoAction.setStatusTip("撤回上一次的操作")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.text.undo)

        self.clearRedoUndoAction = QAction(getIcon('clearUndoRedo'), "清除撤销、重做历史", self)
        self.clearRedoUndoAction.triggered.connect(self.clearUndoRedo)

        self.redoAction = QAction(getIcon('redo'), "重做", self)
        self.redoAction.setStatusTip("重做上次撤销的操作")
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.triggered.connect(self.text.redo)

        dateTimeAction = QAction(getIcon('dateTime'), "插入时间和日期", self)
        dateTimeAction.setStatusTip("插入时间和日期")
        dateTimeAction.setShortcut("Ctrl+D")
        dateTimeAction.triggered.connect(dt.DateTime(self).show)

        wordCountAction = QAction(getIcon('wordCount'), "文字统计", self)
        wordCountAction.setStatusTip("查看文字和符号数量")
        wordCountAction.setShortcut("Ctrl+W")
        wordCountAction.triggered.connect(self.wordCount)

        tableAction = QAction(getIcon('table'), "插入表格", self)
        tableAction.setStatusTip("插入表格")
        tableAction.setShortcut("Ctrl+T")
        tableAction.triggered.connect(self.insertTable)

        imageAction = QAction(getIcon('image'), "插入图片", self)
        imageAction.setStatusTip("插入图片")
        imageAction.setShortcut("Ctrl+Shift+I")
        imageAction.triggered.connect(self.insertImage)

        bulletAction = QAction(getIcon('bullet'), "插入符号列表", self)
        bulletAction.setStatusTip("插入符号列表")
        bulletAction.setShortcut("Ctrl+Shift+B")
        bulletAction.triggered.connect(self.bulletList)

        numberedAction = QAction(getIcon('numbered'), "插入数字列表", self)
        numberedAction.setStatusTip("插入数字列表")
        numberedAction.setShortcut("Ctrl+Shift+L")
        numberedAction.triggered.connect(self.numberList)

        sourceCode = QAction(getIcon('code'), "复制代码", self)
        sourceCode.triggered.connect(self.copySourceCode)

        emojiAction = QAction(getIcon('emoji'), "插入表情", self)
        emojiAction.triggered.connect(self.openEmoji)

        quoteAction = QAction(getIcon('quote'), "插入引用", self)
        quoteAction.triggered.connect(self.insertQuote)

        self.toolbar = self.addToolBar("Options")

        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.closeAction)
        self.toolbar.addAction(self.lockAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.previewAction)
        self.toolbar.addAction(self.propertyAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.cutAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.pasteAction)
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addAction(self.clearRedoUndoAction)
        self.toolbar.addAction(self.findAction)
        self.toolbar.addAction(wordCountAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(dateTimeAction)
        self.toolbar.addAction(tableAction)
        self.toolbar.addAction(imageAction)
        self.toolbar.addAction(bulletAction)
        self.toolbar.addAction(numberedAction)
        self.toolbar.addAction(emojiAction)
        self.toolbar.addAction(quoteAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(sourceCode)

        self.addToolBarBreak()

    @checkLock
    def clearUndoRedo(self):
        return self.text.document().clearUndoRedoStacks()

    def initFormatbar(self):

        self.fontBox = QFontComboBox(self)
        self.fontBox.currentFontChanged.connect(self.font)

        self.fontSize = QSpinBox(self)

        # Will display " pt" after each value
        self.fontSize.setSuffix(" pt")

        self.fontSize.valueChanged.connect(self.setFontSize)

        defaultFont = self.fontBox.currentFont()
        self.initDocumentDefaultSettings(defaultFont)

        self.fontColor = QAction(getIcon('fontColor'),"修改文字颜色",self)
        self.fontColor.triggered.connect(self.fontColorChanged)

        self.boldAction = QAction(getIcon('bold'),"粗体",self)
        self.boldAction.triggered.connect(self.bold)

        self.italicAction = QAction(getIcon('italic'),"斜体",self)
        self.italicAction.triggered.connect(self.italic)

        self.underlAction = QAction(getIcon('underl'),"下划线",self)
        self.underlAction.triggered.connect(self.underline)

        self.strikeAction = QAction(getIcon('strike'),"删除线",self)
        self.strikeAction.triggered.connect(self.strike)

        self.superAction = QAction(getIcon('super'),"上标",self)
        self.superAction.triggered.connect(self.superScript)

        self.subAction = QAction(getIcon('sub'), "下标",self)
        self.subAction.triggered.connect(self.subScript)

        alignLeft = QAction(getIcon('alignLeft'),"左对齐",self)
        alignLeft.triggered.connect(self.alignLeft)

        alignCenter = QAction(getIcon('alignCenter'),"居中",self)
        alignCenter.triggered.connect(self.alignCenter)

        alignRight = QAction(getIcon('alignRight'),"右对齐",self)
        alignRight.triggered.connect(self.alignRight)

        alignJustify = QAction(getIcon('alignJustify'),"两端对齐",self)
        alignJustify.triggered.connect(self.alignJustify)

        indentAction = QAction(getIcon('indent'),"增加缩进",self)
        indentAction.setShortcut("Ctrl+Tab")
        indentAction.triggered.connect(self.indent)

        dedentAction = QAction(getIcon('dedent'),"减少缩进",self)
        dedentAction.setShortcut("Shift+Tab")
        dedentAction.triggered.connect(self.dedent)

        self.backColor = QAction(getIcon('backColor'),"修改背景色",self)
        self.backColor.triggered.connect(self.changeBackgroundColor)

        headButton = QToolButton(self)

        h1Action = QAction(getIcon('h1'), '一级标题', self)
        h2Action = QAction(getIcon('h2'), '二级标题', self)
        h3Action = QAction(getIcon('h3'), '三级标题', self)
        h4Action = QAction(getIcon('h4'), '四级标题', self)

        h1Action.setProperty('level', 1)
        h2Action.setProperty('level', 2)
        h3Action.setProperty('level', 3)
        h4Action.setProperty('level', 4)

        h1Action.triggered.connect(partial(self.head, headButton=headButton, action=h1Action))
        h2Action.triggered.connect(partial(self.head, headButton=headButton, action=h2Action))
        h3Action.triggered.connect(partial(self.head, headButton=headButton, action=h3Action))
        h4Action.triggered.connect(partial(self.head, headButton=headButton, action=h4Action))

        headMenu = QMenu(headButton)
        headMenu.addAction(h1Action)
        headMenu.addAction(h2Action)
        headMenu.addAction(h3Action)
        headMenu.addAction(h4Action)

        headButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        headButton.setDefaultAction(h1Action)
        headButton.setMenu(headMenu)

        highlightButton = QToolButton(self)
        highlightButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        highlightAction = QAction(getIcon('highlight1'), '高亮,，加粗', self)
        highlightAction.triggered.connect(partial(self.highlight, toolButton=highlightButton, action=highlightAction))
        highlightUnderlineAction = QAction(getIcon('highlight2'), '高亮，加粗，下划线', self)
        highlightUnderlineAction.triggered.connect(partial(self.highlightUnderline, toolButton=highlightButton, action=highlightUnderlineAction))

        highlightMenu = QMenu(highlightButton)
        highlightMenu.addAction(highlightAction)
        highlightMenu.addAction(highlightUnderlineAction)

        highlightButton.setDefaultAction(highlightAction)
        highlightButton.setMenu(highlightMenu)

        clearAction = QAction(getIcon('clear'), '清除格式', self)
        clearAction.triggered.connect(self.clearFormat)

        self.formatbar = self.addToolBar("Format")

        self.formatbar.addWidget(self.fontBox)
        self.formatbar.addWidget(self.fontSize)

        self.formatbar.addSeparator()

        self.formatbar.addAction(self.fontColor)
        self.formatbar.addAction(self.backColor)

        self.formatbar.addSeparator()

        self.formatbar.addAction(self.boldAction)
        self.formatbar.addAction(self.italicAction)
        self.formatbar.addAction(self.underlAction)
        self.formatbar.addAction(self.strikeAction)
        self.formatbar.addAction(self.superAction)
        self.formatbar.addAction(self.subAction)

        self.formatbar.addSeparator()

        self.formatbar.addAction(alignLeft)
        self.formatbar.addAction(alignCenter)
        self.formatbar.addAction(alignRight)
        self.formatbar.addAction(alignJustify)

        self.formatbar.addSeparator()

        self.formatbar.addAction(indentAction)
        self.formatbar.addAction(dedentAction)

        self.formatbar.addWidget(headButton)
        self.formatbar.addWidget(highlightButton)

        self.formatbar.addAction(clearAction)

        self.fontSize.setValue(14)

    @checkLock
    def setFontSize(self, fontSize):
        self.text.setFontPointSize(fontSize)
        self.updateFormatBarIcon()

    def initDocumentDefaultSettings(self, defaultFont):
        defaultFont.setPointSize(14)
        self.text.document().setDefaultFont(defaultFont)
        self.text.setTextBackgroundColor(QColor('white'))

    def initMenubar(self):

        menubar = self.menuBar()

        file = menubar.addMenu("文件")
        edit = menubar.addMenu("编辑")
        view = menubar.addMenu("视图")
        key = menubar.addMenu('密钥')
        add_keymanager_menu(key, self)
        #key.menuAction().setProperty('alwaysEnabled', True)
        # Add the most important actions to the menubar

        file.addAction(self.newAction)
        file.addAction(self.openAction)
        file.addAction(self.saveAction)
        file.addAction(self.printAction)
        file.addAction(self.previewAction)
        file.addAction(self.sysSettingAction)

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.copyAction)
        edit.addAction(self.pasteAction)
        edit.addAction(self.findAction)

        # Toggling actions for the various bars
        toolbarAction = QAction("显示/隐藏 工具栏",self)
        toolbarAction.triggered.connect(self.toggleToolbar)

        formatbarAction = QAction("显示/隐藏 格式栏",self)
        formatbarAction.triggered.connect(self.toggleFormatbar)

        statusbarAction = QAction("显示/隐藏 状态栏",self)
        statusbarAction.triggered.connect(self.toggleStatusbar)

        view.addAction(toolbarAction)
        view.addAction(formatbarAction)
        view.addAction(statusbarAction)

    def initUI(self):

        self.text = textedit.TextEdit(self)
        self.text.document().setDocumentMargin(20)
        self.text.document().contentsChanged.connect(lambda: key_cache.get_cur_key().key if key_cache.get_cur_key() is not None and not key_cache.get_cur_key().timeout else None)

        # Set the tab stop width to around 33 pixels which is
        # more or less 8 spaces
        self.text.setTabStopDistance(33)

        self.tablePropertyEditor = table.TableEditor(self.text)

        self.initToolbar()
        self.initFormatbar()
        self.initMenubar()

        self.layout = QStackedLayout()
        self.layout.addWidget(self.text)
        lockLabel = QLabel('已锁定')
        lockLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lockLabelFont = lockLabel.font()
        lockLabelFont.setPointSize(50)
        lockLabel.setFont(lockLabelFont)
        lockLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lockLabel)
        self.setLayout(self.layout)
        self.layoutWidget = QWidget()
        self.layoutWidget.setLayout(self.layout)
        self.setCentralWidget(self.layoutWidget)
        self.text.setFocus()

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

        self.setGeometry(100, 100, 1030, 800)
        self.setWindowTitle("Writer")
        self.setWindowIcon(QIcon("icons/icon.png"))

    def initStatusBar(self):
        self.statusbarKeyIndicator = QPushButton('', self)
        self.statusbarKeyIndicator.setFlat(True)
        self.statusbarTimtoutProgressbarIndicator = QLCDNumber()
        # self.statusbarTimtoutProgressbarIndicator.setStyleSheet('''
        # QLCDNumber {background-color:yellow}
        # ''')
        #self.statusbarTimtoutProgressbarIndicator.setPalette(QtGui.Qt.red)
        QtGui.Qt
        self.statusbarTimtoutProgressbarIndicator.display(9999)
        self.statusbarTimtoutProgressbarIndicator.setMaximumSize(70, 20)
        self.statusbarTimtoutProgressbarIndicator.setSmallDecimalPoint(True)
        self.statusbarTimtoutProgressbarIndicator.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.statusbarTimtoutProgressbarIndicator.setDigitCount(4)
        unlock = getIcon('unlock')
        lock = getIcon('lock')
        add_current_keystatus_callback(lambda key: self.updateStatusbarIcon.emit(key))
        self.statusbar.addPermanentWidget(self.statusbarKeyIndicator)
        self.statusbar.addPermanentWidget(self.statusbarTimtoutProgressbarIndicator)

    def updateStatusbarKeyIndicator(self, key:Key):
        @lru_cache(maxsize=2)
        def getLockIcon(name: str):
            return getIcon(name)
        icon = getLockIcon('unlock') if key is not None and not key.timeout else getLockIcon('lock')
        self.statusbarKeyIndicator.setIcon(icon)

        currentKey = key_cache.get_cur_key()
        if currentKey is not None:
            if currentKey.timeout:
                self.statusbarTimtoutProgressbarIndicator.display(0)
            else:
                lastaccess = currentKey.last_access
                number = int(self.systemSetting.keyTimeout - (time.time() - lastaccess))
                self.statusbarTimtoutProgressbarIndicator.display(number)
        else:
            self.statusbarTimtoutProgressbarIndicator.display(9999)

    def currentKeyAboutToTimeout(self, key:Key):
        current_key = key_cache.get_cur_key()
        if current_key.id != key.id:
            return

        if self.systemSetting.autoLockDoc:
            tempKey = current_key.copy()
            self.autoLockEditor.emit(tempKey, True)

    def changed(self, changesSaved=False):
        self.changesSaved = changesSaved
        self.updateWindowsTitle()

    def updateWindowsTitle(self):
        encryptMsg = ' [加密文档] ' if self.text.isEncryptDocument else ' '
        if self.changesSaved:
            if not self.filename:
                self.setWindowTitle('Writer')
            else:
                self.setWindowTitle('Writer -' + encryptMsg + self.filename )
        else:
            if not self.filename:
                self.setWindowTitle('Writer -' + encryptMsg + '[未保存]')
            else:
                self.setWindowTitle('Writer -' + encryptMsg + self.filename + ' [未保存]')

    def closeEvent(self,event):

        if self.lockAction.property('locked'):
            QMessageBox.critical(self, '错误', '系统被锁定，可能存在未保存的内容')
            event.ignore()
            return

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

    @checkLock
    def context(self,pos: QPoint):

        textCursor = self.text.textCursor()
        mouseCursor = self.text.cursorForPosition(pos)
        mouseCursorPos = mouseCursor.position()

        # 将光标调整到鼠标位置
        if not textCursor.selectionStart() <=mouseCursorPos <= textCursor.selectionEnd():
            self.text.setTextCursor(mouseCursor)
            textCursor = self.text.textCursor()

        # 调整光标位置，否则无法判断图片
        if textCursor.charFormat().isImageFormat(): # 当前光标是图片格式的情况，一般来说此时光标在图片后
            # 当前选中一个字符（图片），调整鼠标位置到选中开始
            if textCursor.hasSelection():
                if textCursor.selectionStart() == textCursor.position() \
                        and abs(textCursor.selectionStart() - textCursor.selectionEnd()) == 1:
                    s = self.text.getSelection()
                    textCursor.clearSelection()
                    self.text.setSelection(s)
            else:
                # 没有选中则选中一个字符位置（图片）
                if textCursor.position() == 0:
                    self.text.setSelection(Selection(0, 1))
                else:
                    s = Selection(textCursor.position() - 1, textCursor.position())
                    self.text.setSelection(s)
        elif not textCursor.hasSelection():# 当前光标不是图片格式且不在选中状态
            # 向后移动一个查看格式
            textCursor.setPosition(textCursor.position() + 1, QTextCursor.MoveMode.MoveAnchor)
            if textCursor.charFormat().isImageFormat():
                s = Selection(textCursor.position() - 1, textCursor.position())
                self.text.setSelection(s)
            else:
                textCursor.setPosition(textCursor.position() - 1, QTextCursor.MoveMode.MoveAnchor)

        charFormat = self.text.currentCharFormat()

        if charFormat.isImageFormat() and abs(textCursor.selectionStart() - textCursor.selectionEnd()) <= 1:
            cursor = self.text.cursorForPosition(pos)
            menu = QMenu(self)
            image_format = charFormat.toImageFormat()
            def showImageSetting():
                imageSetting = image.Image(image_format, self)
                imageSetting.okClicked.connect(lambda f: self.text.setCurrentCharFormat(f))
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

            imageSettingAction = QAction(getIcon('imageSetting'), "调整图片大小", self)
            imageSettingAction.triggered.connect(showImageSetting)
            menu.addAction(imageSettingAction)

            imageExportAction = QAction(getIcon('imageExport'), "图片另存为", self)
            imageExportAction.triggered.connect(imageSaveAs)
            menu.addAction(imageExportAction)

            self.showMenu(menu, pos)

            return

        # Grab the cursor
        cursor = self.text.textCursor()

        currentFrame = cursor.currentFrame()
        if currentFrame != self.text.document().rootFrame() and not cursor.currentTable():
            menu = self.text.createStandardContextMenu()
            menu.addSeparator()
            modQuotePropAction = QAction('修改引用格式', self)
            modQuotePropAction.triggered.connect(self.modifyQuotePropery)
            menu.addAction(modQuotePropAction)
            self.showMenu(menu, pos)
            return


        # Grab the current table, if there is one
        table = cursor.currentTable()

        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:

            menu = QMenu(self)

            appendRowAction = QAction(getIcon('tabAppendRow'), "追加行",self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))

            appendColAction = QAction(getIcon('tabAppendColumn'), "追加列",self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))

            removeRowAction = QAction(getIcon('tabRemoveRow'), "删除行",self)
            removeRowAction.triggered.connect(self.removeRow)

            removeColAction = QAction(getIcon('tabRemoveColumn'), "删除列",self)
            removeColAction.triggered.connect(self.removeCol)


            insertRowAction = QAction(getIcon('tabInsertRow'), "插入行",self)
            insertRowAction.triggered.connect(self.insertRow)

            insertColAction = QAction(getIcon('tabInserColumn'), "插入列",self)
            insertColAction.triggered.connect(self.insertCol)

            mergeAction = QAction(getIcon('tabMergeCells'), "合并单元格",self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))

            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)

            splitAction = QAction(getIcon("tabSplitCells"), "拆分单元格",self)

            cell = table.cellAt(cursor)

            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:

                splitAction.triggered.connect(lambda: table.splitCell(cell.row(),cell.column(),1,1))

            else:
                splitAction.setEnabled(False)

            cellBackgroundAction = QAction(getIcon('tabCellBackground'), '修改单元格背景色', self)
            cellBackgroundAction.triggered.connect(self.modifyCellBackground)

            columnAction = QAction(getIcon('tabColWidth'), "修改列宽", self)
            columnAction.triggered.connect(self.modifyColumnPropery)

            propertyAction = QAction(getIcon('table'), "修改表格格式", self)
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

            menu.addAction(cellBackgroundAction)
            menu.addAction(columnAction)
            menu.addAction(propertyAction)

            self.showMenu(menu, pos)

        else:

            event = QContextMenuEvent(QContextMenuEvent.Mouse,QPoint())

            self.text.contextMenuEvent(event)

    @checkLock
    def showMenu(self, menu:QMenu, pos):
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

    @checkLock
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

    @checkLock
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

    @checkLock
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

    @checkLock
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

    @checkLock
    def toggleToolbar(self):

        state = self.toolbar.isVisible()

        # Set the visibility to its inverse
        self.toolbar.setVisible(not state)

    @checkLock
    def toggleFormatbar(self):

        state = self.formatbar.isVisible()

        # Set the visibility to its inverse
        self.formatbar.setVisible(not state)

    @checkLock
    def toggleStatusbar(self):

        state = self.statusbar.isVisible()

        # Set the visibility to its inverse
        self.statusbar.setVisible(not state)

    @checkLock
    def new(self):
        # spawn = Main()
        #
        # spawn.show()
        self.closeDoc()

    @checkLock
    def open(self):

        oldFileName = self.filename
        isEncryptDocument = self.text.isEncryptDocument
        changSaved = self.changesSaved

        opened = False

        def restore():
            self.filename = oldFileName
            self.text.isEncryptDocument = isEncryptDocument
            self.changesSaved = changSaved
            self.updateWindowsTitle()

        try:
            if not self.changesSaved:
                result = QMessageBox.question(self, '文件未保存', '文件未保存，是否继续打开文件？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if result == QMessageBox.StandardButton.No:
                    return restore()

            self.filename = QFileDialog.getOpenFileName(self, 'Open File', ".", "(*.writer)")[0]
            if self.filename is None or not Path(self.filename).exists() or not Path(self.filename).is_file():
                return restore()

            content = Path(self.filename).read_bytes()
            self.text.isEncryptDocument = keymanager.encryptor.is_encrypt_data(content)

            current_key = key_cache.get_cur_key()

            if self.text.isEncryptDocument:

                if current_key is None:
                    loaded = self.showLoadKeyDialog()
                    current_key = key_cache.get_cur_key()
                    if not loaded:
                        return restore()

                if current_key.timeout:
                    activated = self.showActivateKeyDialog()
                    if not activated:
                        return restore()
                    current_key = key_cache.get_cur_key()

            if self.filename:
                if self.text.isEncryptDocument:
                    encrypt_content = Path(self.filename).read_bytes()
                    content = decrypt_data(current_key.key, encrypt_content)
                else:
                    content = Path(self.filename).read_bytes()
                try:
                    html, prop = self.text.docfromBytes(content)
                except Exception as e:
                    QMessageBox.critical(self, '错误', '文件损坏或密钥不匹配\n' + str(e))
                    return restore()

                if self.text.isEncryptDocument:
                    self.defaultKeyMark = os.urandom(1024)
                    self.encryptedMark = encrypt_data(current_key.key, self.defaultKeyMark)

                self.text.documentProperty = self.text.dictToDocumentProperty(prop, self.text.documentProperty)
                self.changed(changesSaved=True)
                opened = True
        except Exception as e:
            QMessageBox.critical(self,'未知错误', str(e))
            return restore()

        if opened:
            self.text.textChanged.disconnect(self.changed)
            self.text.setText(html)
            self.text.textChanged.connect(self.changed)

    @checkLock
    def save(self):

        current_key = key_cache.get_cur_key()

        if self.text.isEncryptDocument:

            if current_key is None:
                loaded = self.showLoadKeyDialog()
                if not loaded:
                    return False
                current_key = key_cache.get_cur_key()

            if current_key.timeout:
                activated = self.showActivateKeyDialog()
                if not activated:
                    return False
                current_key = key_cache.get_cur_key()

            decryptedMark = decrypt_data(current_key.key, self.encryptedMark)

            if decryptedMark != self.defaultKeyMark:
                result = QMessageBox.question(self, '警告', '检测到打开文档使用的密钥与保存文档使用的密钥不同\n是否继续保存？',
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if result == QMessageBox.StandardButton.No:
                    return False

        if not self.filename:
          self.filename = QFileDialog.getSaveFileName(self, 'Save File')[0]

        if self.filename:
            
            # Append extension if not there yet
            if not self.filename.endswith(".writer"):
              self.filename += ".writer"

            self.text.updateEditTime()
            prop = self.text.documentPropertyToDict(self.text.documentProperty)
            content = self.text.docToBytes(self.text.toHtml(), prop)
            if self.text.isEncryptDocument:
                encrypt_content = encrypt_data(current_key.key, content)
                Path(self.filename).write_bytes(encrypt_content)
                # 重新加密，避免更换key之后每次保存都提示
                self.encryptedMark = encrypt_data(current_key.key, self.defaultKeyMark)
            else:
                Path(self.filename).write_bytes(content)

            self.changesSaved = True
            self.updateWindowsTitle()
            return True
        return False

    @checkLock
    def closeDoc(self):
        if not self.changesSaved:

            result = QMessageBox.question(self, '警告',
                                          '文档发生变化，是否需要保存？',
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if result == QMessageBox.StandardButton.Yes:
                result = self.save()
                if not result:
                    return

        self.text.clear()
        self.filename = ''
        self.text.isEncryptDocument = False
        self.changesSaved = True
        self.updateWindowsTitle()

    def showLoadKeyDialog(self):
        result = QMessageBox.question(self, '错误', '没有激活的密钥，是否需要现在加载密钥？',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if result == QMessageBox.StandardButton.Yes:
            add_key(self)
            current_key = key_cache.get_cur_key()
            if current_key is not None:
                return True
        return False

    def showActivateKeyDialog(self):
        result = QMessageBox.question(self, '错误', '密钥已经超时，是否现在激活？',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        currentKey = key_cache.get_cur_key()
        if result == QMessageBox.StandardButton.Yes:
            reload_key(currentKey, self)
            current_key = key_cache.get_cur_key()
            if current_key is not None and not current_key.timeout:
                return True
        return False

    def lock(self, key:Key=None, forceLock=False):
        locked = self.isDocumentLocked()

        currentKey = key_cache.get_cur_key() if key is None else key
        if not forceLock:
            if currentKey is None:
                result = self.showLoadKeyDialog()
                if not result:
                    return

            currentKey = key_cache.get_cur_key() if key is None else key
            if currentKey.timeout:
                result = self.showActivateKeyDialog()
                if not result:
                    return

        if locked and not forceLock:
            self.doUnLock(currentKey)
            self.setDocumentLock(False)
        elif forceLock and locked:
            pass
        else:
            self.doLock(currentKey)
            self.setDocumentLock(True)

    def isDocumentLocked(self):
        return self.lockAction.property('locked')

    def setDocumentLock(self, locked:bool):
        icon = getIcon('lock') if locked else getIcon('unlock')
        index = 1 if locked else 0
        self.lockAction.setProperty('locked', locked)
        self.lockAction.setIcon(icon)
        self.layout.setCurrentIndex(index)

    def doLock(self, key: Key):

        self.text.setEnabled(False)
        self.text.setReadOnly(True)

        for action in self.toolbar.actions():
            if action.property('alwaysEnabled'):
                continue
            action.setEnabled(False)

        for action in self.formatbar.actions():
            if action.property('alwaysEnabled'):
                continue
            action.setEnabled(False)

        for index, action in enumerate(self.menuBar().actions()):
            if action.property('alwaysEnabled'):
                continue
            action.setEnabled(False)
        text = self.text.toHtml()
        self.encrypt_text = encrypt_data(key.key, text.encode('utf-8'))
        self.text.textCursor().beginEditBlock()
        self.text.textChanged.disconnect(self.changed)
        self.text.clear()
        self.text.textChanged.connect(self.changed)
        self.text.textCursor().endEditBlock()

    def doUnLock(self, key: Key):
        text = decrypt_data(key.key, self.encrypt_text).decode('utf-8')
        self.text.textCursor().joinPreviousEditBlock()
        self.text.textChanged.disconnect(self.changed)
        self.text.setHtml(text)
        self.text.textChanged.connect(self.changed)
        self.text.textCursor().endEditBlock()

        self.text.setEnabled(True)
        self.text.setReadOnly(False)

        for action in self.toolbar.actions():
            action.setEnabled(True)

        for action in self.formatbar.actions():
            action.setEnabled(True)

        for index, action in enumerate(self.menuBar().actions()):
            action.setEnabled(True)

    @checkLock
    def preview(self):

        # Open preview dialog
        preview = QtPrintSupport.QPrintPreviewDialog()

        # If a print is requested, open print dialog
        preview.paintRequested.connect(lambda p: self.text.print_(p))

        preview.exec_()

    @checkLock
    def sysSetting(self):
        editor = systemsetting.SysSettingEditor(self)
        editor.exec()
        editor.destroy()

    @checkLock
    def editProperty(self):
        prop = PropertyEditor(self.text)
        prop.propertySaved.connect(lambda : self.changed())
        prop.exec()
        prop.destroy()

    @checkLock
    def keyManager(self):
        kmd = KeyMgrDialog()
        kmd.exec()
        kmd.destroy()

    @checkLock
    def printHandler(self):

        # Open printing dialog
        dialog = QtPrintSupport.QPrintDialog()

        if dialog.exec_() == QDialog.Accepted:
            self.text.document().print_(dialog.printer())

    def cursorPosition(self):

        if self.systemSetting.resetTimeoutOnSelect:
            currentKey = key_cache.get_cur_key()
            if currentKey is not None and not currentKey.timeout:
                currentKey.touch()

        self.updateFormatBarIcon()

        cursor = self.text.textCursor()

        # Mortals like 1-indexed things
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()

        message = "Line: {} | Column: {}".format(line,col)
        if cursor.hasSelection():
            font = self.text.currentFont()
            family = font.family()
            size = font.pointSize()
            bold = font.bold()
            italic = font.italic()
            message += " | 字体：{} 字号：{} ".format(family, size) + (' 加粗' if bold else '') + (' 斜体' if italic else '')

        self.statusbar.showMessage(message)

    def updateFormatBarIcon(self):
        # TODO 需要处理从右向左选择时的属性
        backgroundColor = self.text.textBackgroundColor()
        font = self.text.currentFont()
        size = font.pointSize()
        color = self.text.textColor()
        bold = font.bold()
        italic = font.italic()
        underLine = font.underline()
        strike = font.strikeOut()

        format = self.text.currentCharFormat()
        alignSuper = format.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSuperScript
        alignSub = format.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSubScript

        @lru_cache(maxsize=128)
        def getFormatbarIcon(name:str, colorName:str, status:bool):
            iconOpt = getIconOpt(name)
            iconOpt = (iconOpt if iconOpt is not None else [{}])
            names = getIconName(name)
            if name == 'fontColor':
                iconOpt[1]['color'] = colorName
            elif name == 'backColor':
                iconOpt[1]['color'] = colorName
            elif name in ('bold', 'italic', 'underl', 'strike', 'super', 'sub'):
                if status:
                    iconOpt = getIconOpt('pressed') + (iconOpt if iconOpt is not None else [{'color': '#393D49'}])
                    names = getIconName('pressed') + names
            iconOpt = addDefaultColorToFontOptions(iconOpt)
            return qta.icon(*names, options=iconOpt)

        self.fontColor.setIcon(getFormatbarIcon('fontColor', color.name(), True))
        self.backColor.setIcon(getFormatbarIcon('backColor', backgroundColor.name(), True))

        self.boldAction.setIcon(getFormatbarIcon('bold', ' ', bold))
        self.italicAction.setIcon(getFormatbarIcon('italic', ' ', italic))
        self.underlAction.setIcon(getFormatbarIcon('underl', ' ', underLine))
        self.strikeAction.setIcon(getFormatbarIcon('strike', ' ', strike))
        self.superAction.setIcon(getFormatbarIcon('super', ' ', alignSuper))
        self.subAction.setIcon(getFormatbarIcon('sub', ' ', alignSub))

        try:
            self.fontSize.blockSignals(True)
            self.fontBox.blockSignals(True)
            self.fontSize.setValue(size)
            self.fontBox.setCurrentFont(font)
        finally:
            self.fontSize.blockSignals(False)
            self.fontBox.blockSignals(False)

    @checkLock
    def wordCount(self):
        wc = wordcount.WordCount(self)
        wc.getText()
        wc.show()

    @checkLock
    def insertImage(self):

        # Get image file name
        #PYQT5 Returns a tuple in PyQt5
        filename = QFileDialog.getOpenFileName(self, 'Insert image',".","Images (*.png *.xpm *.jpg *.bmp *.gif *.svg)")[0]

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

    @checkLock
    def fontColorChanged(self):
        color = QColorDialog.getColor()
        self.text.setTextColor(color)
        self.updateFormatBarIcon()

    @checkLock
    def changeBackgroundColor(self):

        color = QColorDialog.getColor()
        self.text.setTextBackgroundColor(color)
        self.updateFormatBarIcon()

    @checkLock
    def insertTable(self):
        dialog = table.TableEditor(self.text)
        dialog.exec_()
        dialog.destroy()

    @checkLock
    def modifyTableProperty(self):
        dialog = table.TableEditor(self.text)
        dialog.setCurrentFormat(self.text.textCursor().currentTable().format())
        dialog.updateValue()
        dialog.exec_()
        dialog.destroy()

    @checkLock
    def modifyColumnPropery(self):
        dialog = table.ColumnEditor(self.text)
        dialog.exec_()
        dialog.destroy()

    def modifyCellBackground(self):
        table.setCellsBackgroundColor(self.text)

    @checkLock
    def copySourceCode(self):
        #self.text.insertHtml('<h1>标题一</h1>')
        # self.text.textCursor().beginEditBlock()
        # text = self.text.textCursor().selectedText()
        # self.text.textCursor().insertHtml('<h1>' + text + '</h1>')
        # self.text.textCursor().endEditBlock()
        # self.text.textCursor().insertHtml('<code>var i = "1"</code>')
        # self.text.textCursor().insertHtml('<cite>fffffffffffffffffffffffffffff</cite>')
        # textList = self.text.textCursor().currentList()
        # textListCnt = textList.count()
        # for i in range(textListCnt):
        #     block = textList.item(i)
        #     print(block.text())
        #print(self.text.textCursor().selection().toHtml())

        #self.text.insertHtml('<h3>标题三</h3>')

        print(self.text.toHtml())

    @checkLock
    def openEmoji(self):

        if self.emoji_browser is None:
            self.emoji_browser = emo.IconBrowser()
            self.emoji_browser.emojiSelected.connect(lambda char: self.text.textCursor().insertText(char))

        if self.emoji_browser.isVisible():
            return

        self.emoji_browser.show()

    @checkLock
    def insertQuote(self):
        dialog = quote.Quote(self.text)
        dialog.exec_()
        dialog.destroy()

    @checkLock
    def modifyQuotePropery(self):
        dialog = quote.Quote(self.text)
        dialog.setCurrentFormat(self.text.textCursor().currentFrame().format().toFrameFormat())
        dialog.updateValue()
        dialog.exec_()
        dialog.destroy()

    @checkLock
    def font(self, font:QFont):
        currentFont = self.text.currentFont()
        currentFont.setFamily(font.family())
        self.text.setCurrentFont(currentFont)
        self.updateFormatBarIcon()

    @checkLock
    def bold(self):
        if self.text.fontWeight() == QFont.Bold:
            self.text.setFontWeight(QFont.Normal)
        else:
            self.text.setFontWeight(QFont.Bold)

        self.updateFormatBarIcon()

    @checkLock
    def italic(self):
        state = self.text.fontItalic()
        self.text.setFontItalic(not state)
        self.updateFormatBarIcon()

    @checkLock
    def underline(self):
        state = self.text.fontUnderline()
        self.text.setFontUnderline(not state)
        self.updateFormatBarIcon()

    @checkLock
    def strike(self):

        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # And set the next char format
        self.text.setCurrentCharFormat(fmt)
        self.updateFormatBarIcon()

    @checkLock
    def superScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QTextCharFormat.VerticalAlignment.AlignNormal:

            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)

        else:

            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)
        self.updateFormatBarIcon()

    @checkLock
    def subScript(self):

        # Grab the current format
        fmt = self.text.currentCharFormat()

        # And get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QTextCharFormat.VerticalAlignment.AlignNormal:

            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)

        else:

            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)
        self.updateFormatBarIcon()

    @checkLock
    def alignLeft(self):
        self.text.setAlignment(Qt.AlignLeft)

    @checkLock
    def alignRight(self):
        self.text.setAlignment(Qt.AlignRight)

    @checkLock
    def alignCenter(self):
        self.text.setAlignment(Qt.AlignCenter)

    @checkLock
    def alignJustify(self):
        self.text.setAlignment(Qt.AlignJustify)

    @checkLock
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

    @checkLock
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

    @checkLock
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

    @checkLock
    def bulletList(self):

        cursor = self.text.textCursor()

        # Insert bulleted list
        cursor.insertList(QTextListFormat.ListDisc)

    @checkLock
    def numberList(self):

        cursor = self.text.textCursor()

        # Insert list with numbers
        cursor.insertList(QTextListFormat.ListDecimal)

    @checkLock
    def head(self, headButton:QToolButton, action:QAction):
        level = action.property('level')
        selection = self.text.getSelection()
        self.text.textCursor().beginEditBlock()
        text = self.text.textCursor().selectedText()
        headLevel = level
        insertHtml = '<h%s>%s</h%s>' % (headLevel, text, headLevel)
        self.text.textCursor().insertHtml(insertHtml)
        self.text.textCursor().endEditBlock()
        self.text.setSelection(selection)
        headButton.setDefaultAction(action)

    @checkLock
    def highlight(self, toolButton:QToolButton, action: QAction):
        toolButton.setDefaultAction(action)
        if self.text.textCursor().hasSelection():
            format = self.text.currentCharFormat()
            if format.isImageFormat():
                return
            self.text.setTextBackgroundColor(QColor(255, 255, 153))
            self.text.setTextColor(QColor(120, 35, 12))
            self.text.setFontWeight(700)

    @checkLock
    def highlightUnderline(self, toolButton:QToolButton, action: QAction):
        toolButton.setDefaultAction(action)
        if self.text.textCursor().hasSelection():
            format = self.text.currentCharFormat()
            if format.isImageFormat():
                return
            self.text.setCurrentCharFormat(format)
            self.text.setTextColor(QColor(120, 35, 12))
            self.text.setFontUnderline(True)
            self.text.setTextBackgroundColor(QColor(255, 255, 153))
            self.text.setFontWeight(700)

    @checkLock
    def clearFormat(self):

        fmt = self.text.currentCharFormat()
        fmt.setFontStrikeOut(False)
        fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        self.text.setCurrentCharFormat(fmt)

        self.text.setFontWeight(QFont.Normal)
        self.text.setFontItalic(False)
        self.text.setFontUnderline(False)
        self.text.setTextBackgroundColor(QColor(255, 255, 255))
        self.text.setTextColor(QColor(0, 0, 0))


def main():
    key_checker['timeout'] = 600
    start_check_key_thread()
    add_key_invalidate_callback(lambda key: print('key超时'))

    from keymanager import utils
    utils.external_module_name = 'writer.settings'
    utils.get_icon_name_func_name = 'getIconName'
    utils.get_icon_func_name = 'getIcon'
    utils.get_icon_opt_func_name = 'getIconOpt'

    app = QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
