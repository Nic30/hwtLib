#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.hdl.constants import Time
from hwt.interfaces.std import VectSignal
from hwt.simulator.simTestCase import SimTestCase, SingleUnitSimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.hObjList import HObjList


class BitonicSorter(Unit):
    """
    Bitonic sorter of arbitrary data

    .. hwt-schematic::
    """
    def __init__(self, cmpFn=lambda x, y: x < y):
        """
        :param cmpFn: function (item0, item1) if returns true,
            items are not swaped
        """
        Unit.__init__(self)
        self.cmpFn = cmpFn

    def _config(self):
        self.ITEMS = Param(2)
        self.DATA_WIDTH = Param(64)
        self.SIGNED = Param(False)

    def _declr(self):
        w = self.DATA_WIDTH
        sig = bool(self.SIGNED)

        self.inputs = HObjList(
            VectSignal(w, sig) for _ in range(int(self.ITEMS))
        )
        self.outputs = HObjList(
            VectSignal(w, sig)._m() for _ in range(int(self.ITEMS))
        )

    def bitonic_sort(self, cmpFn, x, layer=0, offset=0):
        if len(x) <= 1:
            return x
        else:
            _offset = len(x) // 2
            first = self.bitonic_sort(cmpFn,
                                      x[:_offset],
                                      layer, offset)
            second = self.bitonic_sort(lambda x, y: ~cmpFn(x, y),
                                       x[_offset:],
                                       layer, offset + _offset)
            return self.bitonic_merge(cmpFn, first + second,
                                      layer=layer + _offset, offset=offset)

    def bitonic_merge(self, cmpFn, x, layer, offset):
        # assume input x is bitonic, and sorted list is returned
        if len(x) == 1:
            return x
        else:
            x = self.bitonic_compare(cmpFn, x, layer, offset)
            _offset = len(x) // 2
            first = self.bitonic_merge(cmpFn, x[:_offset],
                                       layer + 1, offset)
            second = self.bitonic_merge(cmpFn, x[_offset:],
                                        layer + 1, offset + _offset)
            return first + second

    def bitonic_compare(self, cmpFn, x, layer, offset):
        dist = len(x) // 2
        _x = [self._sig("sort_tmp_%d_%d" %
                        (layer, offset), x[0]._dtype) for _ in x]
        for i in range(dist):
            If(cmpFn(x[i], x[i + dist]),
                # keep
                _x[i](x[i]),
                _x[i + dist](x[i + dist])
               ).Else(
                # swap
                _x[i](x[i + dist]),
                _x[i + dist](x[i]),
            )
        return _x

    def _impl(self):
        outs = self.bitonic_sort(self.cmpFn, self.inputs)
        for o, otmp in zip(self.outputs, outs):
            o(otmp)


class BitonicSorterTC(SingleUnitSimTestCase):
    SIM_TIME = 40 * Time.ns

    @classmethod
    def getUnit(cls):
        cls.u = BitonicSorter()
        return cls.u

    def getOutputs(self):
        return [outp._ag.data[-1] for outp in self.u.outputs]

    def setInputs(self, values):
        for v, p in zip(values, self.u.inputs):
            p._ag.data.append(v)

    def test_reversed(self):
        u = self.u
        ref = [i for i in range(int(u.ITEMS))]
        self.setInputs(reversed(ref))

        self.runSim(self.SIM_TIME)
        self.assertValSequenceEqual(self.getOutputs(), ref)

    def test_sorted(self):
        u = self.u
        ref = [i for i in range(int(u.ITEMS))]
        self.setInputs(ref)

        self.runSim(self.SIM_TIME)
        self.assertValSequenceEqual(self.getOutputs(), ref)


if __name__ == "__main__":
    import unittest
    from hwt.synthesizer.utils import toRtl

    u = BitonicSorter()
    print(toRtl(u))

    suite = unittest.TestSuite()
    # suite.addTest(BitonicSorterTC('test_sorted'))
    suite.addTest(unittest.makeSuite(BitonicSorterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
