from typing import List

from hwt.code import Concat
from hwtLib.tools.debug_bus_monitor_ctl import select_bit_range
from hwtSimApi.basic_hdl_simulator.proxy import BasicRtlSimProxy
from pyMathBitPrecise.bit_utils import int_to_int_list


class SegmentedArrayProxy():
    """
    A simulation proxy whic can read a and write to memories which are physicaly stored in multiple arrays.
    e.g.

    .. code-block:: c

        // example definition of two segments
        int array0[10];
        int array1[10];
        // a get of actual item
        Concat(array1[i] array0[i])
        // a set of actual item
        array1[i] = select_bit_range(v, 32, 64)
        array0[i] = select_bit_range(v, 0, 32)

    This object allows to use such a list of memories as a list
    thus removing of manual bit selections and concatenations
    when accessing the items stored in memory.
    """

    def __init__(self, mems: List[BasicRtlSimProxy], items_per_index=None, words_per_item=None):
        assert mems, mems
        self.mems = mems
        assert items_per_index is None or words_per_item is None, (items_per_index, words_per_item)
        self.items_per_index = items_per_index
        self.words_per_item = words_per_item
        self.ITEM_WIDTH = mems[0]._dtype.element_t.bit_length() * len(mems)

    def clean(self):
        for mem in self.mems:
            # may not neccessary have to be two different instances
            # as the value is copied into simulator, (copy just to make sure)
            t = mem._dtype
            mem.val = t.from_py([0 for _ in range(t.size)])
            mem.def_val = t.from_py([0 for _ in range(t.size)])

    def __getitem__(self, i: int):
        if self.items_per_index and self.items_per_index != 1:
            raise NotImplementedError()
        elif self.words_per_item and self.words_per_item != 1:
            return Concat(*(
                self._getitem(i * self.words_per_item + i2)
                for i2 in range(self.words_per_item - 1, -1, -1)
            ))
        else:
            return self._getitem(i)

    def _getitem(self, i: int):
        res = [data_mem.val[i] for data_mem in reversed(self.mems)]
        return Concat(*res)

    def _setitem(self, i, val):
        for B_i, data_mem  in enumerate(self.mems):
            t = data_mem._dtype
            _data = select_bit_range(val, B_i * 8, 8)
            if data_mem.def_val is None:
                # a default state before sim execution if there is no default value
                data_mem.def_val = t.from_py([0 for _ in range(t.size)])
            data_mem.val[i] = data_mem.def_val[i] = t.element_t.from_py(_data)

        return val

    def __setitem__(self, i: int, val: int):
        if self.items_per_index and self.items_per_index != 1:
            raise NotImplementedError()
        elif self.words_per_item and self.words_per_item != 1:
            _i = i * self.words_per_item
            _data = int_to_int_list(val, self.ITEM_WIDTH, self.words_per_item)
            for i2, _d in enumerate(_data):
                self._setitem(_i + i2, _d)
            return val
        else:
            return self._setitem(i, val)

    def __len__(self):
        return len(self.mems[0]) // self.words_per_item

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
