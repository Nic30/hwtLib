from typing import Optional

from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class RtlSignalBuilder():

    @staticmethod
    def buildAndOptional(a:Optional[RtlSignal],
                         b:Optional[RtlSignal]):
        if a is None:
            if b is None:
                return None
            else:
                return b
        else:
            if b is None or a is b:
                return a
            else:
                return b & a

    @staticmethod
    def buildOrOptional(a:Optional[RtlSignal],
                        b:Optional[RtlSignal]):
        if a is None:
            if b is None:
                return None
            else:
                return b
        else:
            if b is None or a is b:
                return a
            else:
                return b | a

    @staticmethod
    def buildOrNegatedMaskOptional(a:Optional[RtlSignal], aMask:Optional[RtlSignal]):
        if a is None:
            if aMask is None:
                return None
            else:
                return ~aMask
        else:
            if aMask is None:
                return a
            else:
                return a & ~aMask

    @staticmethod
    def buildOrWithNegatedMaskedOptional(
                                     a:Optional[RtlSignal],
                                     b:Optional[RtlSignal],
                                     bMask:Optional[RtlSignal]):
        """
        :return: a | (b & ~bMask) where every member can be None
        """
        if a is None:
            if bMask is None:
                if b is None:
                    return None
                else:
                    return b
            else:
                return b & ~bMask
        else:
            if a is b:
                return a
            elif bMask is None:
                return a | b
            else:
                return a | (b & ~bMask)

    @staticmethod
    def buildAndNegatedMaskedOptional(a:Optional[RtlSignal],
                                      b:Optional[RtlSignal],
                                      bMask:Optional[RtlSignal]):
        if a is None:
            if bMask is None or b is bMask:
                return b
            elif b is None:
                return None
            else:
                return b & ~bMask
        else:
            if bMask is None:
                if b is None or a is b:
                    return a
                else:
                    return a & b
            else:
                if b is None or b is bMask:
                    return a & ~bMask
                else:
                    return a & (b & ~bMask)
