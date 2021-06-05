import re
from typing import Generator, Union

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.structIntf import Interface_to_HdlType
from hwt.synthesizer.typePath import TypePath
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.strformat import AxiS_strFormat, AxiS_strFormatItem


def _parse_format_groups(f_str: str) -> Generator[Union[str, AxiS_strFormatItem], None, None]:
    _tokens = re.split("([\{\}])", f_str) + [None, ]
    group_start = None
    current_group_body = None
    tokens = iter(enumerate(_tokens))
    for i, t in tokens:
        if t is None:
            assert group_start is None
            break
        t_next = _tokens[i + 1]
        if group_start is None:
            if t == "{":
                if t_next == "{":
                    # escape of {
                    next(tokens)
                    yield t
                elif t_next == None:
                    raise ValueError("Group syntax error: missing closing } for { after reading:", tokens[:i + 1])
                else:
                    group_start = i
            elif t == '}':
                if t_next == '}':
                    # escape of }
                    next(tokens)
                    yield t
                else:
                    raise ValueError("Group syntax error: closing } without { after reading:",
                                     _tokens[:i + 1])
            else:
                yield t
        else:
            if t == "{":
                raise ValueError("Group syntax error: { in a group after reading:",
                                 _tokens[:i + 1], ", this group starts at", group_start)
            elif t == "}":
                if not current_group_body:
                    raise ValueError("Group syntax error: empty group after reading:",
                                     _tokens[:i + 1])
                else:
                    f = current_group_body.split(":")
                    name_or_index = f[0]
                    if len(f) == 1:
                        format_type = None
                        digits = None
                    else:
                        assert len(f) == 2, f
                        format_type = f[1]
                        for i, c in enumerate(format_type):
                            if not c.isdigit():
                                break
                        if i > 0:
                            digits = int(format_type[:i])
                        else:
                            digits = None
                        format_type = format_type[i:]
                    if name_or_index.isdigit():
                        name_or_index = int(name_or_index)
                    yield AxiS_strFormatItem(
                        TypePath(name_or_index),
                        format_type,
                        digits)
                    current_group_body = None
                    group_start = None
            else:
                assert not current_group_body, (
                    "group body has to be in a single string chunk",
                    current_group_body, t)
                current_group_body = t


def axiS_strFormat(parent: Unit, name: str, data_width: int, format_str: str,
                   *args, **kwargs):
    """
    Instanciate an :class:`hwtLib.amba.axis_comp.strformat.AxiS_strFormat` using simplified str.format syntax
    The syntax is allows for an utf-8 string with a variable format groups and several escape sequences
    in addition to normal string escape sequences.

    The escape sequences are (same as :func:`str.format`)


    .. code-block:: text

        +=======+=================+
        | char  | escape sequence |
        +=======+=================+
        | {     | {{              |
        +-------+-----------------+
        | }     | }}              |
        +-------+-----------------+

    The syntax for format group is as folowing:

    .. code-block:: text

        {[index/name]:[nuber_of_digits][type]}

    * The index or name specifies the name or the index of the input parameter.
    * The width specifies how mahy digits should the output have.
    * Format types can be found at :class:`hwtLib.amba.axis_comp.strformat.AxiS_strFormatItem`
    * If nuber_of_digits starts with 0 the leading zeros will be used instead of default space char (' ')
    * The sign char is included in nuber_of_digits ('{0:04X}'.format(-1) == '-001')
    * The type is described in :class:`hwtLib.amba.axis_comp.strformat.AxiS_strFormatItem`
    """

    f = AxiS_strFormat()
    f.DATA_WIDTH = data_width

    # construct input t for configuration
    arg_prefix = "arg_"
    while True:
        arg_names = [f"{arg_prefix}{a_i}" for a_i, _ in enumerate(args)]
        if not kwargs:
            break
        else:
            colliding = False
            for a in arg_names:
                if a in kwargs.keys():
                    colliding = True
            if colliding:
                arg_prefix = f"{arg_prefix}0_"
            else:
                break

    in_intf_name_tuples = [
        *zip(args, arg_names),
        *[
            (a, a_name)
            for a_name, a in sorted(kwargs.items(), key=lambda x: x[0])
         ]
    ]

    format_items = tuple(_parse_format_groups(format_str))
    for fi in format_items:
        if isinstance(fi, str):
            continue
        elif isinstance(fi.member_path[0], int):
            # convert arg index to name in input interface
            fi.member_path = TypePath(arg_names[fi.member_path[0]])

    arg_usage = {}
    for fi in format_items:
        if isinstance(fi, str):
            continue
        usage_cnt  = arg_usage.get(fi.member_path, 0) + 1
        arg_usage[fi.member_path] = usage_cnt
        if fi.format_type == 's':
            assert usage_cnt == 1, ("string arguments may be used only once as string is consumed")

    for i, (a, a_name) in enumerate(in_intf_name_tuples):
        assert arg_usage.get(TypePath(a_name), 0) > 0, ("arg ", i, " named ", a_name, " not used during formating")

    if in_intf_name_tuples:
        struct_members = []
        for a, a_name in in_intf_name_tuples:
            if isinstance(a, AxiStream):
                t = HStream(Bits(8), start_offsets=[0])
            else:
                t = Interface_to_HdlType().apply(a)
            struct_members.append((t, a_name))
        f.INPUT_T = HStruct(*struct_members)
    else:
        f.INPUT_T = None
    f.FORMAT = tuple(format_items)

    # connect inputs
    setattr(parent, name, f)
    for a, a_name in in_intf_name_tuples:
        a_in = getattr(f.data_in, a_name)
        a_in(a)

    return f.data_out
