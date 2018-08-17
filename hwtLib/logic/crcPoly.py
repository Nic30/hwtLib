# http://reveng.sourceforge.net/crc-catalogue/all.htm

"""
Library of common CRC configurations
"""


# also known as parity bit
class CRC_1:
    POLY = 0x1
    WIDTH = 1
    REFIN = False
    REFOUT = False


# mobile networks
class CRC_3_GSM:
    INIT = 0x0
    POLY = 0x3
    REFIN = False
    REFOUT = False
    WIDTH = 3


# G.704
class CRC_4_ITU:
    POLY = 0x3
    WIDTH = 4


# Gen 2 RFID
class CRC_5_EPC:
    POLY = 0x09
    WIDTH = 5


# G.704
class CRC_5_ITU:
    POLY = 0x15
    WIDTH = 5


# USB token packets
class CRC_5_USB:
    CHECK = 0x19
    INIT = 0b11111
    REFIN = True
    REFOUT = True
    RESIDUE = 0b01100
    POLY = 0x05
    WIDTH = 5
    XOROUT = 0x1f


# mobile networks
class CRC_6_CDMA2000_A:
    POLY = 0x27
    WIDTH = 6


# mobile networks
class CRC_6_CDMA2000_B:
    POLY = 0x07
    WIDTH = 6


# Data Radio Channel
class CRC_6_DARC:
    POLY = 0x19
    WIDTH = 6


# mobile networks
class CRC_6_GSM:
    POLY = 0x2F
    WIDTH = 6


# G.704
class CRC_6_ITU:
    POLY = 0x03
    WIDTH = 6


# telecom systems, G.707,G.832, MMC, SD
class CRC_7:
    POLY = 0x09
    WIDTH = 7


# Train Communication Network, IEC 60870-5
class CRC_7_MVB:
    POLY = 0x65
    WIDTH = 7


# DVB-S2
class CRC_8:
    POLY = 0xD5
    WIDTH = 8


# automotive integration,OpenSafety
class CRC_8_AUTOSAR:
    POLY = 0x2F
    WIDTH = 8


# wireless connectivity
class CRC_8_Bluetooth:
    POLY = 0xA7
    WIDTH = 8


# I.432.1; ATM HEC, ISDN HEC and cell delineation
class CRC_8_CCITT:
    CHECK = 0xf4
    INIT = 0X00
    POLY = 0x07
    WIDTH = 8
    REFIN = False
    REFOUT = False
    RESIDUE = 0x00
    XOROUT = 0x00


# 1-Wire bus
class CRC_8_Dallas_Maxim:
    POLY = 0x31
    WIDTH = 8


# Data Radio Channel
class CRC_8_DARC:
    POLY = 0x39
    WIDTH = 8


# mobile networks
class CRC_8_GSM_B:
    POLY = 0x49
    WIDTH = 8


# AES3
class CRC_8_SAE_J1850:
    POLY = 0x1D
    WIDTH = 8


# mobile networks
class CRC_8_WCDMA:
    CHECK = 0x25
    INIT = 0X00
    POLY = 0x9B
    REFIN = True
    REFOUT = True
    RESIDUE = 0x00
    WIDTH = 8
    XOROUT = 0x00


# ATM; I.610
class CRC_10:
    POLY = 0x233
    WIDTH = 10


# mobile networks
class CRC_10_CDMA2000:
    POLY = 0x3D9
    WIDTH = 10


# mobile networks
class CRC_10_GSM:
    POLY = 0x175
    WIDTH = 10


# FlexRay
class CRC_11:
    POLY = 0x385
    WIDTH = 11


# telecom systems
class CRC_12:
    POLY = 0x80F
    WIDTH = 12


# mobile networks
class CRC_12_CDMA2000:
    POLY = 0xF13
    WIDTH = 12


# mobile networks
class CRC_12_GSM:
    POLY = 0xD31
    WIDTH = 12


# Time signal, Radio teleswitch
class CRC_13_BBC:
    POLY = 0x1CF5
    WIDTH = 13


# Data Radio Channel[19]
class CRC_14_DARC:
    POLY = 0x0805
    WIDTH = 14


# mobile networks
class CRC_14_GSM:
    POLY = 0x202D
    WIDTH = 14


class CRC_15_CAN:
    POLY = 0x4599
    WIDTH = 15


class CRC_15_MPT1327:
    POLY = 0x6815
    WIDTH = 15


# Optimal for payloads ≤64 bits
class CRC_16_Chakravarty:
    POLY = 0x2F15
    WIDTH = 16


# ACARS applications
class CRC_16_ARINC:
    POLY = 0xA02B
    WIDTH = 16


# X.25, V.41, HDLC FCS, XMODEM, Bluetooth, PACTOR, SD, DigRF, many others;
# known as CRC_CCITT
class CRC_16_CCITT:
    INIT = 0xFFFF
    POLY = 0x1021
    WIDTH = 16
    REFIN = False
    REFOUT = False
    XOROUT = 0x0000


# mobile networks
class CRC_16_CDMA2000:
    POLY = 0xC867
    WIDTH = 16


# cordless telephones
class CRC_16_DECT:
    POLY = 0x0589
    WIDTH = 16


# SCSI DIF
class CRC_16_T10_DIF:
    POLY = 0x8BB7
    WIDTH = 16


# DNP, IEC 870, M-Bus
class CRC_16_DNP:
    POLY = 0x3D65
    WIDTH = 16


# Bisync, Modbus, USB, ANSI X3.28, SIA DC-07, many others;
# also known as CRC_16 and CRC_16-ANSI
class CRC_16_IBM:
    INIT = 0000
    POLY = 0x8005
    REFIN = True
    REFOUT = True
    WIDTH = 16
    XOROUT = 0000


# safety fieldbus
class CRC_16_OpenSafety_A:
    POLY = 0x5935
    WIDTH = 16


# safety fieldbus
class CRC_16_OpenSafety_B:
    POLY = 0x755B
    WIDTH = 16


# fieldbus networks
class CRC_16_Profibus:
    POLY = 0x1DCF
    WIDTH = 16


# CAN FD
class CRC_17_CAN:
    POLY = 0x1685B
    WIDTH = 17


# CAN FD
class CRC_21_CAN:
    POLY = 0x102899
    WIDTH = 21


# FlexRay
class CRC_24:
    POLY = 0x5D6DCB
    WIDTH = 24


# OpenPGP, RTCM104v3
class CRC_24_Radix_64:
    POLY = 0x864CFB
    WIDTH = 24


# CDMA
class CRC_30:
    POLY = 0x2030B9C7
    WIDTH = 30


# HDLC, ANSI X3.66, ITU-T V.42, Ethernet, Serial ATA,
# MPEG-2, PKZIP, Gzip, Bzip2, PNG, many others
class CRC_32:
    INIT = 0xffffffff
    POLY = 0x04C11DB7
    RESIDUE = 0xC704DD7B  # CBF43926
    REFIN = True
    REFOUT = True
    WIDTH = 32
    XOROUT = 0xffffffff


# (Castagnoli), iSCSI, SCTP, G.hn payload, SSE4.2, Btrfs, ext4, Ceph
class CRC_32C:
    INIT = 0Xffffffff
    CHECK = 0xe3069283
    POLY = 0x1EDC6F41
    WIDTH = 32
    REFIN = True
    REFOUT = True
    RESIDUE = 0xb798b438
    XOROUT = 0xffffffff


# Koopman {1,3,28}
class CRC_32K:
    POLY = 0x741B8CD7
    WIDTH = 32


# Koopman {1,1,30}
class CRC_32K_2:
    POLY = 0x32583499
    WIDTH = 32


# aviation; AIXM
class CRC_32Q:
    POLY = 0x814141AB
    WIDTH = 32


# GSM control channel[40][41]
class CRC_40_GSM:
    POLY = 0x0004820009
    WIDTH = 40


# ECMA-182, XZ Utils
class CRC_64_ECMA:
    POLY = 0x42F0E1EBA9EA3693
    WIDTH = 64


# HDLC, Swiss-Prot/TrEMBL; considered weak for hashing
class CRC_64_ISO:
    POLY = 0x000000000000001B
    WIDTH = 64
