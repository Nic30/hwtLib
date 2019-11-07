#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image
import os

from hwt.hdl.types.bits import Bits
from pyMathBitPrecise.bit_utils import selectBit


# Can be many different formats.
im = Image.open(os.path.dirname(__file__) + "/charToBitmap_font.png")
pixels = im.load()


# img is 8x16 array of bitmaps, each char is 8x8 pix big
def asciiArtOfChar(ch, inverted=True):
    ch = ord(ch)
    imgBuf = []

    for y in range(8):
        row = getCharRow(ch, y)
        lineBuf = []
        for x in range(8):
            pix = selectBit(row, 8 - x - 1)
            if inverted:
                pix = not pix

            if pix:
                pix = ' '
            else:
                pix = '#'
            lineBuf.append(pix)
        imgBuf.append("".join(lineBuf))
        lineBuf.clear()

    return "\n".join(imgBuf)


def getCharRow(charOrd, row):
    CHARS_PER_ROW = 32
    xpos = charOrd % CHARS_PER_ROW
    xbase = xpos * 8
    ypos = charOrd // CHARS_PER_ROW
    ybase = ypos * 8 + row

    for y in range(8):
        n = 0
        for x in range(8):
            pix = pixels[x + xbase, y + ybase]

            if pix != 0 and pix != 1:
                raise NotImplementedError("Unimplemented color %s" % str(pix))

            n |= (pix << (7 - x))
        return n


def addCharToBitmap():
    """
    Add rom to translate ascii to 8x8 char bitmap,
    first row is placed on lower address,
    font is taken from png image

    :return: Bits(8)[128 * 8] where are stored bitmaps of chars,
             up is first lower char is first
    """
    rom = []
    for ch in range(128):
        for row in range(8):
            rom.append(getCharRow(ch, row))

    return Bits(8)[128 * 8].from_py(rom)


if __name__ == "__main__":
    print(asciiArtOfChar("a", inverted=True))
