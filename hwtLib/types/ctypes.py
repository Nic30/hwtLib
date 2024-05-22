from hwt.hdl.types.bits import HBits


char = HBits(8, False)
uint8_t = HBits(8, False)
int8_t = HBits(8, True)

uint16_t = HBits(16, False)
int16_t = HBits(16, True)

uint32_t = HBits(32, False)
int32_t = HBits(32, True)

uint64_t = HBits(64, False)
int64_t = HBits(64, True)
