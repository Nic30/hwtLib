from math import inf
from typing import Union
import unittest

from hwtLib.abstract.frame_utils.alignment_utils import FrameAlignmentUtils


def get_important_byte_cnts(
        offset_out: int, offset_in: int, word_bytes: int, chunk_size: int,
        chunk_cnt_min: Union[int, float], chunk_cnt_max: Union[int, float]):
    fju = FrameAlignmentUtils(word_bytes)
    return fju.get_important_byte_cnts(offset_out, offset_in,
                                       chunk_size, chunk_cnt_min, chunk_cnt_max)


class FrameAlignmentUtilsTC(unittest.TestCase):

    def test_get_important_chunk_cnts_0(self):
        word_bytes = 2
        chunk_size = 2
        chunk_cnt_min = 0
        chunk_cnt_max = 1
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [0, 2]
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 2
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [0, 2, 4]  # 4 for case where last=0
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 3
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 2
        res = get_important_byte_cnts(
            1, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        res = get_important_byte_cnts(
            0, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        res = get_important_byte_cnts(
            1, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 3
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)


    def test_get_important_chunk_cnts_1(self):
        word_bytes = 2
        chunk_size = 2
        chunk_cnt_min = 1
        chunk_cnt_max = 1
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [2]
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 2
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [2, 4]  # 4 for case where last=0
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 3
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 2
        res = get_important_byte_cnts(
            1, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        res = get_important_byte_cnts(
            0, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        res = get_important_byte_cnts(
            1, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = 3
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        self.assertSequenceEqual(res, res_ref)

    def test_get_important_chunk_cnts_2(self):
        word_bytes = 2
        chunk_size = 1
        chunk_cnt_min = 1
        chunk_cnt_max = inf
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [1, 2, 3]  # 3 for case where last=0 for byte 0, 1
        self.assertSequenceEqual(res, res_ref)

        res = get_important_byte_cnts(
            1, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [1, 2, 3, 4]

        self.assertSequenceEqual(res, res_ref)

        word_bytes = 1
        res = get_important_byte_cnts(
            0, 0, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [1, 2]
        self.assertSequenceEqual(res, res_ref)

    def test_get_important_chunk_cnts_3(self):
        word_bytes = 2
        chunk_size = 2
        chunk_cnt_min = 1
        chunk_cnt_max = 1
        res = get_important_byte_cnts(
            0, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [2]
        self.assertSequenceEqual(res, res_ref)

        chunk_cnt_max = inf
        res = get_important_byte_cnts(
            0, 1, word_bytes, chunk_size, chunk_cnt_min, chunk_cnt_max)
        res_ref = [2, 4]
        self.assertSequenceEqual(res, res_ref)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(StreamJoiningUtilsTC('test_struct2xStream64'))
    suite.addTest(unittest.makeSuite(FrameAlignmentUtilsTC))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
