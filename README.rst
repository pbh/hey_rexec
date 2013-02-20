hey_rexec
======
RExec is a simple interface for running R in bulk on .R files.
It is not intended to be a replacement for rpy or rpy2.
If you're the kind of person who does some analysis in R and just wants
to mechanize running it (rather than a closer integration with Python),
this library might be for you.

__doc__
-------
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
