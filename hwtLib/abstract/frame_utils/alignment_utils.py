from itertools import product
from math import inf
from typing import List, Tuple, Union, Optional

from hwt.hdl.types.stream import HStream
from hwtLib.abstract.frame_utils.byte_src_info import ByteSrcInfo


def freeze_frame(f: List[List[ByteSrcInfo]])\
        ->Tuple[Tuple[ByteSrcInfo, ...], ...]:
    return tuple(tuple(w) for w in f)


def count_not_none(items: List[Optional[ByteSrcInfo]]):
    for i, b in enumerate(items):
        if b is not None:
            return i
    return 0


def next_frame_offsets(f0_t: HStream, data_width: int):
    f0_B_width = f0_t.element_t.bit_length()

    f1_start_offsets = set()
    i, len_max = f0_t.len_min, f0_t.len_max
    while i <= len_max:
        offset = (i * f0_B_width) % data_width
        if offset in f1_start_offsets:
            break
        f1_start_offsets.add(offset)
        i += 1

    return sorted(f1_start_offsets)


class FrameAlignmentUtils():
    """
    :ivar ~.word_bytes: number of bytes in 1 output word
    """

    def __init__(self, word_bytes: int, out_offset=0):
        self.word_bytes = word_bytes
        self.out_offset = out_offset

    def join_streams(
            self, stream_data: Tuple[Tuple[Tuple[ByteSrcInfo, ...], ...], ...],
            offset):
        """
        Create output frame with specified offset from input stream

        :param stream_data: list of data for each stream input
            (stream data is list of data words,
            data word is a tuple of ByteSrcInfo)
        :param offset: offset of output stream
        """
        word_bytes = self.word_bytes
        assert offset >= 0 and offset < word_bytes, (offset, word_bytes)
        res = []
        # input data frames to byte list
        in_data_bytes = [None for _ in range(offset)]
        for frame in stream_data:
            for word in frame:
                in_data_bytes.extend(word)

        curr_word = None
        for i, d in enumerate(in_data_bytes):
            if i >= offset and d is None:
                # skip non start fill-up
                continue

            if curr_word is None or len(curr_word) == word_bytes:
                # start of new frame
                curr_word = [d, ]
                res.append(curr_word)
            else:
                curr_word.append(d)

        # final padding to ensure all words do have
        if curr_word is not None and len(curr_word) != word_bytes:
            curr_word.extend(None for _ in range(word_bytes - len(curr_word)))

        return freeze_frame(res)

    def create_frame(self, stream_i: int, byte_cnt: int,
                     offset_out: int, offset_in: int)\
            ->Tuple[Tuple[ByteSrcInfo]]:
        """
        :param byte_cnt: number of bytes in this frame
        :param offset_out: how many empty bytes should be put before data in frame
        :param offset_in: how many bytes skip from imput stream
        """
        assert byte_cnt >= 0, byte_cnt
        word_bytes = self.word_bytes
        assert offset_out >= 0 and offset_out < word_bytes, (offset_out, word_bytes)
        assert offset_in >= 0 and offset_in < word_bytes, (offset_in, word_bytes)

        frame = []
        if byte_cnt == 0:
            return freeze_frame(frame)

        if offset_out:
            frame.append([None for _ in range(offset_out)])
            last_in_word_i = 0
        else:
            last_in_word_i = -1

        last_word_i = ((offset_in + byte_cnt - 1) // word_bytes)
        for i in range(byte_cnt):
            in_B_i = i + offset_in
            in_byte_i = in_B_i % word_bytes
            in_word_i = in_B_i // word_bytes
            is_from_last_input_word = int(in_word_i == last_word_i)
            B_info = ByteSrcInfo(stream_i, in_word_i,
                                 in_byte_i, is_from_last_input_word)

            if in_word_i == last_in_word_i:
                frame[-1].append(B_info)
            else:
                assert last_in_word_i == in_word_i - 1, (last_in_word_i, in_word_i)
                last_in_word_i = in_word_i
                frame.append([B_info, ])

        last_data_word = frame[-1]
        for _ in range(word_bytes - len(last_data_word)):
            last_data_word.append(None)

        return freeze_frame(frame)

    def get_bytes_in_frame_info(self, offset_out, offset_in,
                                chunk_size, chunk_cnt, already_has_body_words):
        # assert chunk_cnt > 0, chunk_cnt
        assert chunk_size > 0, chunk_size
        word_bytes = self.word_bytes

        offset = max(offset_in, offset_out)
        first_word_bytes = min(word_bytes - offset, chunk_cnt * chunk_size)
        last_word_bytes = (offset + chunk_size * chunk_cnt) % word_bytes
        has_body_words = (offset + chunk_size * chunk_cnt) >= (2 * word_bytes)
        # if first_word_bytes + last_word_bytes == word_bytes and word_bytes % chunk_size == 0:
        #    # the output offset will be same after adding data from this frame
        #    has_body_words = False

        first_word_is_last_word = (offset + chunk_cnt * chunk_size) <= word_bytes

        min_representative_frame_size = first_word_bytes
        if has_body_words and (offset != 0 or not already_has_body_words):
            min_representative_frame_size += word_bytes
        if not first_word_is_last_word\
                and not (
                    has_body_words
                    and last_word_bytes == word_bytes
                ):
            min_representative_frame_size += last_word_bytes
        if first_word_bytes == word_bytes\
                and min_representative_frame_size > word_bytes:
            has_body_words = True
        return first_word_bytes, has_body_words, \
            last_word_bytes, min_representative_frame_size

    def get_important_byte_cnts(
            self, offset_out: int, offset_in: int, chunk_size: int,
            chunk_cnt_min: Union[int, float], chunk_cnt_max: Union[int, float]):
        """
        Filter chunk cnt range, let only those values
        which affect the number of valid bytes
        in first/last word of frame and presence of words in body frame
        """
        # assert chunk_cnt_min > 0
        assert chunk_cnt_min <= chunk_cnt_max, (chunk_cnt_min, chunk_cnt_max)
        if isinstance(chunk_cnt_min, int) and isinstance(chunk_cnt_max, int)\
                and chunk_cnt_min == chunk_cnt_max:
            _, _, _, min_representative_frame_size = self.get_bytes_in_frame_info(
                offset_out, offset_in, chunk_size, chunk_cnt_min, False)
            return [min_representative_frame_size, ]

        word_bytes = self.word_bytes
        _chunk_cnt_min = chunk_cnt_min % (2 * word_bytes)
        chunk_cnt_max = _chunk_cnt_min + \
            min((2 * word_bytes), chunk_cnt_max - chunk_cnt_min)
        chunk_cnt_min = _chunk_cnt_min
        sizes = set()
        already_has_body_words = False
        for chunk_cnt in range(chunk_cnt_min, chunk_cnt_max + 1):
            (_,
             has_body_words,
             _,
             min_representative_frame_size) = self.get_bytes_in_frame_info(
                offset_out, offset_in, chunk_size, chunk_cnt,
                already_has_body_words)
            sizes.add(min_representative_frame_size)
            already_has_body_words |= has_body_words

        return sorted(sizes)

    def stream_to_all_possible_frame_formats(
            self, t: HStream, stream_i: int, offset_out: int):
        """
        Generate all possible frame formats with unique features
        (related to masks, last and data mux)
        """
        frames = []
        chunk_size = t.element_t.bit_length() // 8
        for offset_in in t.start_offsets:
            for byte_cnt in self.get_important_byte_cnts(
                    offset_out, offset_in, chunk_size, t.len_min, t.len_max):
                frame = self.create_frame(
                    stream_i, byte_cnt, offset_out, offset_in)
                frames.append(frame)
        return frames

    def streams_to_all_possible_frame_formats(
            self, streams: List[HStream], offset: int):
        """
        :see: :func:`FrameJoinUtils.stream_to_all_possible_frame_formats`
            for multiple input streams
        """
        frames_per_stream = []
        prev_end_offsets = [offset, ]
        for i, t in enumerate(streams):
            assert isinstance(t, HStream), t

            f_frames = set()
            for offset_out in prev_end_offsets:
                f_frames_tmp = self.stream_to_all_possible_frame_formats(
                    t, i, offset_out)
                f_frames.update(f_frames_tmp)

            f_frames = list(f_frames)
            # pprint(f_frames)
            frames_per_stream.append(f_frames)
            _prev_end_offsets = prev_end_offsets
            prev_end_offsets = set()
            # for each frame resolve end alignment of the frames
            for frame in f_frames:
                if frame:
                    last_word = frame[-1]
                    o = count_not_none(last_word)
                else:
                    o = 0
                prev_end_offsets.add(o)

            prev_end_offsets = sorted(prev_end_offsets)

        res = set()
        for frame_combination in product(*frames_per_stream):
            res_frame = self.join_streams(frame_combination, offset)
            res.add(res_frame)

        res = list(res)
        return res

    def resolve_input_bytes_destinations(self, streams: List[HStream]):
        frames = self.streams_to_all_possible_frame_formats(
            streams, self.out_offset)
        input_B_dst = self._resolve_input_bytes_destinations(
            frames, len(streams))
        return input_B_dst

    @staticmethod
    def can_produce_zero_len_frame(streams: List[HStream]):
        return [s.len_min == 0 for s in streams]

    def _resolve_input_bytes_destinations(self, frames, input_cnt):
        """
        :param frames: list of all possible frame formats generated
            from streams_to_all_possible_frame_formats
        :param input_cnt: number of input streams
        """
        word_bytes = self.word_bytes

        def init_word():
            return [set() for _ in range(word_bytes)]

        input_B_dst = [init_word() for _ in range(input_cnt)]

        def add_dst(state_name, input_i, input_B_i, input_time_offset, output_B_i,
                    is_last_word_from_this_input):
            input_B_dst[input_i][input_B_i].add((
                state_name,
                input_time_offset,
                output_B_i,
                is_last_word_from_this_input))

        for f_i, f in enumerate(frames):
            for output_word_i, w in enumerate(f):
                state_label = (f_i, output_word_i)

                # resolve min_word_i_per_input_in_this_out_word
                min_word_i_per_input_in_this_out_word = [
                    inf for _ in range(input_cnt)
                ]
                for output_B_i, byte_info in enumerate(w):
                    if byte_info is None:
                        continue
                    i = byte_info.stream_i
                    min_word_i_per_input_in_this_out_word[i] = \
                        min(min_word_i_per_input_in_this_out_word[i],
                            byte_info.word_i)
                # resolve byte destinations
                for output_B_i, byte_info in enumerate(w):
                    if byte_info is None:
                        continue
                    input_i = byte_info.stream_i
                    input_B_i = byte_info.byte_i
                    time_offset = byte_info.word_i - \
                        min_word_i_per_input_in_this_out_word[input_i]
                    assert time_offset >= 0, time_offset
                    add_dst(state_label, input_i, input_B_i, time_offset,
                            output_B_i, byte_info.is_from_last_input_word)

        return input_B_dst
