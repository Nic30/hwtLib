#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

setup(name='hwtLib',
      version='2.2',
      description='library of hardware components and test for HWToolkit framework (hwt, FPGA devel. tools)',
      url='https://github.com/Nic30/hwtLib',
      author='Michal Orsak',
      author_email='michal.o.socials@gmail.com',
      install_requires=[
        'hwt>=2.2',
        'Pillow',  # there are some components which are working with images
      ],
      license='MIT',
      packages=find_packages(),
      package_data={'hwtLib': ['*.vhd', '*.v', '*.png']},
      include_package_data=True,
      zip_safe=False,
      test_suite='hwtLib.tests.all.suite',)
