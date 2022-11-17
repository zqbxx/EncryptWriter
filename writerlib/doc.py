from io import BytesIO
from typing import List, TypeVar


DocHeadType = TypeVar("DocHeadType", bound="DocHead")
DocInfoBlockType = TypeVar("DocInfoBlockType", bound="DocInfoBlock")
DocBodyType = TypeVar("DocBodyType", bound="DocBody")
DocFileType = TypeVar("DocFileType", bound="DocFile")


class CorruptFileException(Exception):
    pass


def pad(data: bytes, length: int, pad: bytes) -> bytes:
    dataLen = len(data)
    padLen = length - dataLen
    if padLen <= 0:
        return data[:length]
    return padLen * pad + data


def unpad(data: bytes, pad: bytes) -> bytes:
    result = bytearray(b'')
    dataArray = [b'%c' % i for i in data]
    for b in dataArray:
        if b == pad:
            continue
        result += b
    return bytes(result)


def readInt(length: int, bis: BytesIO) -> int:
    b = bis.read(length)
    if len(b) != length:
        raise CorruptFileException('预期读取个%d字节，实际读取%d个字节' % (length, len(b)))
    i = int.from_bytes(b, byteorder='big')
    return i


def readBytes(length: int, bis:BytesIO) -> bytes:
    b = bis.read(length)
    if len(b) != length:
        raise CorruptFileException('预期读取个%d字节，实际读取%d个字节' % (length, len(b)))
    return b

class DocHead:

    DocTypeBytesLen = 2
    DocInfoBlockCountBytesLen = 4
    DocInfoBlockBytesLen = 5
    DocBodyBytesLen = 7

    class DocType:
        Writer = 1

    def __init__(self):
        self.docType:int = None
        self.docInfoBlockLen: List[int] = list()
        self.docBodyLen: int = 0

    def toBytesIO(self, bos:BytesIO=None) -> BytesIO:
        bos = BytesIO() if bos is None else bos
        blockCount = len(self.docInfoBlockLen)
        bos.write(blockCount.to_bytes(self.DocInfoBlockCountBytesLen, byteorder='big'))
        bos.write(self.docType.to_bytes(self.DocTypeBytesLen, byteorder='big'))
        for blockLen in self.docInfoBlockLen:
            bos.write(blockLen.to_bytes(self.DocInfoBlockBytesLen, byteorder='big'))
        bos.write(self.docBodyLen.to_bytes(self.DocBodyBytesLen, byteorder='big'))
        return bos

    @classmethod
    def fromBytes(cls, data: bytes) -> DocHeadType:
        head = DocHead()
        bis = BytesIO(data)
        blockCount = readInt(cls.DocInfoBlockCountBytesLen, bis)
        head.docType = readInt(cls.DocTypeBytesLen, bis)
        for index in range(blockCount):
            blockLen = readInt(cls.DocInfoBlockBytesLen, bis)
            head.docInfoBlockLen.append(blockLen)
        head.docBodyLen = readInt(cls.DocBodyBytesLen, bis)
        return head

    @staticmethod
    def getDocInfoBlockCount(bis:BytesIO):
        position = bis.tell()
        blockCount = readInt(DocHead.DocInfoBlockCountBytesLen, bis)
        bis.seek(position)
        return blockCount

    @staticmethod
    def getHeadBlockBytesLen(blockCount:int):
        return DocHead.DocInfoBlockCountBytesLen \
        + DocHead.DocTypeBytesLen \
        + blockCount * DocHead.DocInfoBlockBytesLen  \
        + DocHead.DocBodyBytesLen  \


class DocInfoBlock:

    nameLen = 1024

    padData = b'\0'

    def __init__(self):
        self.name: bytes = None
        self.value: bytes = None

    def toByteIO(self, bos:BytesIO=None) -> BytesIO:
        bos = BytesIO() if bos is None else bos
        bos.write(pad(self.name, self.nameLen, self.padData))
        bos.write(self.value)
        return bos

    def getByteLen(self):
        return self.nameLen + len(self.value)

    @classmethod
    def fromBytes(cls, data: bytes) -> DocInfoBlockType:
        bis = BytesIO(data)
        block = DocInfoBlock()
        bName = readBytes(cls.nameLen, bis)
        block.name = unpad(bName, cls.padData)
        block.value = bis.read()
        return block



class DocBody:

    def __init__(self):
        self.content: bytes = None

    def toByteIO(self, bos:BytesIO=None) -> BytesIO:
        bos = BytesIO() if bos is None else bos
        bos.write(self.content)
        return bos

    @classmethod
    def fromBytes(cls, data: bytes) -> DocBodyType:
        bis = BytesIO(data)
        docBody = DocBody()
        docBody.content = bis.read()
        return docBody


class DocFile:

    def __init__(self):
        self.docHead:DocHead = None
        self.docInfoBlock:List[DocInfoBlock] = None
        self.docBody: DocBody = None

    def toByteIO(self, bos:BytesIO=None) -> BytesIO:
        bos = BytesIO() if bos is None else bos
        bos = self.docHead.toBytesIO(bos)
        for info in self.docInfoBlock:
            bos = info.toByteIO(bos)
        bos = self.docBody.toByteIO(bos)
        return bos

    @classmethod
    def fromBytes(cls, data: bytes) -> DocFileType:
        bis = BytesIO(data)
        df = DocFile()
        infoBlockCount = DocHead.getDocInfoBlockCount(bis)
        headLen = DocHead.getHeadBlockBytesLen(infoBlockCount)
        df.docHead = DocHead.fromBytes(readBytes(headLen, bis))
        df.docInfoBlock = list()
        for infoLen in df.docHead.docInfoBlockLen:
            infoBlock = DocInfoBlock.fromBytes(readBytes(infoLen, bis))
            df.docInfoBlock.append(infoBlock)
        df.docBody = DocBody.fromBytes(readBytes(df.docHead.docBodyLen, bis))
        return df