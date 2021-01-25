from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.datapump.r import Axi_rDatapump
from hwtLib.amba.datapump.r_aligned_test import Axi3Lite_rDatapumpTC, \
    Axi3_rDatapumpTC


class Axi4Lite_rDatapump_alignas8TC(Axi3Lite_rDatapumpTC):
    CHUNK_WIDTH = 8
    ALIGNAS = 8

    @classmethod
    def getUnit(cls):
        u = Axi_rDatapump(axiCls=Axi4Lite)
        u.DATA_WIDTH = cls.DATA_WIDTH
        u.CHUNK_WIDTH = cls.CHUNK_WIDTH
        u.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)
        u.ALIGNAS = cls.ALIGNAS
        return u


class Axi4Lite_rDatapump_16b_from_64bTC(Axi4Lite_rDatapump_alignas8TC):
    LEN_MAX_VAL = 0
    CHUNK_WIDTH = 16
    ALIGNAS = 16


class Axi3_rDatapump_alignas8_TC(Axi3_rDatapumpTC):
    ALIGNAS = 8
    CHUNK_WIDTH = 8

    @classmethod
    def getUnit(cls):
        u = Axi3_rDatapumpTC.getUnit()
        u.DATA_WIDTH = cls.DATA_WIDTH
        u.CHUNK_WIDTH = cls.CHUNK_WIDTH
        u.MAX_CHUNKS = (cls.DATA_WIDTH // cls.CHUNK_WIDTH) * (cls.LEN_MAX_VAL + 1)
        u.ALIGNAS = cls.ALIGNAS
        return u


Axi_rDatapump_unalignedTCs = [
    Axi3_rDatapump_alignas8_TC,
    Axi4Lite_rDatapump_alignas8TC,
    Axi4Lite_rDatapump_16b_from_64bTC,
]

if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Axi4Lite_rDatapump_16b_from_64bTC('test_notSplitedReqWithData'))
    for tc in Axi_rDatapump_unalignedTCs:
        suite.addTest(unittest.makeSuite(tc))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
