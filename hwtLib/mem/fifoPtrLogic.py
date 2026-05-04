#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import chain
from typing import Union, Optional

from hwt.code import If
from hwt.doc_markers import hwt_expr_producer, hwt_stm_producer
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.bitsRtlSignal import HBitsRtlSignal
from hwt.hwModule import HwModule
from hwt.math import log2ceil, isPow2
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal

EnWaitIncrValTuple = Union[
    tuple[HBitsRtlSignal, HBitsRtlSignal],  # en, wait
    tuple[HBitsRtlSignal, HBitsRtlSignal, Union[int, HBitsRtlSignal]],  # en, wait, incrVal
]


class FifoPtrLogic():
    """
        
    :note: r_ptr=index which is going to be read
    :note: w_ptr=index which is going to be written
    
    Variant of read_ptr/write_ptr implementations
    =============================================
    :note: in all variants r_ptr is initialized to 0, w_ptr to number of interms preloaded in FIFO
    :note: variants with ram.R_LATENCY=1 will latch mem[rd_ptr] if fifo_read 
        so the mem[rd_ptr] is not safe to be written in any variant unless the fifo is empty

    .. code-block::python
        # ram.R_LATENCY=0
        output = ram[read_ptr];
        
        # ram.R_LATENCY=1
        If(self.clk._onRisingEdge(),
            If(fifo_read,
                output(mem[rd_ptr])
            )
        )
    
    Variant with r_wait = w_ptr == r_ptr
    ------------------------------------
    * EFFECTIVE_DEPTH = DEPTH - 1
    * timing issues: w_wait expressions contain add and saturation
    .. code-block::python
       full  = w_wait = (w_ptr+1) % DEPTH == r_ptr
       empty = r_wait = w_ptr == r_ptr
         
       #   rw   
       # [ - - - - ]  
       # 
       #   r     w
       # [ 0 1 2 - ]  
       # 
       #     w r 
       # [ 2 - 0 1 ]  # full=1
       # 
       #       wr 
       # [ 2 3 0 1 ]  # not possible with this pointer logic
       
    * ram.R_LATENCY=1: https://vlsiverify.com/verilog/verilog-codes/synchronous-fifo/
    
    Variant with r_wait = count != 0
    --------------------------------
    * Use of explicit count register may be resource/timing inefficient 
    * EFFECTIVE_DEPTH = DEPTH
    * https://www.asic-world.com/examples/verilog/syn_fifo.html   
    * https://www.digikey.com/en/maker/tutorials/2025/fifo-design-in-systemverilog
    
    Variant with item lock flag
    --------------------------------
    Uses explicit flag to check if the w_ptr moved to r_ptr or r_ptr moved to w_ptr
    * EFFECTIVE_DEPTH = DEPTH
    
     .. code-block::python
        # last_was_r = 0 means current item is locked for write and 1 means for read
        last_was_r = 1 # reset value for empty FIFO
        # cycle step
        if r_en && ~r_wait:
            # lock current item for read 
            last_was_r = 1
        elif w_en & ~w_wait:
            # lock current item for write
            last_was_r = 0
        # :note: if w_ptr.next != r_ptr.next the value will be ignored
        full  = w_wait = (w_ptr._eq(r_ptr)) & ~last_was_read
        empty = r_wait = (w_ptr._eq(r_ptr)) &  last_was_read
     * ram.R_LATENCY=0: https://medium.com/@aiclab.official/fifo-design-and-implementation-tutorial-in-rtl-systemverilog-f11d4c78e3e8
    
    Variant with XORed item lock flag
    --------------------------------------
    Distributed last_was_r set to crossed0_r, crossed0_w
    crossed0_r/crossed0_w is filipped if pointer overflows
    * EFFECTIVE_DEPTH = DEPTH
    .. code-block::python
        r_is_before_w = crossed0_r == crossed0_w
        w_is_before_r = crossed0_r != crossed0_w
        full  = w_wait = (w_ptr._eq(r_ptr)) & ~r_is_before_w
        empty = r_wait = (w_ptr._eq(r_ptr)) &  r_is_before_w
    
    * ram.R_LATENCY=1: https://gist.github.com/C47D/e299230c65b82a87d7fc83579d78b168?permalink_comment_id=4216482#gistcomment-4216482
       * only for pow2 depth 
    """

    def __init__(self, parent: HwModule, DEPTH: int, RAM_SIZE: Optional[int]=None, INIT_SIZE:int=0):
        if RAM_SIZE is None:
            RAM_SIZE = DEPTH
        self.RAM_SIZE = RAM_SIZE
        self.parent = parent
        assert DEPTH > 1, DEPTH
        self.DEPTH = DEPTH
        assert INIT_SIZE < DEPTH, (INIT_SIZE, DEPTH)
        self.INIT_SIZE = INIT_SIZE
        self.PTR_MAX = DEPTH - 1
        self.index_t = HBits(log2ceil(DEPTH), signed=False)

    @hwt_expr_producer
    def _usub_with_modulo(self, v: RtlSignal, decrVal: Union[int, RtlSignal]):
        MAX = self.PTR_MAX
        t = v._dtype.from_py
        DEPTH = self.DEPTH
        if isPow2(DEPTH):
            return v - decrVal
        elif isinstance(decrVal, int) and MAX % decrVal == 0:
            return (v._eq(0))._ternary(t(MAX - (decrVal - 1)), v - decrVal)
        else:
            # return (v < decrVal)._ternary(t(MAX) - (v - decrVal), v - decrVal)
            w = v._dtype.bit_length()
            if isinstance(decrVal, int):
                decrVal = t(decrVal)

            else:
                full_sum = v._ext(w + 1) - decrVal._ext(w + 1)
                overflow = full_sum.getMsb() | (full_sum >= self.DEPTH)
                intMax_min_depth = ((1 << (w)) - self.DEPTH)
                return overflow._ternary(v - decrVal - intMax_min_depth,
                                         v - decrVal)

    @hwt_expr_producer
    def _uadd_with_modulo(self, v: RtlSignal, incrVal: Union[int, RtlSignal]):
        MAX = self.PTR_MAX
        DEPTH = self.DEPTH
        t = v._dtype.from_py
        if isPow2(DEPTH):
            return v + incrVal
        elif isinstance(incrVal, int) and DEPTH % incrVal == 0:
            return (v._eq(MAX))._ternary(t(0), v + incrVal)
        else:
            w = v._dtype.bit_length()
            if isinstance(incrVal, int):
                incrVal = t(incrVal)

            full_sum = v._ext(w + 1) + incrVal._ext(w + 1)
            overflow = full_sum.getMsb() | (full_sum >= self.DEPTH)
            intMax_min_depth = ((1 << (w)) - self.DEPTH)
            return overflow._ternary(v + incrVal + intMax_min_depth,
                                 v + incrVal)

    @staticmethod
    def _normalize_EnWaitIncrValTuple(en_wait_incrVal: EnWaitIncrValTuple) -> EnWaitIncrValTuple:
        if len(en_wait_incrVal) == 2:
            en, wait = en_wait_incrVal
            incr = 1
            return (en, wait, incr)
        else:
            assert len(en_wait_incrVal) == 3, en_wait_incrVal
            return en_wait_incrVal

    @hwt_expr_producer
    def _is_fifo_ptr_add_possible(self,
                                  ptr0: RtlSignal, ptr1: Union[RtlSignal, int],
                                  allow_eq: RtlSignal,
                                  ptr0IncrVal: Union[HBitsRtlSignal, int]
                                  ) -> RtlSignal:
        DEPTH = self.DEPTH
        if isinstance(ptr0IncrVal, int) and DEPTH % ptr0IncrVal == 0:
            assert ptr0IncrVal <= DEPTH, (ptr0IncrVal, DEPTH)
            wouldCross0 = ptr0._eq(DEPTH - ptr0IncrVal)
        else:
            if isPow2(DEPTH):
                wouldCross0 = (ptr0 + ptr0IncrVal) < ptr0
            else:
                wouldCross0 = ((ptr0 + ptr0IncrVal) < ptr0) | ((ptr0 + ptr0IncrVal) >= DEPTH)

        # can not move if ptr0 + ptr0IncrVal would cross the value of ptr1
        if isinstance(ptr0IncrVal, int) and ptr0IncrVal == 1:
            # there is only a single value which ptr0 can not have if ~allow_eq
            addPossible = allow_eq | (ptr0 != ptr1)
        else:
            # there is a range of value which ptr0 can not have.
            # ~allow_eq modifies this range
            dist = self._fifo_ptr_distance(ptr0, ptr1)
            if isinstance(ptr0IncrVal, int):
                ptr0IncrVal = ptr0._dtype.from_py(ptr0IncrVal)
            _ptr0IncrVal = ptr0IncrVal._zext(dist._dtype.bit_length())

            addPossible = (ptr0._eq(ptr1))._ternary(allow_eq,
                                                    dist >= _ptr0IncrVal)

        return addPossible, wouldCross0

    @hwt_expr_producer
    def _fifo_ptr_distance(self, ptr0: HBitsRtlSignal, ptr1: HBitsRtlSignal):
        """
        Computes distance from ptr0 to ptr1
        """
        w = ptr1._dtype.bit_length()
        diff = ptr1._zext(w + 1) - ptr0._zext(w + 1)
        DEPTH = self.DEPTH
        # ;note: (diff + DEPTH)._trunc(w) # works only for pow2 DEPTH
        wraps = ptr1 < ptr0;
        return wraps._ternary((diff + DEPTH), diff)

    def _should_use_distributed_locks(self, write_en_wait_incrVal: EnWaitIncrValTuple,
                      read_en_wait_incrVal_list: list[EnWaitIncrValTuple]) -> bool:
        """
        Use distibuted locks if the check for overflow needs to check incrVal
        because 
        """
        for en_wait_incrVal in chain((write_en_wait_incrVal,), read_en_wait_incrVal_list):
            if len(en_wait_incrVal) == 3:
                incrVal = en_wait_incrVal[2]
                if not isinstance(incrVal, int):
                    return True
                if self.DEPTH % incrVal != 0:
                    return True

        return False

    def fifo_pointers(self, write_en_wait_incrVal: EnWaitIncrValTuple,
                      read_en_wait_incrVal_list: list[EnWaitIncrValTuple])\
                      ->list[tuple[RtlSignal, RtlSignal]]:
        """
        Create fifo writer and reader pointers and enable/wait logic
        This functions supports multiple reader pointers

        :note: Multiple read pointers are useful when the data in fifo passes
        through multiple states, this efficiently means that instead of
        two FIFOs betwen some components we can use just 1 with multiple read poiners.
        For example 1st read pointer may represent if the data is beeing processed (lock)
        and the second if the data processing was finished and the item in fifo is deallocated (commit).

        :note: *_en are inputs, *_wait, are outputs
        :note: en=1 and wait=1 will result in nop and will not cause underflow/overflow
        :attention: writer pointer next logic check only last reader pointer

        :return: list, tule(en, ptr) for writer and each reader
        """

        assert len(read_en_wait_incrVal_list) > 0
        s = self.parent._sig
        r = self.parent._reg
        index_t = self.index_t
        DEPTH = self.DEPTH

        fifo_write = s("fifo_write")
        write_ptr = r("write_ptr", index_t, self.INIT_SIZE % self.DEPTH)
        ack_ptr_list = [(fifo_write, write_ptr), ]

        # Write ptr logic part 1 out of 2
        en, wait, write_incr = self._normalize_EnWaitIncrValTuple(write_en_wait_incrVal)
        write_en_wait = en, wait
        ptr = write_ptr
        IS_INITIALIZED_FULL = self.INIT_SIZE == DEPTH
        USE_DISTRIBUTED_LOCK = self._should_use_distributed_locks(write_en_wait_incrVal, read_en_wait_incrVal_list)
        if USE_DISTRIBUTED_LOCK:
            crossed0_w = r(f"crossed0_w", def_val=IS_INITIALIZED_FULL)
            crossed0 = crossed0_w
        # instantiate all read pointers
        for i, (read_en, read_wait, read_incr) in enumerate([self._normalize_EnWaitIncrValTuple(v)
                                                             for v in read_en_wait_incrVal_list]):
            read_ptr = r(f"read_ptr{i:d}", index_t, 0)
            fifo_read = s(f"fifo_read{i:d}")
            ack_ptr_list.append((fifo_read, read_ptr))
            # update reader (tail) pointer as needed

            # check if state where w_ptr == r_ptr is full or empty
            if USE_DISTRIBUTED_LOCK:
                crossed0_r = r(f"crossed0_r{i:d}", def_val=i == 0 and IS_INITIALIZED_FULL)
                ptrsAllowedToEqual = crossed0 != crossed0_r
            else:
                last_was_r = r(f"last_was_r{i:d}", def_val=i != 0 or not IS_INITIALIZED_FULL)
                ptrsAllowedToEqual = ~last_was_r

            read_possible, wouldCross0 = self._is_fifo_ptr_add_possible(read_ptr, ptr, ptrsAllowedToEqual, read_incr)
            if USE_DISTRIBUTED_LOCK:
                If(read_en & read_possible & wouldCross0,
                   crossed0_r(~crossed0_r)
                )
            else:
                If(read_en & read_possible,
                    # write stalled and comsumming item, potentially reaching
                    # w_ptr if write pointer not advancing enough
                    last_was_r(1)
                ).Elif(en & ~wait,
                    # not reading and write advancing ==>
                    last_was_r(0)
                )

            read_wait(~read_possible)
            fifo_read(read_en & read_possible)
            If(fifo_read,
               read_ptr(self._uadd_with_modulo(read_ptr, read_incr))
            )

            # previous reader is next port writer (producer) as it next reader can continue
            # only if previous reader did consume the item
            en, _ = read_en, read_wait
            ptr = read_ptr
            if USE_DISTRIBUTED_LOCK:
                crossed0 = crossed0_r

        # Write ptr logic part 2 out of 2
        write_en, write_wait = write_en_wait
        if USE_DISTRIBUTED_LOCK:
            ptrsAllowedToEqual = crossed0_w._eq(crossed0_r)
        else:
            ptrsAllowedToEqual = last_was_r

        write_possible, w_willCross0 = self._is_fifo_ptr_add_possible(
            write_ptr, read_ptr, ptrsAllowedToEqual, write_incr)
        if USE_DISTRIBUTED_LOCK:
            If(write_en & write_possible & w_willCross0,
               crossed0_w(~crossed0_w)
            )
        If(fifo_write,
           write_ptr(self._uadd_with_modulo(write_ptr, write_incr))
        )
        # Update Empty and Full flags
        write_wait(~write_possible)
        fifo_write(write_en & write_possible)

        return ack_ptr_list
