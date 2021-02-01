import unittest
from hwtLib.amba.axi_comp.cache.pseudo_lru import PseudoLru


class PseudoLru_TC(unittest.TestCase):

    def test_get_width_and_items(self):
        ref = {
             8: 7 ,  # 1+2+4 bits
            16: 15,  # 1+2+4+8 bits
            32: 31,  # 1+2+4+8+16 bits
            64: 63,  # 1+2+4+8+16+32 bits
        }
        for items, w in ref.items():
            w_ = PseudoLru.lru_reg_width(items)
            self.assertEqual(w_, w)
            items_ = PseudoLru.lru_reg_items(w)
            self.assertEqual(items_, items)


if __name__ == '__main__':
    unittest.main()
