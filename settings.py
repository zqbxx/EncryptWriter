import qtawesome as qta

icon_names = {

    # 工具栏
    'new': 'ei.file-new',
    'open': 'ei.folder-open',
    'save': 'fa.save',
    'print': 'ei.print',
    'preview': 'msc.open-preview',
    'property': 'ri.file-info-fill',
    'keyMgr': 'fa5s.key',
    'find': 'ei.search',
    'cut': 'fa.cut',
    'copy': 'fa.copy',
    'paste': 'fa.paste',
    'undo': 'fa5s.undo',
    'redo': 'fa5s.redo',
    'clearUndoRedo': ('ei.refresh', 'fa.remove'),
    'dateTime': 'mdi.clock-time-eight-outline',
    'wordCount': ('msc.symbol-string', 'fa5s.hand-point-up'),
    'table': 'ph.table',
    'image': 'fa.image',
    'bullet': 'mdi.format-list-bulleted',
    'numbered': 'fa.list-ol',
    'code': 'fa.code',
    'emoji': 'fa5s.smile-wink',
    'quote': 'ri.chat-quote-line',

    # 格式
    'fontColor': ('fa.font', 'mdi6.select-color'),
    'backColor': 'mdi6.format-color-fill',
    'bold': 'ei.bold',
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
    'highlight2': ('mdi.format-color-highlight', 'mdi.border-bottom-variant'),
    'clear': 'mdi.format-clear',

    # 状态栏
    'unlock': 'ei.unlock',
    'lock': 'ei.lock',

    # 菜单
    'imageSetting': 'mdi.resize',
    'imageExport': 'msc.save-as',

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
}

icon_opts = {

    'unlock': [{'color': '#006600'}],
    'lock':[{'color': '#660033'}],
    'fontColor': [{'scale_factor': 0.8, }, {'color': 'black', 'scale_factor': 1.7}],
    'backColor': [{'scale_factor': 1.5, }, ],
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
    'table': [{'scale_factor': 1.3}, ],

}

document_properties = {
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


def getIcon(name: str):
    iconNames = getIconName(name)
    iconOpt = getIconOpt(name)
    return qta.icon(*iconNames, options=iconOpt)


def getIconName(name: str):
    iconNames = icon_names[name]
    if type(iconNames) is str:
        return (icon_names[name],)
    elif type(iconNames) is tuple:
        return iconNames
    return None


def getIconOpt(name: str):
    return icon_opts.get(name, [{'scale_factor': 1,}])