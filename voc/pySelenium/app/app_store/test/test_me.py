import os
import sys
from unittest import TestCase
from voc.pySelenium.app.app_store.get_app_store_review import main


class TU(TestCase):
    """
    TestCase AppStore
    """

    # ==========================================================================
    def test0010_app_vadal_mijok(self):
        r = main('378084485',
                 r'C:\work\voc\app\appstore\26_앱스토어-배달의민족_20220128-094646',
                 r'C:\work\voc\pySelenium\app\app_store\app_store.yaml')

    # # ==========================================================================
    # def test0020_stop_datetime(self):
    #     r = main('378084485', r'C:\work\voc\app\appstore\26_앱스토어-배달의민족_20220128-094646', '배달',
    #              '2022/01/01 00:00:00')
    #
    # # ==========================================================================
    # def test0030_add_num_comments(self):
    #     r = main('378084485', r'C:\work\voc\app\appstore\26_요기요_20220214-191710', '배달',
    #              '2022/01/01 00:00:00')

    # ==========================================================================
    def test0040_test_input(self):
        r = main('378084485', r'C:\work\voc\app\appstore\26_배달의민족_20220215-193145', '2022/02/10 00:00:00')
