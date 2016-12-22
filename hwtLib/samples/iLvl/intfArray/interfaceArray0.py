#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import hInt
from hwt.interfaces.std import VldSynced
from hwt.intfLvl import Unit, Param


class InterfaceArraySample0(Unit):
    """
    Sample unit with array interface (a and b)
    which is not using items of these array interfaces
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = hInt(3)
    
    def _declr(self):
        with self._paramsShared():
            self.a = VldSynced(multipliedBy=self.LEN)
            self.b = VldSynced(multipliedBy=self.LEN)
    
    def _impl(self):
        # directly connect arrays, note that we are not using array items
        # and thats why they are not created
        self.b ** self.a


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    print(toRtl(InterfaceArraySample0))

