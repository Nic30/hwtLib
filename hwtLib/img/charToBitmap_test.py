import unittest
from hwtLib.img.charToBitmap import asciiArtOfChar


A = """#   ####
 ### ###
 ### ###
     ###
 ### ###
 ### ###
########
########"""

dot = """########
########
########
########
########
# ######
########
########"""

six = """##  ####
# ######
#   ####
 ### ###
 ### ###
#   ####
########
########"""

a_inverted = """########
########
#    ###
 ### ###
 ##  ###
#  # ###
########
########"""


class CharToBitmapTC(unittest.TestCase):
    def test_A(self):
        self.assertEqual(asciiArtOfChar("A"), A)

    def test_dot(self):
        self.assertEqual(asciiArtOfChar("."), dot)

    def test_6(self):
        self.assertEqual(asciiArtOfChar("6"), six)

    def test_a_inverted(self):
        self.assertEqual(asciiArtOfChar("a", inverted=True), a_inverted)
        

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(ArrayBuff_writer_TC('test_fullFill_withoutAck'))
    suite.addTest(unittest.makeSuite(CharToBitmapTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
