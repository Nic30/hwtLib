#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image
import os

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array


im = Image.open(os.path.dirname(__file__) + "/charToBitmap_font.png")  # Can be many different formats.
pixels = im.load()


# img is 8x16 array of bitmaps, each char is 8x8 pix big
def printChar(ch):
    ch = ord(ch)
    for y in range(8):
        row = getCharRow(ch, y)
        for x in range(8):
            pix = row & (1 << (7 - x))
            if pix:
                pix = '#'
            else:
                pix = ' '
            print(pix, end="")  # Get the RGBA Value of the a pixel of an image
        print()

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


def addCharToBitmap(unit, name="charToBitmap"):
    """
    Add rom to translate ascii to 8x8 char bitmap,
    first row is placed on lower address,
    font is taken from png image
    """
    rom = []
    for ch in range(128):
        for row in range(8):
            rom.append(getCharRow(ch, row))
            
    mem = unit._sig(name, Array(vecT(8), 128 * 8), defVal=rom)
    return mem

    
if __name__ == "__main__":
    printChar("A")
