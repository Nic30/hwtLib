# http://reveng.sourceforge.net/crc-catalogue/all.htm
"""
Library of common CRC configurations

:note: POLY is the polynome of CRC and specifies which bits
    should be xored together.
:note: WIDTH - specifies the width of CRC state/value
:note: REFIN - If it is True the bits in each byte are reversed before processing.
:note: REFOUT If it is set to FALSE, the
    final value in the register is fed into the XOROUT stage directly,
    otherwise, if this parameter is TRUE, the final register value is
    reflected first.
:note: XOROUT This is an WIDTH-bit value. It is XORed to the final register value
    (after the REFOUT) stage before the value is returned as the official
    checksum.

:note: http://reveng.sourceforge.net/crc-catalogue/all.htm
:note: https://github.com/nanpuyue/crc/blob/master/CRC.txt
"""


class CRC_POLY:
    """
    Base class for crc configuration specifications
    """
    POLY = None
    WIDTH = None
    INIT = 0
    REFIN = False
    REFOUT = False
    XOROUT = 0


class CRC_1(CRC_POLY):
    """
    also known as parity bit
    """
    POLY = 0x1
    WIDTH = 1


class CRC_3_GSM(CRC_POLY):
    """
    Used in mobile networks
    """
    INIT = 0x0
    POLY = 0x3
    XOROUT = 0x07
    WIDTH = 3


class CRC3_ROHC(CRC_POLY):
    "CRC-3/ROHC (Robust header compression rfc3095)"
    WIDTH = 3
    POLY = 0x03
    INIT = 0x07
    REFIN = True
    REFOUT = True
    CHECK = 0x6
    RESIDUE = 0x0


class CRC_4_ITU(CRC_POLY):
    """
    G.704
    """
    POLY = 0x3
    WIDTH = 4
    REFIN = True
    REFOUT = True
    CHECK = 0x7
    RESIDUE = 0x0


class CRC_5_EPC(CRC_POLY):
    """
    Gen 2 RFID EPC-C1G2
    """
    POLY = 0x09
    WIDTH = 5
    CHECK = 0x00
    RESIDUE = 0x00


class CRC_5_ITU(CRC_POLY):
    """
    G.704
    """
    POLY = 0x15
    WIDTH = 5


class CRC_5_USB(CRC_POLY):
    """
    USB token packets
    """
    CHECK = 0x19
    INIT = 0b11111
    REFIN = True
    REFOUT = True
    RESIDUE = 0b01100
    POLY = 0x05
    WIDTH = 5
    XOROUT = 0x1f


class CRC_6_CDMA2000_A(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x27
    WIDTH = 6


class CRC_6_CDMA2000_B(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x07
    WIDTH = 6


class CRC_6_DARC(CRC_POLY):
    "Data Radio Channel"
    POLY = 0x19
    WIDTH = 6


class CRC_6_GSM(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x2F
    WIDTH = 6


class CRC_6_ITU(CRC_POLY):
    "Used in G.704"
    POLY = 0x03
    WIDTH = 6


class CRC_7(CRC_POLY):
    "Used in telecom systems, G.707,G.832, MMC, SD"
    POLY = 0x09
    WIDTH = 7


class CRC_7_MVB(CRC_POLY):
    "Used in Train Communication Network, IEC 60870-5"
    POLY = 0x65
    WIDTH = 7


class CRC_8(CRC_POLY):
    "Used in DVB-S2"
    POLY = 0xD5
    WIDTH = 8


class CRC_8_AUTOSAR(CRC_POLY):
    "Used in automotive integration, OpenSafety"
    POLY = 0x2F
    WIDTH = 8


class CRC_8_Bluetooth(CRC_POLY):
    "Used in wireless connectivity"
    POLY = 0xA7
    WIDTH = 8


class CRC_8_CCITT(CRC_POLY):
    "Used in I.432.1; ATM HEC, ISDN HEC and cell delineation"
    CHECK = 0xf4
    POLY = 0x07
    WIDTH = 8
    RESIDUE = 0x00


class CRC_8_Dallas_Maxim(CRC_POLY):
    "Used in 1-Wire bus"
    POLY = 0x31
    WIDTH = 8


class CRC_8_DARC(CRC_POLY):
    "Used in Data Radio Channel"
    POLY = 0x39
    WIDTH = 8


class CRC_8_GSM_B(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x49
    WIDTH = 8


class CRC_8_SAE_J1850(CRC_POLY):
    "Used in AES3"
    POLY = 0x1D
    WIDTH = 8


class CRC_8_WCDMA(CRC_POLY):
    "Used in mobile networks"
    CHECK = 0x25
    INIT = 0X00
    POLY = 0x9B
    REFIN = True
    REFOUT = True
    RESIDUE = 0x00
    WIDTH = 8


class CRC_10(CRC_POLY):
    "Used in ATM; I.610"
    POLY = 0x233
    WIDTH = 10


class CRC_10_CDMA2000(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x3D9
    WIDTH = 10


class CRC_10_GSM(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x175
    WIDTH = 10


class CRC_11(CRC_POLY):
    "Used in FlexRay"
    POLY = 0x385
    WIDTH = 11


class CRC_12(CRC_POLY):
    "Used in telecom systems"
    POLY = 0x80F
    WIDTH = 12


class CRC_12_CDMA2000(CRC_POLY):
    "Used in mobile networks"
    POLY = 0xF13
    WIDTH = 12


class CRC_12_GSM(CRC_POLY):
    "Used in mobile networks"
    POLY = 0xD31
    WIDTH = 12


class CRC_13_BBC(CRC_POLY):
    "Used in Time signal, Radio teleswitch"
    POLY = 0x1CF5
    WIDTH = 13


class CRC_14_DARC(CRC_POLY):
    "Used in Data Radio Channel[19]"
    POLY = 0x0805
    WIDTH = 14


class CRC_14_GSM(CRC_POLY):
    "Used in mobile networks"
    POLY = 0x202D
    WIDTH = 14


class CRC_15_CAN(CRC_POLY):
    POLY = 0x4599
    WIDTH = 15


class CRC_15_MPT1327(CRC_POLY):
    POLY = 0x6815
    WIDTH = 15


class CRC_16_Chakravarty(CRC_POLY):
    "Used in Optimal for payloads ≤64 bits"
    POLY = 0x2F15
    WIDTH = 16


class CRC_16_ARINC(CRC_POLY):
    "Used in ACARS applications"
    POLY = 0xA02B
    WIDTH = 16


class CRC_16_CCITT(CRC_POLY):
    """
    Used in X.25, V.41, HDLC FCS, XMODEM, Bluetooth, PACTOR, SD, DigRF, many others;
    Also known as CRC_CCITT
    """
    INIT = 0xFFFF
    POLY = 0x1021
    WIDTH = 16


class CRC_16_CDMA2000(CRC_POLY):
    "Used in mobile networks"
    POLY = 0xC867
    WIDTH = 16


class CRC_16_DECT(CRC_POLY):
    "Used in cordless telephones"
    POLY = 0x0589
    WIDTH = 16


class CRC_16_T10_DIF(CRC_POLY):
    "Used in SCSI DIF"
    POLY = 0x8BB7
    WIDTH = 16


class CRC_16_DNP(CRC_POLY):
    "Used in DNP, IEC 870, M-Bus"
    POLY = 0x3D65
    WIDTH = 16


class CRC_16_IBM(CRC_POLY):
    """
    Used in Bisync, Modbus, ANSI X3.28, SIA DC-07, many others;
    Also known as CRC_16 and CRC_16-ANSI
    """
    POLY = 0x8005
    REFIN = True
    REFOUT = True
    WIDTH = 16

class CRC_16_USB:
    POLY=0x8005
    INIT=0XFFFF
    REFIN=True
    REFOUT=True
    XOROUT=0XFFFF
    CHECK=0XB4C8
    RESIDUE=0XB001
    WIDTH=16

class CRC_16_OpenSafety_A(CRC_POLY):
    "Used in safety fieldbus"
    POLY = 0x5935
    WIDTH = 16


class CRC_16_OpenSafety_B(CRC_POLY):
    "Used in safety fieldbus"
    POLY = 0x755B
    WIDTH = 16


class CRC_16_Profibus(CRC_POLY):
    "Used in fieldbus networks"
    POLY = 0x1DCF
    WIDTH = 16


class CRC_17_CAN(CRC_POLY):
    "Used in CAN FD"
    POLY = 0x1685B
    WIDTH = 17


class CRC_21_CAN(CRC_POLY):
    "Used in CAN FD"
    POLY = 0x102899
    WIDTH = 21


class CRC_24(CRC_POLY):
    "Used in FlexRay"
    POLY = 0x5D6DCB
    WIDTH = 24


class CRC_24_Radix_64(CRC_POLY):
    "Used in OpenPGP, RTCM104v3"
    POLY = 0x864CFB
    WIDTH = 24


class CRC_30(CRC_POLY):
    "Used in CDMA"
    POLY = 0x2030B9C7
    WIDTH = 30


class CRC_32(CRC_POLY):
    """
    Used in  HDLC, ANSI X3.66, ITU-T V.42, Ethernet, Serial ATA,
    MPEG-2, PKZIP, Gzip, Bzip2, PNG, many others
    """
    INIT = 0xffffffff
    POLY = 0x04C11DB7
    RESIDUE = 0xC704DD7B  # CBF43926
    REFIN = True
    REFOUT = True
    WIDTH = 32
    XOROUT = 0xffffffff


class CRC_32C(CRC_POLY):
    "Used in (Castagnoli), iSCSI, SCTP, G.hn payload, SSE4.2, Btrfs, ext4, Ceph"
    INIT = 0Xffffffff
    CHECK = 0xe3069283
    POLY = 0x1EDC6F41
    WIDTH = 32
    REFIN = True
    REFOUT = True
    RESIDUE = 0xb798b438
    XOROUT = 0xffffffff


class CRC_32K(CRC_POLY):
    "Koopman {1,3,28}"
    POLY = 0x741B8CD7
    WIDTH = 32


class CRC_32K_2(CRC_POLY):
    "Koopman {1,1,30}"
    POLY = 0x32583499
    WIDTH = 32


class CRC_32Q(CRC_POLY):
    "Used in aviation; AIXM"
    POLY = 0x814141AB
    WIDTH = 32


class CRC_40_GSM(CRC_POLY):
    "Used in GSM control channel[40][41]"
    POLY = 0x0004820009
    WIDTH = 40


class CRC_64_ECMA(CRC_POLY):
    "Used in ECMA-182, XZ Utils"
    POLY = 0x42F0E1EBA9EA3693
    WIDTH = 64


class CRC_64_ISO(CRC_POLY):
    "Used in HDLC, Swiss-Prot/TrEMBL; considered weak for hashing"
    POLY = 0x000000000000001B
    WIDTH = 64
