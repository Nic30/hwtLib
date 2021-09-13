#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import StringIO
import json
from math import ceil
import subprocess
import sys
from typing import List, Union, Tuple, Optional, Dict


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


class Colorizer():
    """
    A base class for objects which looks at the data and resolves color of the output text/element
    """

    def get_color(self, name:str, data_spec:list, data: int):
        raise  NotImplementedError("Should be overriden in implementation of this abstract class")


class ColorizerHandshakeOrEnLike(Colorizer):
    LIGHT_RED = '#ffcccb'
    LIGHT_PURPLE = '#b19cd9'
    LIGHT_GREEN = '#90ee90'

    def _get_intf_names(self, data_spec):
        return {
            n: (i, d_spec) for i, (n, d_spec) in enumerate(data_spec)
        }

    def _try_get_intf_index_by_name(self, intfs: Dict[str, Tuple[int, Tuple[int, int]]], names: List[str], data) -> Optional[int]:
        for n in names:
            i = intfs.get(n, None)
            if i is not None:
                bits_start, bits_len = i[1]
                val = select_bit_range(data, bits_start, bits_len)
                return i, val
        return None, None

    def get_color(self, name:str, data_spec:list, data: int):
        if not data_spec or isinstance(data_spec[0], int):
            return

        intfs = self._get_intf_names(data_spec)
        rd, rd_v = self._try_get_intf_index_by_name(intfs, ["rd", "ready"], data)
        vld, vld_v = self._try_get_intf_index_by_name(intfs, ["vld", "valid", 'en', 'enable', 'ce', 'clock_enable'], data)

        # we recognize 3 types of interfaces
        if rd is not None or vld is not None:
            # handshake (ready + valid, bi-dir handshake)
            if rd_v and vld_v:
                return self.LIGHT_GREEN
            elif vld_v:
                return self.LIGHT_RED
            elif not rd_v:
                return self.LIGHT_PURPLE

        elif vld is not None:
            # valid-synced (en from source)
            if vld_v:
                return self.LIGHT_GREEN
            else:
                return self.LIGHT_RED

        elif rd is not None:
            # ready-synced (en from sink)
            if rd_v:
                return self.LIGHT_GREEN
            else:
                return self.LIGHT_RED


class VisualNodeTemplate():

    def __init__(self, id_:int, name:str, data_spec:list, parent: Optional["VisualNodeTemplate"]=None):
        self.parent = parent
        self.name = name
        self.id = id_
        self.data_spec = data_spec

        self.links: List[VisualNodeTemplate] = []
        self.children: List[VisualNodeTemplate] = []

    @classmethod
    def _get_intf_depth(cls, data_spec: Union[dict, Tuple[int, int]]) -> int:
        if not data_spec or isinstance(data_spec[0], int):
            return 1
        else:
            return max(cls._get_intf_depth(i[1]) for i in data_spec) + 1

    @classmethod
    def _visual_format_intf_rows(cls, name: str,
                                 data_spec: Union[dict, Tuple[int, int]],
                                 buff: StringIO,
                                 column_cnt: int,
                                 cur_indent: int,
                                 data:int,
                                 text_indent:int,
                                 colorizer: Optional[Colorizer]) -> None:
        color = colorizer.get_color(name, data_spec, data)
        if color is None:
            color = ""
        else:
            color = f' bgcolor="{color}"'

        empty_column = f"<td{color:s}></td>"

        cls._dump_txt_indent(buff, text_indent)
        buff.write("<tr>")
        for _ in range(cur_indent):
            buff.write(empty_column)
        buff.write(f"<td{color:s}>")
        buff.write(name)
        buff.write("</td>")

        has_subinterfaces = data_spec and not isinstance(data_spec[0], int)
        columns_until_end = column_cnt - cur_indent - 1
        if not has_subinterfaces:
            buff.write(f"<td{color:s}>")
            if data_spec:
                buff.write(cls._format_data(data, data_spec))
            buff.write("</td>")
            columns_until_end -= 1

        for _ in range(columns_until_end):
            buff.write(empty_column)

        buff.write("</tr>\n")
        if has_subinterfaces:
            for k, v in data_spec:
                cls._visual_format_intf_rows(k, v, buff, column_cnt, cur_indent + 1,
                                             data, text_indent, colorizer)

    def _default_dot_formatter(self, data:int, out: StringIO,
                               indent: int, colorizer: Optional[Colorizer]) -> str:
        """
        Format interface signals and values as a html like table for graphwiz
        """
        self._dump_txt_indent(out, indent)
        color = colorizer.get_color(self.name, self.data_spec, data)
        if color is None:
            color = ""
        else:
            color = f' bgcolor="{color}"'
        out.write(f"<table border='0' cellborder='1' cellspacing='0'{color:s}>\n")
        column_cnt = self._get_intf_depth(self.data_spec) + 1  # +1 for value column
        self._visual_format_intf_rows(self.name, self.data_spec, out, column_cnt, 0, data, indent + 1, colorizer)

        self._dump_txt_indent(out, indent)
        out.write("</table>\n")

    @classmethod
    def _dump_txt_indent(cls, out: StringIO, indent: int):
        for _ in range(indent):
            out.write("  ")

    @classmethod
    def _format_data(cls, data, data_spec: Tuple[int, int]):
        bits_start, bits_len = data_spec
        val = select_bit_range(data, bits_start, bits_len)
        if bits_len == 1:
            return f"{val:d}"
        else:
            return f"0x{val:x}"

    @classmethod
    def _default_txt_formatter(cls, name:str, data_spec, children: List["VisualNodeTemplate"],
                               data: int, out: StringIO, indent: int):
        cls._dump_txt_indent(out, indent)
        out.write(name)
        if data_spec and isinstance(data_spec[0], int):
            out.write(": ")
            out.write(cls._format_data(data, data_spec))
            out.write("\n")
        else:
            out.write(":\n")
            for k, v in data_spec:
                cls._default_txt_formatter(k, v, (), data, out, indent + 1)

            for c in children:
                cls._default_txt_formatter(c.name, c.data_spec, c.children, data, out, indent + 1)


class DebugBusMonitorCtl():
    """
    A tool used to interact with a :class:`hwtLib.abstract.debug_bus_monitor.DebugBusMonitor`
    """
    REG_NAME_MEMORY_SIZE = 0x0
    REG_NAME_MEMORY_OFFSET = 0x4
    REG_DATA_MEMORY = 0x8

    def __init__(self, addr):
        self.addr = addr
        self.meta_memory: Optional[VisualNodeTemplate] = None
        self.data_memory_size: Optional[int] = None

    def _decode_meta_memory_json(self, data: list):
        new_data = []
        for _d in data:
            d = VisualNodeTemplate(_d["id"], _d["name"], _d["data"])
            d.links = _d["links"]
            d.children = self._decode_meta_memory_json(_d.get("children", d.children))
            d.links = _d.get("links", d.links)
            new_data.append(d)

        return new_data

    def load_meta_memory(self):
        size = self.read_int(self.REG_NAME_MEMORY_SIZE, 4)
        offset = self.read_int(self.REG_NAME_MEMORY_OFFSET, 4)
        meta_memory = self.read(offset, size)
        meta_memory = meta_memory.decode("utf-8")
        meta_memory = json.loads(meta_memory)
        meta_memory = self._decode_meta_memory_json(meta_memory)
        data_width = self.get_data_memory_width(meta_memory)
        self.meta_memory = meta_memory
        self.data_memory_size = ceil(data_width / 8)

    def get_data_memory_width(self, meta_memory: Union[VisualNodeTemplate, list, List[int]]):
        if isinstance(meta_memory, VisualNodeTemplate):
            meta_memory = meta_memory.data_spec

        w = 0
        if meta_memory and isinstance(meta_memory[0], int):
            offset, width = meta_memory
            return offset + width
        elif meta_memory and isinstance(meta_memory[0], VisualNodeTemplate):
            pass
        else:
            meta_memory = (v for _, v in meta_memory)
        for v in meta_memory:
            w = max(w, self.get_data_memory_width(v))

        return w

    def read_int(self, addr: int, size: int) -> int:
        v = self.read(addr, size)
        v = int.from_bytes(v, "little")
        return v

    def read(self, addr: int, size: int):
        addr += self.addr
        raise NotImplementedError("Implement this in your implementation of this abstract class")

    def _load_meta_and_data(self) -> int:
        if self.meta_memory is None:
            self.load_meta_memory()

        return self.read_int(self.REG_DATA_MEMORY, self.data_memory_size)

    def dump_txt(self, out=sys.stdout) -> None:
        data = self._load_meta_and_data()
        for kv in self.meta_memory:
            kv._default_txt_formatter(kv.name, kv.data_spec, kv.children, data, out, 0)

    def construct_id_to_node_dict(self, meta_memory: List[VisualNodeTemplate],
                                  res: Dict[int, VisualNodeTemplate]):
        for d in meta_memory:
            res[d.id] = d
            self.construct_id_to_node_dict(d.children, res)

    def _dump_dot_node_set(self, meta_memory: List[VisualNodeTemplate], out: StringIO,
                           colorizer: Colorizer, data:int, indent: int) -> None:
        for n in meta_memory:
            VisualNodeTemplate._dump_txt_indent(out, indent)
            if n.data_spec:
                # regular node with data
                out.write(f"n{n.id:d} [shape=plaintext, label=<\n")
                n._default_dot_formatter(data, out, indent + 1, colorizer)
                VisualNodeTemplate._dump_txt_indent(out, indent)
                out.write(">];\n")
            else:
                # visual hierachy node which will be represented as subgraph of nodes with a value
                # :attention: cluster_ prefix in label is required for graphwiz to work correctly
                out.write(f"subgraph cluster_{n.id:d} {{\n")
                VisualNodeTemplate._dump_txt_indent(out, indent + 1)
                out.write(f'label="{n.name:s}";\n')
                self._dump_dot_node_set(n.children, out, colorizer, data, indent + 1)
                VisualNodeTemplate._dump_txt_indent(out, indent)
                out.write("}\n")

    def _dump_dot_link_set(self, meta_memory: List[VisualNodeTemplate], out: StringIO, indent: int) -> None:
        for n in meta_memory:
            for suc in n.links:
                VisualNodeTemplate._dump_txt_indent(out, indent)
                out.write(f'n{n.id:d} -> n{suc:d};\n')
            self._dump_dot_link_set(n.children, out, indent)

    def dump_dot(self, out=sys.stdout, colorizer=ColorizerHandshakeOrEnLike()) -> None:
        data = self._load_meta_and_data()
        id_to_node = {}
        self.construct_id_to_node_dict(self.meta_memory, id_to_node)

        out.write("digraph {\n")
        self._dump_dot_node_set(self.meta_memory, out, colorizer, data, 1)
        self._dump_dot_link_set(self.meta_memory, out, 1)

        out.write("}\n")


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
    parser.add_argument('address', metavar='ADDR', type=lambda x: int(x, 0),
                        help='base address of component')
    parser.add_argument('--devmem', default="devmem", type=str,
                        help='the devmem tool to use')
    parser.add_argument('--memory-desc', dest='mem_desc', default=None, type=str,
                        help='path to a file with a json specification of memory space of the signals')
    parser.add_argument("--output-format", dest="output_format", default="str", type=str, choices=["txt", "dot"],
                        help="format of output produced from this script (txt = basic indented text, dot = grahwiz graph)")

    args = parser.parse_args()
    db = DebugBusMonitorCtlDevmem(args.address)
    db.devmem = args.devmem
    if args.mem_desc:
        with open(args.mem_desc) as fp:
            meta_memory = json.load(fp)
        data_width = db.get_data_memory_width(meta_memory)
        db.meta_memory = meta_memory
        db.data_memory_size = ceil(data_width / 8)
    if args.output_format == "txt":
        db.dump_txt(sys.stdout)
    elif args.output_format == "dot":
        db.dump_dot(sys.stdout)
    else:
        raise ValueError("Unsupported format of output", args.output_format)

