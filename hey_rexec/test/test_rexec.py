import unittest2

import string
import random
import os
import re
import warnings
import mock
import hey_dl
import hey_rexec

warnings.filterwarnings("ignore", "tempnam", RuntimeWarning)
warnings.filterwarnings("ignore", "tmpnam", RuntimeWarning)

class RExecTestCase(unittest2.TestCase):
    def setUp(self):
        self._dl = hey_dl.DirectoryLocalizer()
        self._dl.set()

        self._test_cwd = os.tempnam('/tmp')
        os.makedirs(self._test_cwd)

    def tearDown(self): pass

    def test_null_exec(self): 
        assert len(hey_rexec.RExec(self._test_cwd)
                   .append_string('')
                   .execute()
                   .results()) == 0

    def test_cat_to_tmp(self):
        tmpnm =  os.tempnam(self._test_cwd)

        (hey_rexec.RExec(self._test_cwd)
         .append_string('sink("%s") ; cat("foo") ; sink()' % tmpnm)
         .execute())

        assert os.path.exists(tmpnm)
        assert re.search(r'^\s*foo\s*$', file(tmpnm, 'r').read(), re.MULTILINE)
        
    def test_cat(self):
        assert re.search(
            r'^\s*foo\s*$',
            hey_rexec.RExec(self._test_cwd)
            .append_string('sink("r_test.txt") ; cat("foo") ; sink()')
            .execute()
            .results()['txt']['test'],
            re.MULTILINE)

    def test_get_text(self):
        assert re.search(
            r'^\s*foo\s*$',
            hey_rexec.RExec(self._test_cwd)
            .append_string('sink("r_test.txt") ; cat("foo") ; sink()')
            .execute()
            .get_text('test'),
            re.MULTILINE)

    def test_get_text_raises(self):
        with self.assertRaises(KeyError):
            (hey_rexec.RExec(self._test_cwd)
             .append_string('sink("r_test.txt") ; cat("foo") ; sink()')
             .execute()
             .get_text('other'))

    def test_append_file_dl(self):
        assert re.search(
            r'^\s*weird\s*$',
            hey_rexec.RExec(self._test_cwd)
            .append_file('txt/cat_txt.R', localizer=self._dl)
            .execute()
            .get_text('something'),
            re.MULTILINE)

    def test_append_file_abs(self):
        abs_fn = os.tempnam('/tmp')
        
        file(abs_fn,'w').write('sink("r_something2.txt"); cat("what"); sink()')

        assert re.search(
            r'^\s*what\s*$',
            hey_rexec.RExec(self._test_cwd)
            .append_file(abs_fn)
            .execute()
            .get_text('something2'),
            re.MULTILINE)

    def test_append_libraries_graphics(self):
        assert 'qhist' in (
            hey_rexec.RExec(self._test_cwd)
            .append_libraries(['ggplot2'])
            .append_graphic('png', 'qhist', 'qplot(runif(100))')
            .execute()
            .results()['png'])

    def test_get_graphic_rel(self):
        assert (hey_rexec.RExec(self._test_cwd)
                .append_libraries(['ggplot2'])
                .append_graphic('png', 'qhist2', 'qplot(runif(100))')
                .execute()
                .get_graphic('qhist2', path='relative')
                .endswith('png'))

    def test_get_graphic_abs(self):
        assert '/' in (hey_rexec.RExec(self._test_cwd)
                       .append_libraries(['ggplot2'])
                       .append_graphic('png', 'qhist3', 'qplot(runif(100))')
                       .execute()
                       .get_graphic('qhist3', path='abs'))

    def test_get_graphic_svg(self):
        assert '/' in (hey_rexec.RExec(self._test_cwd)
                       .append_libraries(['ggplot2'])
                       .append_graphic('svg', 'qhist4', 'qplot(runif(100))')
                       .execute()
                       .get_graphic('qhist4', path='abs'))

    def test_csv_sink(self):
        assert re.search(
            r'^\s*27\s*$',
            hey_rexec.RExec(self._test_cwd)
            .append_csv_read(self._dl.path('txt/points.csv'), 'points')
            .append_sink('sum', 'cat(sum(points$points))')
            .execute()
            .get_text('sum'))

