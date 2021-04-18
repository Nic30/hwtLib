from typing import Dict, Tuple, List, Union, Optional

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import If, Switch, SwitchLogic, Or
from hwt.hdl.statements.statement import HdlStatement
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.structIntf import HdlType_to_Interface
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.typePath import TypePath
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.amba.axis import AxiStream
from hwtLib.logic.binToBcd import BinToBcd
from hwtLib.types.ctypes import uint32_t
from hwt.hdl.types.defs import BIT


class AxiS_strFormatItem():
    """
    :ivar member_path: path which specifies the loacation of interface with the value on input interface
    :ivar digits: number of digitsof output formated number (not used for 's' format)
    :ivar format_type: is one of folloving characters.
        +------+-------------------------------+
        | char | format meaning                |
        +======+===============================+
        | 'd'  | decadic number                |
        +------+-------------------------------+
        | 'b'  | binary number                 |
        +------+-------------------------------+
        | 'o'  | octal number                  |
        +------+-------------------------------+
        | 'x'  | hexadecimal number lowercase  |
        +------+-------------------------------+
        | 'X'  | hexadecimal number uppercase  |
        +------+-------------------------------+
        | 's'  | string                        |
        +------+-------------------------------+
    :ivar str leading_char_fill: character which should be used to fill leading digits if number of digits
        is used but the value have less digits
    """
    BITS_PER_CHAR = {
        'b': 1,
        'o': 3,
        'd': 4,
        'x': 4,
        'X': 4,
    }

    def __init__(self, member_path: TypePath,
                 format_type: str,
                 digits: int):
        assert format_type in ('d', 'b', 'o', 'x', 'X', 's')
        self.member_path = member_path
        self.format_type = format_type
        self.digits = digits

    def __repr__(self):
        return f"<AxiS_strFormatItem {self.member_path}, {self.format_type}, {self.digits}>"


class HdlType_to_Interface_with_AxiStream(HdlType_to_Interface):

    def apply(self, dtype: HdlType, field_path: Optional[TypePath]=None) -> Interface:
        """
        Run the connversion
        """
        if isinstance(dtype, HStream):
            assert dtype.element_t == Bits(8), dtype
            assert dtype.start_offsets == (0,), dtype.start_offsets
            assert dtype.len_min >= 1, dtype
            i = AxiStream()
            i.DATA_WIDTH = 8
        else:
            i = super(HdlType_to_Interface_with_AxiStream, self).apply(dtype, field_path)
        return i


@serializeParamsUniq
class AxiS_strFormat(Unit):
    """
    Generate compomonent which does same thing as printf just in hw.
    The output string is stream of encoded characters. The ending '0' is not appended.
    And 'last' signal of AxiStream is used instead.

    :note: use :func:`hwtLib.amba.axis_comp.strformat_fn.axiS_strFormat` to generate instance
        of this component from normal string format string and argument

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.FORMAT = Param((
            "AxiS_strFormat"
            ": hex: 0x", AxiS_strFormatItem(TypePath("data"), 'x', 32 // 4),
            ", dec: ", AxiS_strFormatItem(TypePath("data"), 'd', BinToBcd.decadic_deciamls_for_bin(32)),
            " is the value of data from example"
        ))
        self.INPUT_T = Param(HStruct(
            (uint32_t, "data"),
        ))
        self.ENCODING = Param("utf-8")

    def _declr(self):
        addClkRstn(self)
        if self.INPUT_T is not None:
            # if INPUT_T is none it menas that the component is configured to print a costant string.
            self.data_in = HdlType_to_Interface_with_AxiStream().apply(self.INPUT_T)
        # filter out emplty strings
        self.FORMAT = tuple(f for f in self.FORMAT if not isinstance(f, str) or f)
        assert self.FORMAT, "Need to have something to print"

        with self._paramsShared():
            self.data_out = AxiStream()._m()

    def build_string_rom(self):
        """
        Collect all const strings and char translation tables and pack them in to a content of string rom
        """

        # offset of tables for translation to a char
        digit_translation_tables = {}
        strings = {}  # type: Dict[index, bytes]
        input_strings = []
        max_bcd_digits = 0
        max_chars_per_format = 0
        for i, f in enumerate(self.FORMAT):
            if isinstance(f, str):
                s = strings[i] = f.encode(self.ENCODING)
                max_chars_per_format = max(max_chars_per_format, len(s))
            else:
                assert isinstance(f, AxiS_strFormatItem), f
                t = f.format_type
                if t == 'd':
                    # use bcd
                    max_bcd_digits = max(max_bcd_digits, f.digits)
                    max_chars_per_format = max(max_chars_per_format, f.digits)
                    table = [f"{i}" for i in range(10)]
                elif t in digit_translation_tables.keys():
                    continue
                elif t == 'b':
                    table = [f"{i}" for i in range(2)]
                elif t == 'o':
                    table = [f"{i}" for i in range(8)]
                elif t == 'x':
                    table = [f"{i}" for i in range(10)] + ['a', 'b', 'c', 'd', 'e', 'f']
                elif t == 'X':
                    table = [f"{i}" for i in range(10)] + ['A', 'B', 'C', 'D', 'E', 'F']
                elif t == 's':
                    input_strings.append(f)
                    continue
                else:
                    raise NotImplementedError(f"Not implement for format char:{t}")

                max_chars_per_format = max(max_chars_per_format, f.digits)
                # we use bytes representation as we need an exact size of the string
                digit_translation_tables[t] = "".join(table).encode(self.ENCODING)

        _string_rom = []
        strings_offset_and_size = {}
        # sort based on table inclusion and remove tables which are included in some larger table
        # e.g. d (0-9) is included in X (0-F)
        last_end = 0
        for i, s in sorted(strings.items(), key=lambda x: x[0]):
            strings_offset_and_size[i] = (last_end, len(s))
            _string_rom.append(s)
            last_end += len(s)
        for f_char, table in sorted(digit_translation_tables.items(), key=lambda x: x[0]):
            strings_offset_and_size[f_char] = (last_end, len(table))
            _string_rom.append(table)
            last_end += len(table)

        _string_rom = b"".join(_string_rom)

        return _string_rom, strings_offset_and_size, max_chars_per_format, max_bcd_digits

    def create_char_mux(self, in_, out_, char_i, digits, bits_per_digit):
        """
        Create a MUX which select the degit from input vector.
        Also perform necessary type casting for corner cases.
        """
        in_w = in_._dtype.bit_length()
        Switch(char_i)\
        .add_cases([
            (digits - i - 1,
             out_(
                    fitTo(
                        in_[min((i + 1) * bits_per_digit, in_w): i * bits_per_digit],
                        out_,
                        # moast significant digits may overlap the input size
                        extend=True,
                    )
                )
                if i * bits_per_digit < in_w else
                # case where there are more digits than in the input domain
                out_(0)
            )
            for i in range(digits)])\
        .Default(out_(None))
        # default branch should not be used as counter should not get to such a value


    def connect_single_format_group(self,
                                    f_i: int,
                                    f: Union[str, AxiS_strFormatItem],
                                    strings_offset_and_size: Dict[Union[int, str], Tuple[int, int]],
                                    string_rom: RtlSignal,
                                    char_i: RtlSignal,
                                    to_bcd_inputs: List[Tuple[RtlSignal, HdlStatement]],
                                    en: RtlSignal):
        """
        Connect a single formating group or string chunk to output.
        Depending on item type this may involve:

        * iterate the string characters stored in string_rom
        * iterate and translate bin/oct/hex characters
        * register bcd input for later connection
        * connect an input string from an input AxiStream
        """
        dout = self.data_out
        in_vld = BIT.from_py(1)
        res = []
        in_last = None
        string_rom_index_t = Bits(log2ceil(string_rom._dtype.size), signed=False)
        if isinstance(f, str):
            str_offset, str_size = strings_offset_and_size[f_i]
            str_offset = string_rom_index_t.from_py(str_offset)
            res.append(
                # read char of the string from string_rom
                dout.data(string_rom[str_offset + fitTo(char_i, str_offset, shrink=False)])
            )
        else:
            assert isinstance(f, AxiS_strFormatItem), f
            in_ = self.data_in._fieldsToInterfaces[f.member_path]

            if f.format_type in ('d', 'b', 'o', 'x', 'X'):
                if  f.format_type == 'd':
                    # first use BCD convertor to convert to BCD
                    to_bcd_inputs.append((en, in_))
                    bcd = self.bin_to_bcd.dout
                    in_vld = bcd.vld
                    bcd.rd(dout.ready & en & char_i._eq(f.digits - 1))
                    in_ = bcd.data

                bits_per_char = AxiS_strFormatItem.BITS_PER_CHAR[f.format_type]
                actual_digit = self._sig(f"f_{f_i}_actual_digit", Bits(bits_per_char))
                to_str_table_offset, _ = strings_offset_and_size[f.format_type]
                to_str_table_offset = string_rom_index_t.from_py(to_str_table_offset)
                # iterate output digits using char_i
                self.create_char_mux(in_, actual_digit, char_i, f.digits, bits_per_char)

                res.append(
                    # use char translation table from string_rom to translate digit in to a char
                    dout.data(string_rom[to_str_table_offset + fitTo(actual_digit, to_str_table_offset, shrink=False)])
                )

                str_size = f.digits

            else:
                # connect a string from an input AxiStream
                assert f.format_type == 's', f.format_type
                assert in_.DATA_WIDTH == 8, in_.DATA_WIDTH
                assert in_.USE_STRB == False, in_.USE_STRB
                assert in_.USE_KEEP == False, in_.USE_KEEP

                in_vld = in_.valid
                in_.ready(dout.ready & en)
                res.append(
                    dout.data(in_.data)
                )
                in_last = in_.last

        if in_last is None:
            # if signal to detect last character is not overriden use counter to resolve it
            in_last = char_i._eq(str_size - 1)

        return res, in_vld, in_last,

    def _impl(self) -> None:
        _string_rom, strings_offset_and_size, max_chars_per_format, max_bcd_digits = self.build_string_rom()
        if self.DATA_WIDTH != 8:
            # it self.DATA_WIDTH != 1B we need to handle all possible alignments and shifts, precompute some strings
            # because number of string memory ports is limited etc.
            raise NotImplementedError()
        # instanciate bin_to_bcd if required
        if max_bcd_digits > 0:
            bin_to_bcd = BinToBcd()
            bin_to_bcd.INPUT_WIDTH = log2ceil(10 ** max_bcd_digits - 1)
            self.bin_to_bcd = bin_to_bcd
        # tuples (cond, input)
        to_bcd_inputs = []

        string_rom = self._sig("string_rom", Bits(8)[len(_string_rom)], def_val=[int(c) for c in _string_rom])
        char_i = self._reg("char_i", Bits(log2ceil(max_chars_per_format), signed=False), def_val=0)

        # create an iterator over all characters
        element_cnt = len(self.FORMAT)
        dout = self.data_out
        if element_cnt == 1:
            en = 1
            f_i = 0
            f = self.FORMAT[f_i]
            _, out_vld, out_last = self.connect_single_format_group(f_i, f, strings_offset_and_size, string_rom, char_i, to_bcd_inputs, en)
            char_i_rst = out_last
        else:
            main_st = self._reg("main_st", Bits(log2ceil(element_cnt), signed=False), def_val=0)
            char_i_rst = out_last = out_vld = BIT.from_py(0)
            main_st_fsm = Switch(main_st)
            for is_last_f, (f_i, f) in iter_with_last(enumerate(self.FORMAT)):
                en = main_st._eq(f_i)
                data_drive, in_vld, in_last = self.connect_single_format_group(
                    f_i, f, strings_offset_and_size, string_rom, char_i,
                    to_bcd_inputs, en)
                # build out vld from all input valids
                out_vld = out_vld | (en & in_vld)
                # keep only last of the last part
                out_last = en & in_last
                char_i_rst = char_i_rst | out_last
                main_st_fsm.Case(
                    f_i,
                    If(dout.ready & in_vld & in_last,
                       main_st(0)
                       if is_last_f else
                       main_st(main_st + 1)
                    ),
                    *data_drive
                )
            main_st_fsm.Default(
                main_st(None),
                dout.data(None)
            )

        dout.valid(out_vld)
        dout.last(out_last)
        If(dout.ready & out_vld,
            If(char_i_rst,
               char_i(0)
            ).Else(
               char_i(char_i + 1)
            )
        )

        if to_bcd_inputs:
            in_ = bin_to_bcd.din
            SwitchLogic(
                # actual value may be smaller, because bcd is shared among
                # multiple input formats
                [(c, in_.data(fitTo(v, in_.data, shrink=False)))
                 for c, v in to_bcd_inputs],
                default=in_.data(None)
            )
            in_.vld(char_i._eq(0) & Or(*(c for c, _ in to_bcd_inputs)))
            propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiS_strFormat()
    print(to_rtl_str(u))

