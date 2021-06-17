#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from math import ceil
import subprocess
import sys


def bit_mask(w):
    """
    :note: duplication with pyMathBitPrecise in order to keep this script without non-std dependencies
    """
    return (1 << w) - 1


def select_bit_range(val: int, bits_start: int, bits_len: int):
    """
    Get sequence of bits from an int value

    :note: duplication with pyMathBitPrecise in order to keep this script without non-std dependencies
    """
    val >>= bits_start
    return val & bit_mask(bits_len)


def words_to_int(words, word_size, size):
    end_bytes = size % word_size
    if end_bytes != 0:
        words[-1] &= bit_mask(8 * end_bytes)

    res = 0
    for w in reversed(words):
        res <<= 8 * word_size
        res |= w
    return res


class DebugBusMonitorCtl():
    """
    A tool used to interact with a :class:`hwtLib.abstract.debug_bus_monitor.DebugBusMonitor`
    """
    REG_NAME_MEMORY_SIZE = 0x0
    REG_NAME_MEMORY_OFFSET = 0x4
    REG_DATA_MEMORY = 0x8

    def __init__(self, addr):
        self.addr = addr
        self.name_memory = None
        self.data_memory_size = None

    def load_name_memory(self):
        size = self.read_int(self.REG_NAME_MEMORY_SIZE, 4)
        offset = self.read_int(self.REG_NAME_MEMORY_OFFSET, 4)
        name_memory = self.read(offset, size)
        name_memory = (name_memory).decode("utf-8")
        name_memory = json.loads(name_memory)
        data_width = self.get_data_memory_width(name_memory)
        self.name_memory = name_memory
        self.data_memory_size = ceil(data_width / 8)

    def get_data_memory_width(self, name_memory):
        if isinstance(name_memory, list):
            offset, width = name_memory
            return offset + width
        else:
            w = 0
            for _, v in name_memory.items():
                w = max(w, self.get_data_memory_width(v))
            return w

    def read_int(self, addr, size):
        v = self.read(addr, size)
        v = int.from_bytes(v, "little")
        return v

    def read(self, addr, size):
        addr += self.addr
        raise NotImplementedError("Implement this in your implementation of this abstract class")

    def _dump_txt_indent(self, out, indent):
        for _ in range(indent):
            out.write("  ")

    def _dump_txt(self, out, name_memory, data, indent):
        for k, v in name_memory.items():
            if isinstance(v, list):
                self._dump_txt_indent(out, indent)
                out.write(k)
                out.write(": ")
                bits_start, bits_len = v
                val = select_bit_range(data, bits_start, bits_len)
                if bits_len == 1:
                    out.write(f"{val:d}")
                else:
                    out.write(f"0x{val:x}")
                out.write("\n")
            else:
                self._dump_txt_indent(out, indent)
                out.write(k)
                out.write(":\n")
                self._dump_txt(out, v, data, indent + 1)

    def dump_txt(self, out=sys.stdout):
        if self.name_memory is None:
            self.load_name_memory()

        data = self.read_int(self.REG_DATA_MEMORY, self.data_memory_size)
        self._dump_txt(out, self.name_memory, data, 0)


class DebugBusMonitorCtlDevmem(DebugBusMonitorCtl):

    def __init__(self, addr):
        DebugBusMonitorCtl.__init__(self, addr)
        self.devmem = "devmem"

    def read(self, addr, size):
        addr += self.addr
        word_size = 0x4
        words = []
        for _ in range(ceil(size / word_size)):
            s = subprocess.check_output([self.devmem, f"0x{addr:x}"])
            s = s.decode("utf-8")
            d = int(s.strip(), 16)
            words.append(d)
            addr += word_size

        return words_to_int(words, word_size, size).to_bytes(size, "little")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Dump a values from DebugBusMonitor instance.')
    parser.add_argument('address', metavar='ADDR', type=lambda x: int(x,0),
                        help='base address of component')
    parser.add_argument('--devmem', default="devmem", type=str,
                        help='the devmem tool to use')
    parser.add_argument('--memory-desc', dest='mem_desc', default=None, type=str,
                        help='path to a file with a json specification of memory space of the signals')

    args = parser.parse_args()
    db = DebugBusMonitorCtlDevmem(args.address)
    db.devmem = args.devmem
    if args.mem_desc:
        with open(args.mem_desc) as fp:
            name_memory = json.load(fp)
        data_width = db.get_data_memory_width(name_memory)
        db.name_memory = name_memory
        db.data_memory_size = ceil(data_width / 8)

    db.dump_txt(sys.stdout)
