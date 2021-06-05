from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwtLib.types.ctypes import uint64_t, uint32_t, int32_t, uint8_t
from math import inf


s1field = HStruct(
    (uint64_t, "item0")
)

s3field = HStruct(
    (uint64_t, "item0"),
    (uint64_t, "item1"),
    (uint64_t, "item2")
)

s2Pading = HStruct(
    (uint64_t, "item0_0"),
    (uint64_t, "item0_1"),
    (uint64_t, None),
    (uint64_t, "item1_0"),
    (uint64_t, "item1_1"),
    (uint64_t, None),
)

s1field_composit0 = HStruct(
    (uint32_t, "item0"), (uint32_t, "item1"),
)

unionOfStructs = HUnion(
    (HStruct(
        (uint64_t, "itemA0"),
        (uint64_t, "itemA1")
        ), "frameA"),
    (HStruct(
        (uint32_t, "itemB0"),
        (uint32_t, "itemB1"),
        (uint32_t, "itemB2"),
        (uint32_t, "itemB3")
        ), "frameB")
)

unionSimple = HUnion(
    (uint32_t, "a"),
    (int32_t, "b")
)

structStream64 = HStruct(
    (HStream(uint64_t), "streamIn")
)

structStream64before = HStruct(
    (HStream(uint64_t), "streamIn"),
    (uint64_t, "item0"),
)

structStream64after = HStruct(
    (uint64_t, "item0"),
    (HStream(uint64_t), "streamIn"),
)

struct2xStream64 = HStruct(
    (HStream(uint64_t), "streamIn0"),
    (HStream(uint64_t), "streamIn1")
)

structStreamAndFooter = HStruct(
    (HStream(uint8_t), "data"),
    (uint32_t, "footer"),
)

struct2xStream8 = HStruct(
    (HStream(uint8_t), "streamIn0"),
    (HStream(uint8_t), "streamIn1")
)

struct2xStream8_0B = HStruct(
    (HStream(uint8_t, frame_len=(0, inf)), "streamIn0"),
    (HStream(uint8_t, frame_len=(0, inf)), "streamIn1")
)

unionDifferentMask = HUnion(
    (HStruct((uint8_t, "data"), (uint8_t, None)), "u0"),
    (HStruct((uint8_t, None), (uint8_t, "data")), "u1"),
)

