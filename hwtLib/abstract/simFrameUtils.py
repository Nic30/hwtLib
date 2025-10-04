from math import ceil
from typing import Self, Union, Sequence, Generator, Generic, TypeVar, \
    Deque

from hwt.hdl.const import HConst
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.utils import HConst_from_words
from hwt.hwIO import HwIO

WordTupleTy = TypeVar('WordTupleTy')  # a type representing a word used by simulation agent for a target hwio

b8_t = HBits(8)


class SimFrameUtils(Generic[WordTupleTy]):
    """
    This class is a base class for utility classes which converts between pythonic formats of frames
    and formats used by simulation agents.

    :note: The main purpose is to simplify work with the frames and to make test agnostic to a specific stream hwio type.
    """

    def __init__(self, DATA_WIDTH: int):
        self.DATA_WIDTH = DATA_WIDTH

    @classmethod
    def from_HwIO(cls, hwio: HwIO) -> Self:
        """
        Create a an instance of self configured for specified hwio instance
        """
        raise NotImplementedError("Override this in your implementation of this abstract class")

    @staticmethod
    def _getWordDataFn(wordTuple:tuple[HConst]):
        return wordTuple[0]

    def _toHConst(self, v: Union[HConst, Sequence[int]]):
        isVoid = False
        if not isinstance(v, HConst):
            try:
                valByteCnt = len(v)
            except:
                v = tuple(v)
                valByteCnt = len(v)

            if valByteCnt == 0:
                v = None
                isVoid = True
            else:
                v = b8_t[valByteCnt].from_py(v)

        return v, isVoid

    def pack_frame(self, structVal: Union[HConst, Sequence[int]])\
            ->Generator[WordTupleTy, None, None]:
        """
        pack data of structure into words of target hwio
        Words are tuples specific to each hwio.
        
        :param structVal: value to be send, HConst instance or list of int for each byte
        
        :returns: generator of word tuples
        """
        raise NotImplementedError("Override this in your implementation of this abstract class")

    def unpack_frame(self, structT: HdlType, frameData: Deque[WordTupleTy]) -> HConst:
        """
        opposite of :meth:`~.pack_frame"
        """
        res = HConst_from_words(structT, frameData, self._getWordDataFn, self.DATA_WIDTH)
        for _ in range(ceil(structT.bit_length() / self.DATA_WIDTH)):
            frameData.popleft()

        return res

    def concatWordBits(self, frameBeats: Sequence[WordTupleTy]) -> Generator[HBitsConst, None, None]:
        """
        Convert word tuple (produced by :meth:`~.send_bytes`/:meth:`~.pack_frame`) to flat :class:`HBitsConst` (members of input tuple are typically ints so they need to be cast to correct type first)
        """
        raise NotImplementedError("Override this in your implementation of this abstract class")

    def updackWordBits(self):
        """
        opposite of concatWordBits
        """
        raise NotImplementedError("Override this in your implementation of this abstract class")

    def receive_bytes(self, ag_data: Deque[WordTupleTy]) -> tuple[int, list[int]]:
        """
        :param ag_data: list of stream hwio words
        :return: tuple dataStartOffset, data_Bytes
        """
        raise NotImplementedError("Override this in your implementation of this abstract class")

    def send_bytes(self, data_B: Union[bytes, list[int]], ag_data: Deque[WordTupleTy], offset:int=0)\
            ->list[WordTupleTy]:
        """
        Build frame out of data_B bytes and insert it into ag_data deque which is expected
        to be a queue of driver sim agent
        """
        if data_B:
            if isinstance(data_B, bytes):
                data_B = [int(x) for x in data_B]
            t = b8_t[len(data_B) + offset]
            _data_B = t.from_py([None for _ in range(offset)] + data_B)
        else:
            _data_B = data_B
        # :attention: strb signal is reinterpreted as a keep signal
        f = self.pack_frame(_data_B)
        ag_data.extend(f)
        return f
