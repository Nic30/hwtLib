from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint64_t, uint16_t, uint32_t


structManyInts = HStruct(
    (uint64_t, "i0"),
    (uint64_t, None),  # dummy word
    (uint64_t, "i1"),
    (uint64_t, None),
    (uint16_t, "i2"),
    (uint16_t, "i3"),
    (uint32_t, "i4"),  # 3 items in one word

    (uint32_t, None),
    (uint64_t, "i5"),  # this word is split on two bus words
    (uint32_t, None),

    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, None),
    (uint64_t, "i6"),
    (uint64_t, "i7"),
)

MAGIC = 14
ref0_structManyInts = {
    "i0": MAGIC + 1,
    "i1": MAGIC + 2,
    "i2": MAGIC + 3,
    "i3": MAGIC + 4,
    "i4": MAGIC + 5,
    "i5": MAGIC + 6,
    "i6": MAGIC + 7,
    "i7": MAGIC + 8,
}
ref1_structManyInts = {
    "i0": MAGIC + 10,
    "i1": MAGIC + 20,
    "i2": MAGIC + 30,
    "i3": MAGIC + 40,
    "i4": MAGIC + 50,
    "i5": MAGIC + 60,
    "i6": MAGIC + 70,
    "i7": MAGIC + 80,
}


ref_unionOfStructs0 = (
    "frameA", {
        "itemA0": MAGIC + 1,
        "itemA1": MAGIC + 2,
    },
)

ref_unionOfStructs1 = (
    "frameA", {
        "itemA0": MAGIC + 10,
        "itemA1": MAGIC + 20,
    },
)

ref_unionOfStructs2 = (
    "frameB", {
        "itemB0": MAGIC + 3,
        "itemB1": MAGIC + 4,
        "itemB2": MAGIC + 5,
        "itemB3": MAGIC + 6,
    }
)

ref_unionOfStructs3 = (
    "frameB", {
        "itemB0": MAGIC + 30,
        "itemB1": MAGIC + 40,
        "itemB2": MAGIC + 50,
        "itemB3": MAGIC + 60,
    }
)


ref_unionSimple0 = ("a", MAGIC + 1)
ref_unionSimple1 = ("a", MAGIC + 10)
ref_unionSimple2 = ("b", MAGIC + 2)
ref_unionSimple3 = ("b", MAGIC + 20)
