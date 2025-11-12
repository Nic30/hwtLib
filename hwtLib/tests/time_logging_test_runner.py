#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import unittest
from unittest.runner import TextTestResult
from hwt.pyUtils.typingFuture import override


class TimeLoggingTestResult(TextTestResult):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_timings = []

    @override
    def startTest(self, test):
        self._test_started_at = time.time()
        super().startTest(test)

    def _calladdResultMethodWithTimeLog(self, addResultMethod, *args):
        elapsed = time.time() - self._test_started_at
        name = self.getDescription(args[0])
        self.test_timings.append((name, elapsed))
        addResultMethod(*args)
        if self.showAll:
            self.stream.write("ok")
            self.stream.writeln(" {:.03}s".format(elapsed))
        elif self.dots:
            self.stream.write('.')
            self.stream.flush()

    @override
    def addSuccess(self, test):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addSuccess, test)

    @override
    def addError(self, test, err):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addError, test, err)

    @override
    def addFailure(self, test, err):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addFailure, test, err)

    @override
    def addSkip(self, test, reason):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addSkip, test, reason)

    @override
    def addExpectedFailure(self, test, err):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addExpectedFailure, test, err)

    @override
    def addUnexpectedSuccess(self, test):
        self._calladdResultMethodWithTimeLog(super(TextTestResult, self).addUnexpectedSuccess, test)

    def getTestTimings(self):
        return self.test_timings

    def printTop(self, n=None):
        timings = self.test_timings
        timings.sort(key=lambda x:-x[1])

        if n is not None and n < len(timings):
            timings = timings[:n]
        for name, elapsed in timings:
            print(f"{name}\t {elapsed:.03}s")


class TimeLoggingTestRunner(unittest.TextTestRunner):

    def __init__(self, *args, **kwargs):
        if kwargs.get("resultclass", None) is None:
            kwargs["resultclass"] = TimeLoggingTestResult
        if "verbosity" not in kwargs:
            kwargs["verbosity"] = 3
        return super(TimeLoggingTestRunner, self).__init__(
            *args,
            **kwargs
        )

