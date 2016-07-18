import unittest
from hdl_toolkit.parser.compileOrderResolver import  resolveComplileOrder
from hdl_toolkit.parser.loader import ParserFileInfo
from python_toolkit.arrayQuery import single

SAMPLES_DIR = '../samples/vhdlCodesign/vhdl/'
package1 = SAMPLES_DIR + 'packWithComps/package1.vhd'
top1 = SAMPLES_DIR + 'packWithComps/top1.vhd'

def p(fn, lib):
    pi = ParserFileInfo(fn, lib)
    pi.hierarchyOnly = True
    return pi

class HierarchyExtractorTC(unittest.TestCase):
    def testDependentOnPackage(self):
        fis = [p(package1, "work"), p(top1, "work")]
        co = resolveComplileOrder(fis, fis[1])
        expected = fis

        self.assertSequenceEqual(co, expected)

    def testDependetOnPackageFromDiferentLib(self):
        
        top1 = SAMPLES_DIR + 'multiLib/top1.vhd'
        pack = [p(package1, 'packWithComps')]
        work = [p(top1, 'work')]
        
        co = resolveComplileOrder(work + pack, work[0])


        expected = pack + work
        self.assertSequenceEqual(co, expected)
        
        
    
    def test_tripleNestedPackage(self):
        _files = ["abody.vhd", "a.vhd", "bbody.vhd", "b.vhd", "cbody.vhd", "c.vhd"]
        files = [p(SAMPLES_DIR + "tripleNestedPackage/" + f, "work") for f in _files ]
        
        compileOrder = resolveComplileOrder(files, files[1])
        
        def f(name):
            return single(files, lambda x: x.fileName.endswith(name + ".vhd"))
        expected = [f("c"), f("cbody"), f("b"), f("bbody"), f("a"), f("abody")]
        self.assertSequenceEqual(compileOrder, expected)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(HierarchyExtractorTC('test_tripleNestedPackage'))
    suite.addTest(unittest.makeSuite(HierarchyExtractorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
