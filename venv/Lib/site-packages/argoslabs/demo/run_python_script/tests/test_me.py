#!/usr/bin/env python
# coding=utf8
"""
ARGOS LABS plugin module : unittest
"""

################################################################################
import os
import sys
import unittest
from alabs.common.util.vvargs import ArgsError
from unittest import TestCase
# noinspection PyProtectedMember
from argoslabs.demo.run_python_script import _main as main
from argoslabs.demo.run_python_script import get_kwargs

import pathlib

CURRENT_PATH = pathlib.Path(pathlib.Path(__file__).resolve()).parent

SAMPLE_SCRIPT_1 = str(CURRENT_PATH / pathlib.Path('sample_script_1.py'))
SAMPLE_SCRIPT_2 = str(CURRENT_PATH / pathlib.Path('sample_script_2.py'))
SAMPLE_SCRIPT_10 = str(CURRENT_PATH / pathlib.Path('sample_script_10.py'))
SAMPLE_SCRIPT_11 = str(CURRENT_PATH / pathlib.Path('sample_script_11_error.py'))


################################################################################
class TU(TestCase):
    """
    TestCase for argoslabs.demo.helloworld
    """
    # ==========================================================================
    isFirst = True

    # ==========================================================================
    def test0000_init(self):
        self.assertTrue(True)

    # =========================================================================
    def test0010_get_kwargs(self):
        # 정상동작 케이스
        k = ('abc=1', 'cde=2', 'efg==3', 'ghi=')
        expect = dict(abc='1', cde='2', efg='=3', ghi='')
        result = get_kwargs(k)
        self.assertDictEqual(result, expect)

    # =========================================================================
    def test0011_get_kwargs(self):
        # 에러 케이스
        with self.assertRaises(ValueError):
            k = ('abc', 'cde=2')
            get_kwargs(k)

    # ==========================================================================
    def test0012_get_kwargs(self):
        with self.assertRaises(ValueError):
            k = ('=1', 'cde=2')
            print(get_kwargs(k))

    # ==========================================================================
    def test0010_main_input_case(self):
        outfile = 'stdout.txt'
        expect = "('1', '2', '3')"
        try:
            r = main('--python_file', SAMPLE_SCRIPT_1, '-a1', '-a2', '-a3',
                     '--outfile', outfile)
            self.assertTrue(r == 0)
            with open(outfile, encoding='utf-8') as ifp:
                rs = ifp.read()
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

        self.assertEqual(rs, expect)

    # ==========================================================================
    def test0011_main_input_case_error(self):
        # 스크립트에서 요구한 파라메터 개수가 맞지 않을때 에러
        outfile = 'stderr.txt'
        try:
            r = main('--python_file', SAMPLE_SCRIPT_1, '-a1', '-a2',
                     '--errfile', outfile)
            self.assertEqual(r, 1)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

    # =========================================================================
    def test0012_main_input_case_error(self):
        # 키워드 파라메터가 정의되어 있지 않은 상태에서 사용
        outfile = 'stderr.txt'
        try:
            # with self.assertRaises(TypeError):
            r = main('--python_file', SAMPLE_SCRIPT_1, '-a1', '-a2', '-a3', '-k abc=4',
                     '--errfile', outfile)
            self.assertEqual(r, 1)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

    # =========================================================================
    def test0013_main_input_case(self):
        # 키워드 사용, 같은 이름의 변수가 있으면 해당 변수에 대입
        outfile = 'stdout.txt'
        try:
            r = main('--python_file', SAMPLE_SCRIPT_2, '-a1', '-a2', '-k abc=4', '-k c=3',
                     '--outfile', outfile)
            self.assertEqual(r, 0)
            with open(outfile, encoding='utf-8') as ifp:
                rs = ifp.read()
                print(rs)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

    # =========================================================================
    def test0020_run_script(self):
        # 키워드 사용, 같은 이름의 변수가 있으면 해당 변수에 대입
        outfile = 'stdout.txt'
        try:
            r = main('--python_file', SAMPLE_SCRIPT_10, '-a1', '-a2', '-a3', '--outfile', outfile)
            self.assertEqual(r, 0)
            with open(outfile, encoding='utf-8') as ifp:
                rs = ifp.read()
                print(rs)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

    # =========================================================================
    def test0030_detail_error(self):
        # 키워드 사용, 같은 이름의 변수가 있으면 해당 변수에 대입
        outfile = 'stderr.txt'
        try:
            r = main('--python_file', SAMPLE_SCRIPT_11, '-a1', '-a2', '-a3', '--detail-error', '--outfile', outfile)
            self.assertEqual(r, 1)
            with open(outfile, encoding='utf-8') as ifp:
                rs = ifp.read()
                print(rs)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

    # =========================================================================
    def test0031_detail_error(self):
        # 키워드 사용, 같은 이름의 변수가 있으면 해당 변수에 대입
        outfile = 'stderr.txt'
        try:
            r = main('--python_file', SAMPLE_SCRIPT_11, '-a1', '-a2', '-a3', '--outfile', outfile)
            self.assertEqual(r, 1)
            with open(outfile, encoding='utf-8') as ifp:
                rs = ifp.read()
                print(rs)
        finally:
            if os.path.exists(outfile):
                os.remove(outfile)

if __name__ == '__main__':
    unittest.main()
