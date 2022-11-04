import qtawesome as qta

icon_names = {

    # 工具栏
    'new': 'ei.file-new',
    'open': 'ei.folder-open',
    'save': 'fa.save',
    'print': 'ei.print',
    'preview': 'msc.open-preview',
    'keyMgr': 'fa5s.key',
    'find': 'ei.search',
    'cut': 'fa.cut',
    'copy': 'fa.copy',
    'paste': 'fa.paste',
    'undo': 'fa5s.undo',
    'redo': 'fa5s.redo',
    'dateTime': 'fa.calendar',
    'wordCount': 'mdi.calculator',
    'table': 'fa.table',
    'image': 'fa.image',
    'bullet': 'mdi.format-list-bulleted',
    'numbered': 'fa.list-ol',
    'code': 'fa.code',
    'emoji': 'mdi.sticker-emoji',
    'quote': 'ri.chat-quote-line',

    # 格式
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
    'backColor': 'mdi6.format-color-fill',
}


def getIcon(name: str):
    if name == 'fontColor':
        return qta.icon('fa.font', 'mdi6.select-color', options=[{'scale_factor': 0.8,}, {'color': 'black', 'scale_factor': 1.7}])
    if name == 'backColor':
        return qta.icon("mdi6.format-color-fill", options=[{'scale_factor': 1.5, },])
    return qta.icon(icon_names[name])