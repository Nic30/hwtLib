#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.constants import Time
from hwt.hwIOs.std import HwIOVectSignal
from hwt.simulator.simTestCase import SimTestCase
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.hObjList import HObjList


class BitonicSorter(HwModule):
    """
    Bitonic sorter of arbitrary data

    .. hwt-autodoc::
    """
    def __init__(self, cmpFn=lambda x, y: x < y):
        """
        :param cmpFn: function (item0, item1) if returns true,
            items are not swaped
        """
        HwModule.__init__(self)
        self.cmpFn = cmpFn

    def _config(self):
        self.ITEMS = HwParam(2)
        self.DATA_WIDTH = HwParam(64)
        self.SIGNED = HwParam(False)

    def _declr(self):
        w = self.DATA_WIDTH
        sig = bool(self.SIGNED)

        self.inputs = HObjList(
            HwIOVectSignal(w, sig) for _ in range(int(self.ITEMS))
        )
        self.outputs = HObjList(
            HwIOVectSignal(w, sig)._m() for _ in range(int(self.ITEMS))
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
        _x = [self._sig(f"sort_tmp_{layer:d}_{offset:d}", x[0]._dtype) for _ in x]
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


class BitonicSorterTC(SimTestCase):
    SIM_TIME = 40 * Time.ns

    @classmethod
    def setUpClass(cls):
        cls.dut = BitonicSorter()
        cls.compileSim(cls.dut)

    def getOutputs(self):
        return [outp._ag.data[-1] for outp in self.dut.outputs]

    def setInputs(self, values):
        for v, p in zip(values, self.dut.inputs):
            p._ag.data.append(v)

    def test_reversed(self):
        dut = self.dut
        ref = [i for i in range(int(dut.ITEMS))]
        self.setInputs(reversed(ref))

        self.runSim(self.SIM_TIME)
        self.assertValSequenceEqual(self.getOutputs(), ref)

    def test_sorted(self):
        dut = self.dut
        ref = [i for i in range(int(dut.ITEMS))]
        self.setInputs(ref)

        self.runSim(self.SIM_TIME)
        self.assertValSequenceEqual(self.getOutputs(), ref)


if __name__ == "__main__":
    import unittest
    from hwt.synth import to_rtl_str

    m = BitonicSorter()
    print(to_rtl_str(m))

    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([BitonicSorterTC("test_sorted")])
    suite = testLoader.loadTestsFromTestCase(BitonicSorterTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
