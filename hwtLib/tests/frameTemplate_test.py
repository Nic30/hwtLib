import unittest

from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
from hwt.hdlObjects.transactionTemplate import TransactionTemplate
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.transactionPart import FrameTemplate

s_basic = HStruct(
    (uint64_t, "item0"),
    (uint64_t, "item0"),
    (uint64_t, None),
)

s_basic_srt = """<TransactionTemplate start:0, end:192
    <TransactionTemplate name:item0, start:0, end:64>
    <TransactionTemplate name:item0, start:64, end:128>
>"""

s0 = HStruct(
    (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
    (uint64_t, None),  # name = None means this field will be ignored
    (uint64_t, "item1"),
    (uint64_t, None),
    (uint16_t, "item2"),
    (uint16_t, "item3"),
    (uint32_t, "item4"),

    (uint32_t, None),
    (uint64_t, "item5"),  # this word is split on two bus words
    (uint32_t, None),

    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, "item6"),
    (uint64_t, "item7"),
    (HStruct(
        (uint64_t, "item0"),
        (uint64_t, "item1"),
     ), "struct0"
    )
    )
s0at64bit_str = \
"""     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |                             item1                             |
3    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
4    |             item4             |     item3     |     item2     |
5    |             item5             |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
6    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|             item5             |
7    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
8    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
9    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
10   |                             item6                             |
11   |                             item7                             |
12   |                         struct0.item0                         |
13   |                         struct0.item1                         |
     -----------------------------------------------------------------"""

s0at71bit_str = \
"""     70                                                                                                                                           0
     -----------------------------------------------------------------------------------------------------------------------------------------------
0    |XXXXXXXXXXXX|                                                             item0                                                             |
1    |          item1           |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                                               item1                                               |
3    |         item3         |             item2             |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
4    |item5|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                             item4                             | item3 |
5    |XXXXXXXXXXXXXXXXXXX|                                                          item5                                                          |
6    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
7    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
8    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
9    |   item7   |                                                             item6                                                             |X|
10   |      struct0.item0      |                                                       item7                                                       |
11   |             struct0.item1             |                                            struct0.item0                                            |
12   |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|                                     struct0.item1                                     |
     -----------------------------------------------------------------------------------------------------------------------------------------------"""

s1 = HStruct(
            (Array(uint64_t, 3), "arr0"),
            (Array(uint32_t, 5), "arr1")
            )

s1_str = """     63                                                             0
     -----------------------------------------------------------------
0    |                            arr0[0]                            |
1    |                            arr0[1]                            |
2    |                            arr0[2]                            |
3    |            arr1[1]            |            arr1[0]            |
4    |            arr1[3]            |            arr1[2]            |
5    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|            arr1[4]            |
     -----------------------------------------------------------------"""

sWithPadding = HStruct(
                       (uint64_t, "item0_0"),
                       (uint64_t, "item0_1"),
                       (uint64_t, None),
                       (uint64_t, "item1_0"),
                       (uint64_t, "item1_1"),
                       (uint64_t, None)
                       )

sWithPadding_str = """     63                                                             0
     -----------------------------------------------------------------
0    |                            item0_0                            |
1    |                            item0_1                            |
2    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
3    |                            item1_0                            |
4    |                            item1_1                            |
5    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
     -----------------------------------------------------------------""" 

sWithPaddingMultiframe0_str = """     63                                                             0
     -----------------------------------------------------------------
0    |                            item0_0                            |
1    |                            item0_1                            |
     -----------------------------------------------------------------"""

sWithPaddingMultiframe1_str = """     63                                                             0
     -----------------------------------------------------------------
0    |                            item1_0                            |
1    |                            item1_1                            |
     -----------------------------------------------------------------""" 


sWithStartPadding = HStruct(
                       (uint64_t, None),
                       (uint64_t, None),
                       (uint64_t, "item0"),
                       (uint64_t, "item1"),
                    )

sWithStartPadding_strTrim = """     63                                                             0
     -----------------------------------------------------------------
0    |                             item0                             |
1    |                             item1                             |
     -----------------------------------------------------------------"""

sWithStartPadding_strKept = """     63                                                             0
     -----------------------------------------------------------------
0    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
1    |XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|
2    |                             item0                             |
3    |                             item1                             |
     -----------------------------------------------------------------"""

def instantiateChilds():
    raise NotImplementedError()


class FrameTemplateTC(unittest.TestCase):
    def test_s0at64bit(self):
        DW = 64
        tmpl = TransactionTemplate(s0)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s0at64bit_str, frames[0].__repr__())

    def test_s0at71bit(self):
        DW = 71
        tmpl = TransactionTemplate(s0)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s0at71bit_str, frames[0].__repr__(scale=2))

    def test_s1at64(self):
        DW = 64
        tmpl = TransactionTemplate(s1)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(s1_str, frames[0].__repr__())

    def test_sBasic(self):
        tmpl = TransactionTemplate(s_basic)
        self.assertEqual(s_basic_srt, tmpl.__repr__())

    def test_sWithPadding(self):
        DW = 64
        tmpl = TransactionTemplate(sWithPadding)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW))
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithPadding_str, frames[0].__repr__())

    def test_sWithPaddingMultiFrame(self):
        DW = 64
        tmpl = TransactionTemplate(sWithPadding)
        frames = FrameTemplate.framesFromTransactionTemplate(tmpl,
                                                             DW,
                                                             maxPaddingWords=0,
                                                             trimPaddingWordsOnStart=True,
                                                             trimPaddingWordsOnEnd=True)
        frames = list(frames)
        self.assertEqual(len(frames), 2)
        
        self.assertEqual(sWithPaddingMultiframe0_str, frames[0].__repr__())
        self.assertEqual(sWithPaddingMultiframe1_str, frames[1].__repr__())
    
    def test_sWithStartPadding(self):
        DW = 64
        tmpl = TransactionTemplate(sWithStartPadding)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW, 
                                                                  maxPaddingWords=0,
                                                                  trimPaddingWordsOnStart=True,
                                                                  trimPaddingWordsOnEnd=True))
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithStartPadding_strTrim, frames[0].__repr__())
    
    def test_sWithStartPaddingKept(self):
        DW = 64
        tmpl = TransactionTemplate(sWithStartPadding)
        frames = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW, 
                                                                  maxPaddingWords=2,
                                                                  trimPaddingWordsOnStart=True,
                                                                  trimPaddingWordsOnEnd=True))
        self.assertEqual(len(frames), 1)
        self.assertEqual(sWithStartPadding_strKept, frames[0].__repr__())

if __name__ == "__main__":
    suite = unittest.TestSuite()
    #suite.addTest(FrameTemplateTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(FrameTemplateTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
