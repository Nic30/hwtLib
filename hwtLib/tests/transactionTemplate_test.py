import unittest

from hwt.hdlObjects.types.struct import HStruct
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t
from hwt.hdlObjects.transactionTemplate import TransactionTemplate,\
    TransactionTemplateConfig
from hwt.hdlObjects.types.array import Array


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
            (Array(uint64_t, 10), "arr0"),
            (Array(uint32_t, 5), "arr1")
            )


def instantiateChilds():
    raise NotImplementedError()


class TransactionTemplateTC(unittest.TestCase):
    def test_translateHStruct(self):
        DW = 64
        tmpl = TransactionTemplate.fromHStruct(s0)
        config = TransactionTemplateConfig(DW, instantiateChilds)
        tmpl.translateHStruct(config)
        self.assertEqual(s0at64bit_str, tmpl.__repr__())

    def test_translateHStruct_s0_71bit(self):
        DW = 71
        config = TransactionTemplateConfig(DW, instantiateChilds)
        tmpl = TransactionTemplate.fromHStruct(s0)
        tmpl.translateHStruct(config)
        self.assertEqual(s0at71bit_str, tmpl.__repr__(scale=2))

    def test_translateHStruct_s1_64(self):
        DW = 64
        tmpl = TransactionTemplate.fromHStruct(s1)
        config = TransactionTemplateConfig(DW, instantiateChilds)
        tmpl.translateHStruct(config)
        print(tmpl)
        #self.assertEqual(s0at64bit_str, tmpl.__repr__())

if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TransactionTemplateTC('test_translateHStruct_s1_64'))
    #suite.addTest(unittest.makeSuite(TransactionTemplateTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
