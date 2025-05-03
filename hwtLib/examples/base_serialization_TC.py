import os
import re

from hwt.hwModule import HwModule
from hwt.serializer.hwt import HwtSerializer
from hwt.serializer.systemC import SystemCSerializer
from hwt.serializer.verilog import VerilogSerializer
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.simulator.simTestCase import SimTestCase
from hwt.synth import to_rtl_str

rmWhitespaces = re.compile(r'\s+', re.MULTILINE)


class BaseSerializationTC(SimTestCase):
    # file should be set on child class because we want the pats in tests
    # to be relative to a current test case
    __FILE__ = None
    SERIALIZER_BY_EXT = {
        "v": VerilogSerializer,
        "vhd": Vhdl2008Serializer,
        "cpp": SystemCSerializer,
        "py": HwtSerializer,
    }

    def tearDown(self):
        self.rmSim()
        SimTestCase.tearDown(self)

    def strStructureCmp(self, cont, tmpl: str):
        if not isinstance(cont, str):
            cont = repr(cont)

        _tmpl = rmWhitespaces.sub(" ", tmpl).strip()
        _cont = rmWhitespaces.sub(" ", cont).strip()

        self.assertEqual(_tmpl, _cont)

    def assert_serializes_as_file(self, m: HwModule, file_name: str):
        ser = self.SERIALIZER_BY_EXT[file_name.split(".")[-1]]
        s = to_rtl_str(m, serializer_cls=ser)
        self.assert_same_as_file(s, file_name)

    def assert_same_as_file(self, s:str, file_name: str, printOnError=False):
        assert self.__FILE__ is not None, "This should be set on child class"
        THIS_DIR = os.path.dirname(os.path.realpath(self.__FILE__))
        fn = os.path.join(THIS_DIR, file_name)
        # print(s)
        # with open(fn, "w") as f:
        #     f.write(s)
        try:
            with open(fn) as f:
                ref_s = f.read()
        except FileNotFoundError as e:
            if printOnError:
                print(s)
            raise e
        # self.strStructureCmp(s, ref_s)
        try:
            self.strStructureCmp(s, ref_s)
        except:
            if printOnError:
                print(ref_s)
                print(s)
            raise
