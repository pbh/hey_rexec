#!/usr/bin/env python

"""
    hey_rexec.rexec
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility for executing an R file in its own directory.

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
    """
    A chaining R executing object.

    RExec lets you run R code and get the results from Python.  For the
    most part, the interface is pretty hacky.  The goal is to make it
    easy to automate the usage of existing R files, rather than make
    elegant programs integrating R and Python.  (For the latter, you
    might consider rpy or rpy2.)

    An RExec object takes a directory where it will be run.  You can then
    add R code to the object in a variety of ways (append_string,
    append_file and so on).  When you are done appending to the RExec
    object, you can use the execute() method which will run an R slave
    process on all of the R that you have appended so far (concatenated
    together.  Finally, you can get access to results of your R script
    in a relatively unorthodox way.  Any files output with an "r_" prefix
    will be available by calling get_text() or get_graphic() as appropriate.

    RExec has a chaining interface.  This means you can do things like:

      r_ex =(RExec(some_dir)
              .append_file("some.R")
              .append_file("other.R")
              .execute())
      r_ex.get_graphic('foo.svg', path='absolute')
    """

    def __init__(self, cwd):
        self._results = []
        self._cur_r_str = ''
        self._cwd = cwd

    def append_string(self, s):
        'Append a string to the R that will be executed.'
        self._cur_r_str = self._cur_r_str + "\n" + s + "\n"
        return self

    def append_file(self, fn, localizer=None):
        'Append the contents of a file to the R that will be executed.'
        self.append_string(
            _read_file_with_localizer(fn, localizer)
            )

        return self

    def append_libraries(self, lib_list):
        'Append a list of library() calls to the R that will be executed.'
        self._cur_r_str = self._cur_r_str + "\n" + '\n'.join(
            ["library('%s')" % lib for lib in lib_list]) + "\n"
        return self

    def append_graphic(self, typ, name, r_str):
        'Append creation of a graphic to the R that will be executed.'
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
        'Append a read of a CSV file to the R that will be executed.'
        self._cur_r_str += "\n" + """
%s <- read.csv('%s')
""" % (to_var, fn)

        return self

    def append_sink(self, name, r_str):
        'Append a sink() to the R that will be executed.'
        self._cur_r_str += "\n" + """
sink('r_%s.txt')
%s
sink()
""" % (name, r_str)
        
        return self

    def execute(self):
        'Execute the accumulated R code that has been appended to the object.'
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
        'Get textual content/path that was output to an r_{something}.{txt|html} file.'
        if self._results.has_key('txt') and self._results['txt'].has_key(name):
            return self._results['txt'][name]
        elif self._results.has_key('html') and self._results['html'].has_key(name):
            return self._results['html'][name]
        else:
            raise KeyError('No such text output %s.' % name)

    def get_graphic(self, name, path='relative'):
        'Get path for graphic output as an r_{something}.{png|svg} file.'
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

