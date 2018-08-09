import errno
import os
from os.path import join
from tempfile import TemporaryDirectory
import unittest

from hwt.pyUtils.fileHelpers import find_files


class FileUtilsTC(unittest.TestCase):
    def mkFile(self, d, fileName):
        fileName = join(d, fileName)
        if not os.path.exists(os.path.dirname(fileName)):
            try:
                os.makedirs(os.path.dirname(fileName))
            except OSError as exc:
                # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        open(fileName, 'w').close()
        return fileName

    def assertFound(self, directory, pattern, fileNames, recursive=True):
        f = set(find_files(directory, pattern, recursive=recursive))
        self.assertEqual(f, set(fileNames))

    def test_basic(self):
        with TemporaryDirectory() as d:
            self.assertFound(d, "*", {})

            a = self.mkFile(d, "a.a")
            self.assertFound(d, "*", {a})
            self.assertFound(d, "*.a", {a})
            self.assertFound(d, "*.*", {a})
            self.assertFound(d, "a.*", {a})
            self.assertFound(d, "b.*", {})
            self.assertFound(d, "*.b", {})
            self.assertFound(d, "", {})

            a2 = self.mkFile(d, "a2.a")
            self.assertFound(d, "*", {a, a2})
            self.assertFound(d, "*.a", {a, a2})
            self.assertFound(d, "*.*", {a, a2})
            self.assertFound(d, "a.*", {a})

            a3 = self.mkFile(d, join("a", "b", "c", "d.a"))
            self.assertFound(d, "*", {a, a2, a3})
            self.assertFound(d, "*.a", {a, a2, a3})
            self.assertFound(d, "*.*", {a, a2, a3})
            self.assertFound(d, "a.*", {a})
            self.assertFound(d, "*", {a, a2}, recursive=False)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameTmplTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(FileUtilsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
