import unittest
from io import BytesIO
from typing import List

from writer import DocHead, DocInfoBlock, DocBody, DocFile


class MyTestCase(unittest.TestCase):
    def test_dochead(self):
        bio = BytesIO()
        head = self.createDocHead()
        bio = head.toBytesIO(bio)
        length = len(bio.getvalue())
        bio.seek(0)
        infoBlockCount = DocHead.getDocInfoBlockCount(bio)
        headLen = DocHead.getHeadBlockBytesLen(infoBlockCount)
        newHead = DocHead.fromBytes(bio.read(headLen))
        self.assertEqual(infoBlockCount, len(head.docInfoBlockLen))
        self.assertEqual(headLen, length)
        self.assertDocHead(head, newHead)

    def assertDocHead(self, head, newHead):
        self.assertEqual(head.docBodyLen, newHead.docBodyLen)
        self.assertEqual(head.docType, newHead.docType)
        self.assertEqual(len(head.docInfoBlockLen), len(newHead.docInfoBlockLen))
        for d1, d2 in zip(head.docInfoBlockLen, newHead.docInfoBlockLen):
            self.assertEqual(d1, d2)

    def createDocHead(self):
        head = DocHead()
        head.docBodyLen = 1000000000
        head.docType = DocHead.DocType.Writer
        head.docInfoBlockLen = list()
        head.docInfoBlockLen.append(20938)
        head.docInfoBlockLen.append(50938)
        head.docInfoBlockLen.append(689500)
        return head

    def test_docinfoblock(self):
        block = DocInfoBlock()
        block.name = 'author'.encode('utf-8')
        block.value = '名字'.encode('utf-8')
        bio = BytesIO()
        bio = block.toByteIO(bio)
        newBlock = DocInfoBlock.fromBytes(bio.getvalue())
        self.assertDocInfoBlock(block, newBlock)
        self.assertEqual(newBlock.name.decode('utf-8'), 'author')
        self.assertEqual(newBlock.value.decode('utf-8'), '名字')

    def assertDocInfoBlock(self, block, newBlock):
        self.assertEqual(newBlock.name, block.name)
        self.assertEqual(newBlock.value, block.value)

    def test_docbody(self):
        docBody = DocBody()
        docBody.content = conent.encode('utf-8')
        bio = BytesIO()
        bio = docBody.toByteIO(bio)
        newDocBody = DocBody.fromBytes(bio.getvalue())
        self.assertDocBody(docBody, newDocBody)

    def assertDocBody(self, docBody, newDocBody):
        self.assertEqual(len(newDocBody.content), len(docBody.content))
        self.assertEqual(newDocBody.content, docBody.content)
        self.assertEqual(newDocBody.content.decode('utf-8'), conent)

    def test_docfile(self):
        df = DocFile()

        docBody = DocBody()
        docBody.content = conent.encode('utf-8')

        block1 = DocInfoBlock()
        block1.name = 'author'.encode('utf-8')
        block1.value = '名字'.encode('utf-8')

        block2 = DocInfoBlock()
        block2.name = '测试'.encode('utf-8')
        block2.value = 'aaaa'.encode('utf-8')

        infoList:List[DocInfoBlock] = list()
        infoList.append(block1)
        infoList.append(block2)

        head = DocHead()
        head.docBodyLen = len(docBody.content)
        head.docType = DocHead.DocType.Writer
        head.docInfoBlockLen = [i.getByteLen() for i in infoList]

        df.docHead = head
        df.docBody = docBody
        df.docInfoBlock = infoList

        bio = BytesIO()
        bio = df.toByteIO(bio)
        data = bio.getvalue()

        newDf = DocFile.fromBytes(data)
        self.assertDocHead(newDf.docHead, df.docHead)
        for a,b in zip(newDf.docInfoBlock, df.docInfoBlock):
            self.assertDocInfoBlock(a, b)
        self.assertDocBody(newDf.docBody, df.docBody)


    def test_docfile_emptyinfolists(self):
        df = DocFile()

        docBody = DocBody()
        docBody.content = conent.encode('utf-8')

        infoList:List[DocInfoBlock] = list()

        head = DocHead()
        head.docBodyLen = len(docBody.content)
        head.docType = DocHead.DocType.Writer
        head.docInfoBlockLen = [i.getByteLen() for i in infoList]

        df.docHead = head
        df.docBody = docBody
        df.docInfoBlock = infoList

        bio = BytesIO()
        bio = df.toByteIO(bio)
        data = bio.getvalue()

        newDf = DocFile.fromBytes(data)
        self.assertDocHead(newDf.docHead, df.docHead)
        for a,b in zip(newDf.docInfoBlock, df.docInfoBlock):
            self.assertDocInfoBlock(a, b)
        self.assertDocBody(newDf.docBody, df.docBody)

conent = '''
近日，历史老师将“羊了个羊”游戏创新改编成“历了个史”的消息引发广泛关注。🅿️🆑🆓🀄🃏🏺🐎

　　据封面新闻报道，近日，浙江湖州一高中历史老师徐娇娇将“羊了个羊”游戏创新改编成“历了个史”，让历史课变得趣味无穷，深受学生们喜爱。据了解，徐老师是一位“90后”姑娘，她自曝虽然此前玩“羊了个羊”只过了第一关，但将网上冲浪的灵感运用到教学中，仅用了半个小时。

　　从日常的生活习惯和学生们熟悉的周边环境切入，将时下流行的小游戏设置成特定的场景，并融入相关的知识，这让徐老师收获了很多学生和网友的赞许。在不少人看来，此举让课堂不再变得枯燥，尤其是对于学习任务重的高中学生而言，这样寓教于乐、融学于趣的教学方式，让以往需要死记硬背的历史知识变得生动了起来，因此也受到了学生欢迎。

　　事实上，这其中的关键在于，教师要让学生在学习的过程中产生参与感。在学习知识的过程中，充分的互动也在某种程度上拉近了学生与教师的距离。而更进一步去看，这种不同于以往模式化的教学方式，除了少了些刻板化教学的内容外，也更多呈现出一种趣味性。

　　而让学生们像喜欢玩游戏一样喜欢学习，本质上也是一种多元、平等教学理念的展现。近些年来，我们欣喜地看到，这种理念在潜移默化之中改变着很多教师的课堂。它不再是一种严肃的、灌输式的教育，而是可以在课堂互动中让学生们快乐学习的教育。这是我们的教育中最为本质、也是最值得欣慰的变化。

　　其实，不管课堂教学形式如何变化，其最终目的都如同徐老师在接受采访时说的那样，“激发学生学习历史的兴趣和积极性。”从短期引起的效果来看，徐老师的目的显然达到了一部分——起码调和了课堂教学的氛围，塑造了一个快乐的学习过程，提升了学生积极性，这与打造有效课堂的目标处于相同的逻辑链条之下。

　　俗话说，万变不离其宗，回到此事去看，“历了个史”之所以受到好评，除了形式新颖外，根本上还是依赖于徐老师优秀的逻辑能力和对相关知识点的深入掌握，因此才能“仅用了半个小时就完成了”。这也表明，对于教师而言，在日常的教学中，对课堂教学形式作出改变固然重要，但根本上，还是要以优秀的教学能力为依托。

　　值得一提的是，自从“羊了个羊”火了之后，不止一位教师改编过这个游戏。据媒体报道，此前，广东佛山的廖老师和学生制作的元素周期表版“羊了个羊”——一款名为“化了个学”的教学课件，也曾引发广泛关注。越来越多的新颖“玩法”开始进入日常课堂，呈现了一种新气象。

　　当然，人们对“徐老师们”的教学方式表示欢迎，根本上还是源于对教学理念变化的期待——越来越多知识丰富、理念前卫的新生代教师进入教育行业，能够让课堂教学变得更为多元、更为快乐，进而让孩子们能够度过一个更为丰富的青少年时期。

'''
if __name__ == '__main__':
    unittest.main()

import sys

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QToolButton, QPushButton

#0.创建一个APP
app = QApplication(sys.argv)

w = QWidget()
w.setWindowTitle("QToolButton")
w.resize(300,300)

#创建菜单
menu = QMenu()
#创建子菜单
sub_menu = QMenu(menu)
sub_menu.setTitle("子菜单")
sub_menu.addAction(QAction('test'))

#在菜单中添加子菜单
menu.addMenu(sub_menu)

#创建action并添加到菜单中
action = QAction("行为",menu)
menu.addAction(action)
#响应action点击事件
action.triggered.connect(lambda:print("点击了 action"))


#创建一个 QToolButton
tb = QToolButton(w)
tb.setAutoRaise(True)

pb = QPushButton(w)
pb.move(0,30)
pb.setText("按键")

#QToolBool添加菜单
tb.setMenu(menu)
pb.setMenu(menu)

w.show()

sys.exit(app.exec_())