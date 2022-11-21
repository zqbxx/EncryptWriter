import copy
import json
import os
import shutil
from pathlib import Path
from typing import Any

import qtawesome as qta
from PySide6.QtGui import QIcon
from deepdiff import DeepDiff

SETTING_FILE = './config/settings.json'
SETTING_FILE_BACKUP = './config/settings.json.backup'


class Settings:

    def __init__(self) -> None:
        self.d: [dict[str, str]] = dict()
        self.read()
        self.original = copy.deepcopy(self.d)

    def read(self):
        try:
            with open(SETTING_FILE) as f:
                self.d = json.load(f)
        except:
            self.d = dict()
        finally:
            self._setDefault()

    def _setDefault(self):
        if 'keyTimeout' not in self.d:
            self.d['keyTimeout'] = 600
        if 'autoLockDoc' not in self.d:
            self.d['autoLockDoc'] = True
        if 'resetTimeoutOnSelect' not in self.d:
            self.d['resetTimeoutOnSelect'] = True
        if 'webcam' not in self.d:
            self.d['webcam'] = {}

    def _makeDir(self) -> None:
        folder = Path(SETTING_FILE).parent
        if not folder.is_dir():
            folder.mkdir(parents=True)

    def write(self) -> None:
        diff = DeepDiff(self.d, self.original, ignore_order=True)
        if len(diff) == 0:
            return
        self._makeDir()
        with open(SETTING_FILE_BACKUP, "w") as f:
            json.dump(self.d, f, indent=2)
        if os.path.getsize(SETTING_FILE_BACKUP) > 0:
            shutil.move(SETTING_FILE_BACKUP, SETTING_FILE)

    @property
    def keyTimeout(self) -> int:
        return self.d['keyTimeout']

    @keyTimeout.setter
    def keyTimeout(self, timeout:int):
        self.d['keyTimeout'] = timeout

    @property
    def autoLockDoc(self) -> bool:
        return self.d['autoLockDoc'] == 'True'

    @autoLockDoc.setter
    def autoLockDoc(self, auto: bool):
        self.d['autoLockDoc'] = 'True' if auto else 'False'

    @property
    def resetTimeoutOnSelect(self) -> bool:
        return self.d['resetTimeoutOnSelect'] == 'True'

    @resetTimeoutOnSelect.setter
    def resetTimeoutOnSelect(self, reset: bool):
        self.d['resetTimeoutOnSelect'] = 'True' if reset else 'False'

    @property
    def webcams(self):
        return copy.deepcopy(self.d['webcam'])

    def isWebcamExists(self, name:str):
        return name in self.d['webcam']

    def addWebcam(self, name: str, webcam: dict):
        self.d['webcam'][name] = webcam

    def removeWebcam(self, name:str):
        if self.isWebcamExists(name):
            del self.d['webcam'][name]


IconNames = {

    # 工具栏
    'new': 'ei.file-new',
    'open': 'ei.folder-open',
    'save': 'fa.save',
    'saveas': 'msc.save-as',
    'close': 'fa.close',
    'print': 'ei.print',
    'preview': 'msc.open-preview',
    'sysSetting': 'ri.settings-3-line',
    'property': 'ri.file-info-fill',
    'keyMgr': 'fa5s.key',
    'find': 'ei.search',
    'cut': 'fa.cut',
    'copy': 'fa.copy',
    'paste': 'fa.paste',
    'undo': 'fa5s.undo',
    'redo': 'fa5s.redo',
    'clearUndoRedo': ['ei.refresh', 'fa.remove'],
    'dateTime': 'mdi.clock-time-eight-outline',
    'wordCount': ['msc.symbol-string', 'fa5s.hand-point-up'],
    'table': 'ph.table',
    'image': 'fa.image',
    'camera': 'ei.camera',
    'bullet': 'mdi.format-list-bulleted',
    'numbered': 'fa.list-ol',
    'code': 'fa.code',
    'emoji': 'fa5s.smile-wink',
    'quote': 'ri.chat-quote-fill',

    # 格式
    'fontColor': ['fa.font', 'fa.minus',],
    'backColor': ['mdi.square-rounded', 'mdi.square-rounded', 'mdi.square-rounded-outline', 'mdi.square-rounded'],
    'bold': 'fa5s.bold',
    'pressed': ['fa5s.square-full', 'fa5s.square-full', ],
    'italic': 'ei.italic',
    'underl': 'fa5s.underline',
    'strike': 'fa5s.strikethrough',
    'super': 'fa5s.superscript',
    'sub': 'fa5s.subscript',
    'alignLeft' : 'ei.align-left',
    'alignCenter': 'ei.align-center',
    'alignRight': 'ei.align-right',
    'alignJustify': 'ei.align-justify',
    'indent': 'fa.indent',
    'dedent': 'fa.dedent',
    'h0': 'fa.remove',
    'h1': 'mdi.format-header-1',
    'h2': 'mdi.format-header-2',
    'h3': 'mdi.format-header-3',
    'h4': 'mdi.format-header-4',
    'highlight': 'mdi.draw',
    'highlight1': 'fa5s.highlighter',
    'highlight2': ['mdi.format-color-highlight', 'mdi.border-bottom-variant'],
    'clear': 'mdi.format-clear',

    # 状态栏
    'unlock': 'fa5s.unlock',
    'lock': 'fa5s.lock',

    # 菜单
    'imageSetting': 'mdi.resize',
    'imageExport': 'msc.save-as',

    # 表格
    'tableColumn': 'mdi.table-column',
    'tabColPerWidth': 'fa.percent',
    'tabColFixWidth': 'mdi.numeric',
    'tabColVarWidth': 'mdi.variable',

    'tabColWidth': 'mdi.table-column-width',
    'tabCellBackground': 'ph.selection-background',
    'tabAppendRow': 'mdi6.table-row-plus-after',
    'tabInsertRow': 'mdi6.table-row-plus-before',
    'tabRemoveRow': 'mdi6.table-row-remove',
    'tabAppendColumn': 'mdi6.table-column-plus-after',
    'tabInserColumn': 'mdi6.table-column-plus-before',
    'tabRemoveColumn': 'mdi6.table-column-remove',
    'tabMergeCells': 'mdi.set-merge',
    'tabSplitCells': 'mdi.set-split',

    'webcam': ('mdi.webcam'),
    'webcamAdd': ('mdi.webcam', 'ri.add-circle-fill'),
    'webcamRemove': ('mdi.webcam', 'fa.remove'),
    'camRefresh': ('ei.camera', 'fa.refresh')

}

IconOpts = {

    'unlock': [{'scale_factor': 0.85, 'color': '#009688'}],
    'lock':[{'scale_factor': 0.85, 'color': '#660033'}],
    'fontColor': [{'scale_factor': 0.7, 'offset': (0, -0.1)}, {'color': 'black', 'offset': (0, 0.35)}],
    'backColor': [{'scale_factor': 0.8, 'offset': (0.1, 0.1)}, {'scale_factor': 0.7, 'offset': (0.1, 0.1)},{'scale_factor': 0.8, 'offset': (-0.1, -0.1)}, {'color':'white', 'scale_factor': 0.7, 'offset': (-0.1, -0.1)}],
    'highlight1': [{'scale_factor': 0.8, }],
    'highlight2': [{'scale_factor': 0.7, }, {'scale_factor': 1.1, }],
    'clearUndoRedo':[
        {'scale_factor': 1, 'rotated': 0, 'offset': (-0.1, 0)},
        {'scale_factor': 0.7, 'offset': (0.2, 0.2), 'color': '#993324', 'opacity': 0.9, }
    ],
    'wordCount': [
        {'scale_factor': 1.2, 'offset': (0,-0.06)},
        {'scale_factor': 0.7, 'rotated': -30, 'offset':(0.1,0.35), 'opacity': 0.9, 'color': '#993324'},
    ],
    'table': [{'scale_factor': 1.3, 'color': '#009688'}],
    'quote': [{'color': '#cca331'}],
    'emoji': [{'scale_factor': 0.9, 'color': '#1E9FFF'}, ],
    'property': [{'color': '#993324'},],
    'pressed':[
        {'color': '#b7c2cc', 'scale_factor': 1.2},
        {'color': '#e5f3ff', 'scale_factor': 1.1,},
    ],

    # 密钥模块
    'add_key':[{'color': ''}, {}],
    'create_key':[{'color': ''}, {}, {}],
    'manage_key':[{'color': ''},],

    'webcamAdd':[
        {'offset': (-0.1, -0.15), 'scale_factor':0.9, },
        {'scale_factor': 0.68, 'offset': (0.25, 0.2), 'color': '#59a869'}
    ],
    'webcamRemove':[
        {'offset': (-0.1, -0.15), 'scale_factor':0.9, },
        {'scale_factor': 0.68, 'offset': (0.25, 0.2), 'color': '#db5860'}
    ],
    'camRefresh':[
        {'offset': (-0.1, -0.15), 'scale_factor':0.9, },
        {'scale_factor': 0.68, 'offset': (0.25, 0.2), 'color': '#1E9FFF'}
    ]

}

DocumentProperties = {
    'author': {
        'display': '作者',
        'value': '',
        'internal': False,
    },
    'createDatetime': {
        'display': '创建时间',
        'value': '',
        'internal': True,
    },
    'editDatetime': {
        'display': '修改时间',
        'value': '',
        'internal': True,
    },
    'title': {
        'display': '标题',
        'value': '',
        'internal': False,
    },
    'remarks': {
        'display': '备注',
        'value': '',
        'internal': False,
    },
}

SymbolEmojis = {
    '圆形':['🔴', '🔵', '🟠', '🟡', '🟢', '🟣', '🟤', '⚫', '⚪', '🔘','⭕'],
    '正方形':['🟥','🟦','🟧','🟨','🟩','🟪','🟫','🏿','🏾','🏽','🏼','🏻'],
    '选项1':['☑', '✔','✖','◻','◼'],
    '选项2':['✅','⬜','❌','❎','🟩','🔲','🔳'],
    '符号1':['🔶','🔷','🔸','🔹'],
    '符号2':['◽','◾','▪','▫'],
    '其他':['⭐']
}


def getIcon(name: str) -> QIcon:
    iconNames = getIconName(name)
    if iconNames is None:
        return None
    iconOpt = getIconOpt(name)
    if iconOpt is None:
        return qta.icon(*iconNames, options=[{'color':'#393D49'}])
    iconOpt = addDefaultColorToFontOptions(iconOpt)
    return qta.icon(*iconNames, options=iconOpt)


def addDefaultColorToFontOptions(iconOpt):
    for opt in iconOpt:
        if not 'color' in opt:
            opt['color'] = '#393D49'
    return iconOpt


def getIconName(name: str) -> list[dict[str, str]]:
    if not name in IconNames:
        return None
    iconNames = IconNames[name]
    if type(iconNames) is str:
        return [IconNames[name], ]
    elif type(iconNames) is tuple or type(iconNames) is list:
        return iconNames
    return None


def getIconOpt(name: str) -> tuple[dict[str, Any]]:
    if name in IconOpts:
        return IconOpts.get(name)
    return None


def getSymbolEmojiType(char: str):
    for type, symbols in SymbolEmojis.items():
        for symbol in symbols:
            if symbol == char:
                return  type
    return None