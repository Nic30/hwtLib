from hwt.hdlObjects.frameTemplate import FrameTemplate
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.pyUtils.arrayQuery import iter_with_last


class TemplateBasedUnit(Unit):
    """
    Class with functions for extracting metadata in frame template
    """
    def parseTemplate(self):
        if self._tmpl is None:
            self._tmpl = TransTmpl(self._structT)

        if self._frames is None:
            DW = int(self.DATA_WIDTH)
            frames = FrameTemplate.framesFromTransTmpl(self._tmpl,
                                                       DW)
            self._frames = list(frames)

    def chainFrameWords(self):
        offset = 0
        for f in self._frames:
            for last, (wi, w) in iter_with_last(f.walkWords(showPadding=True)):
                yield (offset + wi, w, last)
            offset += wi + 1
