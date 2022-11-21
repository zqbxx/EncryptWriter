import sys
import threading

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Signal
from PySide6.QtGui import QShortcut, QFont

from writerlib.widgets import checkLock
from .settings import getIcon

VIEW_COLUMNS = 10
AUTO_SEARCH_TIMEOUT = 500
ALL_COLLECTIONS = 'All'


class EmojiBrowser(QtWidgets.QMainWindow):

    EmojiChar = None

    @classmethod
    def isEmojiChars(cls, char: str):
        if cls.EmojiChar is None:
            cls.initEmojiChar()
        return char in cls.EmojiChar

    zero_width_char = [u'\u200c', u'\u200d', u'\u200e', u'\u200f', u'\ufeff']

    @classmethod
    def initEmojiChar(cls):
        from emoji_data_python import emoji_data
        if cls.EmojiChar is None:
            cls.EmojiChar = []
            for data in emoji_data:
                string = data.char
                cls.EmojiChar.append(string)

    emojiSelected = Signal(str)

    def __init__(self, parent):
        from emoji_data_python import emoji_data
        super().__init__(parent)

        if EmojiBrowser.EmojiChar is None:
            threading.Thread(target=EmojiBrowser.initEmojiChar).start()

        self._parentWidget = parent

        self.setMinimumSize(800, 600)
        self.setWindowTitle('表情选择器')
        self.setWindowIcon(getIcon('emoji'))

        self.emojiNames = []
        self.emojiInfo = []
        self.updateEmojiData(ALL_COLLECTIONS)
        self.groupNames = list(set([c.category for c in emoji_data]))
        #self.groupNames = []
        self._filterTimer = QtCore.QTimer(self)
        self._filterTimer.setSingleShot(True)
        self._filterTimer.setInterval(AUTO_SEARCH_TIMEOUT)
        self._filterTimer.timeout.connect(self._updateFilter)

        self.emoji_model = IconModel()
        self.emoji_model.setStringList(self.emojiNames)

        list_font = QFont()
        list_font.setPointSize(30)

        self._listView = IconListView(self)
        self._listView.setFont(list_font)
        self._listView.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self._listView.setViewMode(QtWidgets.QListView.IconMode)
        self._listView.setModel(self.emoji_model)
        self._listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._listView.doubleClicked.connect(self._copyIconText)
        self._listView.selectionModel().selectionChanged.connect(self._updateNameField)

        css = 'QListView::item { border: 0.6px solid #0099CC; background-color:#f6f9fc; margin:1px}'
        css += 'QListView::item:hover { background-color: #FFFFCC;}'
        css += 'QListView::item:selected { color: black;}'
        css += 'QListView {background-color:#f6f9fc;}'

        self._listView.setStyleSheet(css)

        self._lineEdit = QtWidgets.QLineEdit(self)
        self._lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self._lineEdit.textChanged.connect(self._triggerDelayedUpdate)
        self._lineEdit.returnPressed.connect(self._triggerImmediateUpdate)

        self._comboBox = QtWidgets.QComboBox(self)
        self._comboBox.setMinimumWidth(100)
        self._comboBox.currentIndexChanged.connect(self._triggerImmediateUpdate)
        self._comboBox.addItems([ALL_COLLECTIONS] + self.groupNames)

        lyt = QtWidgets.QHBoxLayout()
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self._comboBox)
        lyt.addWidget(self._lineEdit)

        searchBarFrame = QtWidgets.QFrame(self)
        searchBarFrame.setLayout(lyt)

        self._nameField = QtWidgets.QLineEdit(self)
        self._nameField.setAlignment(QtCore.Qt.AlignCenter)
        self._nameField.setReadOnly(True)

        #self._copyButton = QtWidgets.QPushButton('Copy Name', self)
        #self._copyButton.clicked.connect(self._copyIconText)

        lyt = QtWidgets.QVBoxLayout()
        lyt.addWidget(searchBarFrame)
        lyt.addWidget(self._listView)
        lyt.addWidget(self._nameField)
        #lyt.addWidget(self._copyButton)

        frame = QtWidgets.QFrame(self)
        frame.setLayout(lyt)

        self.setCentralWidget(frame)

        self.setTabOrder(self._comboBox, self._lineEdit)
        self.setTabOrder(self._lineEdit, self._listView)
        self.setTabOrder(self._listView, self._nameField)
        self.setTabOrder(self._nameField, self._comboBox)

        QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Return),
            self,
            self._copyIconText,
        )

        geo = self.geometry()

        # QApplication.desktop() has been removed in Qt 6.
        # Instead, QGuiApplication.screenAt(QPoint) is supported
        # in Qt 5.10 or later.
        try:
            screen = QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos())
            centerPoint = screen.geometry().center()
        except AttributeError:
            desktop = QtWidgets.QApplication.desktop()
            screen = desktop.screenNumber(desktop.cursor().pos())
            centerPoint = desktop.screenGeometry(screen).center()

        geo.moveCenter(centerPoint)
        self.setGeometry(geo)

    def _updateFilter(self):
        """
        Update the string used for filtering in the proxy model with the
        current text from the line edit.
        """
        reString = ""

        group = self._comboBox.currentText()
        keyword = self._lineEdit.text().strip()
        self.updateEmojiData(group, keyword)
        self.emoji_model.setStringList(self.emojiNames)

        # QSortFilterProxyModel.setFilterRegExp has been removed in Qt 6.
        # Instead, QSortFilterProxyModel.setFilterRegularExpression is
        # supported in Qt 5.12 or later.

    def updateEmojiData(self, group, keyword=None):
        from emoji_data_python import emoji_data
        self.emojiNames = []
        self.emojiInfo = []
        if group != ALL_COLLECTIONS:
            if keyword is None:
                self.emojiNames = [c.char for c in emoji_data if c.category == group]
                self.emojiInfo = [c.short_names for c in emoji_data if c.category == group]
            else:
                self.emojiNames = [c.char for c in emoji_data if c.category == group and self.isTextInArray(keyword, c.short_names)]
                self.emojiInfo = [c.short_names for c in emoji_data if c.category == group and self.isTextInArray(keyword, c.short_names)]
        else:
            if keyword is None:
                self.emojiNames = [c.char for c in emoji_data]
                self.emojiInfo = [c.short_names for c in emoji_data]
            else:
                self.emojiNames = [c.char for c in emoji_data if self.isTextInArray(keyword, c.short_names)]
                self.emojiInfo = [c.short_names for c in emoji_data if self.isTextInArray(keyword, c.short_names)]

    def isTextInArray(self, text, textArray):
        for t in textArray:
            if t.find(text) >= 0:
                return True
        return False

    def _triggerDelayedUpdate(self):
        """
        Reset the timer used for committing the search term to the proxy model.
        """
        self._filterTimer.stop()
        self._filterTimer.start()


    def _triggerImmediateUpdate(self):
        """
        Stop the timer used for committing the search term and update the
        proxy model immediately.
        """
        self._filterTimer.stop()
        self._updateFilter()

    @checkLock
    def _copyIconText(self, _):
        """
        Copy the name of the currently selected icon to the clipboard.
        """
        indexes = self._listView.selectedIndexes()
        if not indexes:
            return

        charToInsert = indexes[0].data()
        self.emojiSelected.emit(charToInsert)


    def _updateNameField(self):
        """
        Update field to the name of the currently selected icon.
        """
        indexes = self._listView.selectedIndexes()
        if not indexes:
            self._nameField.setText("")
        else:
            self._nameField.setText(",".join(self.emojiInfo[indexes[0].row()]))


class IconListView(QtWidgets.QListView):
    """
    A QListView that scales it's grid size to ensure the same number of
    columns are always drawn.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def resizeEvent(self, event):
        """
        Re-implemented to re-calculate the grid size to provide scaling icons
        Parameters
        ----------
        event : QtCore.QEvent
        """
        width = self.viewport().width() - 30
        # The minus 30 above ensures we don't end up with an item width that
        # can't be drawn the expected number of times across the view without
        # being wrapped. Without this, the view can flicker during resize
        tileWidth = width / VIEW_COLUMNS
        iconWidth = int(tileWidth * 0.8)
        # tileWidth needs to be an integer for setGridSize
        tileWidth = int(tileWidth)

        #self.setGridSize(QtCore.QSize(tileWidth, tileWidth))
        #self.setIconSize(QtCore.QSize(iconWidth, iconWidth))

        return super().resizeEvent(event)


class IconModel(QtCore.QStringListModel):

    def __init__(self):
        super().__init__()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        return super().data(index, role)


def run():
    """
    Start the IconBrowser and block until the process exits.
    """
    app = QtWidgets.QApplication([])
    #qtawesome.dark(app)

    browser = EmojiBrowser()
    browser.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    run()