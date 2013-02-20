#!/usr/bin/env python

"""
    hey_rexec.rexec
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    SKEL

    :copyright: (c) 2013 by oDesk Corporation.
    :license: BSD, see LICENSE for more details.
"""

import os
import warnings
import subprocess
import re
from collections import defaultdict

# yes, tempnam/tmpnam are insecure, but if someone has access to our
# machines we're doing analysis on, we're probably already in bigger trouble

warnings.filterwarnings("ignore", "tempnam", RuntimeWarning)
warnings.filterwarnings("ignore", "tmpnam", RuntimeWarning)

def _read_file_with_localizer(fn, localizer=None):
    s = ''
    
    if localizer is None:
        s = file(fn).read()
    else:
        s = localizer.read(fn)
        
    return s

class RExec(object):
    def __init__(self, cwd):
        self._results = []
        self._cur_r_str = ''
        self._cwd = cwd

    def append_string(self, s):
        self._cur_r_str = self._cur_r_str + "\n" + s + "\n"
        return self

    def append_file(self, fn, localizer=None):
        self.append_string(
            _read_file_with_localizer(fn, localizer)
            )

        return self

    def append_libraries(self, lib_list):
        self._cur_r_str = self._cur_r_str + "\n" + '\n'.join(
            ["library('%s')" % lib for lib in lib_list]) + "\n"
        return self

    def append_graphic(self, typ, name, r_str):
        if typ == 'png':
            self._cur_r_str += "\n" + """
png('r_%s.png')
%s
dev.off()
""" % (name, r_str)
        elif typ == 'svg':
            self._cur_r_str += "\n" + """
svg('r_%s.svg')
%s
dev.off()
""" % (name, r_str)
        else:
            raise NotImplementedError()
        
        return self

    def append_csv_read(self, fn, to_var):
        self._cur_r_str += "\n" + """
%s <- read.csv('%s')
""" % (to_var, fn)

        return self

    def append_sink(self, name, r_str):
        self._cur_r_str += "\n" + """
sink('r_%s.txt')
%s
sink()
""" % (name, r_str)
        
        return self

    def execute(self):
        tmp_r_fn = os.tempnam(self._cwd)
        tmp_r_file = file(tmp_r_fn, 'w')
        tmp_r_file.write(self._cur_r_str)
        tmp_r_file.close()

        end_of_r_fn = os.path.split(tmp_r_fn)[1]

        subprocess.call('R --vanilla --slave -f %s' % end_of_r_fn,
                        shell=True, cwd=self._cwd)

        r_type_name_tups = [(
                re.search(r'^r_(.+?)\.(.+?)$', fn).groups()[1],
                re.search(r'^r_(.+?)\.(.+?)$', fn).groups()[0]
                )
                            for fn in os.listdir(self._cwd)
                            if re.search(r'^r_(.+?)\.(.+?)$', fn)]
        
        r_outputs = defaultdict(dict)
        
        for file_type, name in r_type_name_tups:
            if file_type == 'txt':
                r_outputs[file_type][name] = \
                    file(os.path.join(self._cwd, 'r_%s.%s' % (name, file_type))).read()
            else:
                r_outputs[file_type][name] = \
                    os.path.join(self._cwd, 'r_%s.%s' % (name, file_type))
                
        self._results = r_outputs

        return self

    def results(self):
        return self._results

    def get_text(self, name):
        if self._results.has_key('txt') and self._results['txt'].has_key(name):
            return self._results['txt'][name]
        elif self._results.has_key('html') and self._results['html'].has_key(name):
            return self._results['html'][name]
        else:
            raise KeyError('No such text output %s.' % name)

    def get_graphic(self, name, path='relative'):
        if path not in ('abs', 'absolute', 'rel', 'relative'):
            raise RuntimeError('Path %s is not a valid path type.' % path)

        for img_type in ['png', 'svg']:
            if (self._results.has_key(img_type) and 
                self._results[img_type].has_key(name)):
                if path in ('abs', 'absolute'):
                    return self._results[img_type][name]
                elif path in ('rel', 'relative'):
                    return os.path.split(self._results[img_type][name])[1]

        raise RuntimeError('No such graphic with name %s.' % name)

