"""
RotLog is intended for per-run logging of informational, debugging, warning
or fatal messages. Per instantiation of a RotLog object, previous files are
rotated to a historical version and a new log is opened.

Synopsis:
  import RotLog
  rl = RotLog(basedir='/var/log/mydir',   # dir for logs, default current dir
              basename='out.log',         # filename, default 'rotlog.log'
              versions=10,                # historical logs to keep, def. 10
              verbose=False)              # will rl.debug() output, def. not

  # Set verbosity on
  rl.verbose(True)

  # Debug message, shown if verbose is set to True. Also goes to stdout.
  rl.debug('Hello %s', 'world')

  # Informational, also goes to stdout.
  rl.info('Hello %s', 'world')

  # Warning, also goes to stderr
  rl.warn('Hello %s', 'world')

  # Fatal, also exits the program
  rl.fatal('Hello %s', 'world')

  print('not reached')
"""
import os
import os.path
import time
import sys

class RotLog:

  def __init__(self, basedir='.', basename='rotlog.log',
               versions=10, verbose=False):
    """Initializes the rotating logger.

    Parameters:
      basedir: directory where logs are created, default is '.'
      basename: name of logs, default 'rotlog.log'
      versions: number of historical versions to keep, default 10
      verbose: should debug() output? Default is False.

    The historical versions are 'rotated' to historical versions as follows
    (<file> stands for 'basedir/basename'):
      The previous <file>   is renamed to <file>-1
      The previous <file>-1 is renamed to <file>-2
      The previous <file>-2 is renamed to <file>-3
      ... and so on, until 'versions'
    The logging of the current instance then continues to <file>.
    """

    # Create base directory if not done yet
    if not os.path.exists(basedir):
      os.makedirs(basedir)

    # Here's where we will log to
    self._logname = '%s/%s' % (basedir, basename)

    # Rotate to previous versions if required.
    for i in range(9, 0, -1):
      thisfile = '%s-%d' % (self._logname, i)
      prevfile = '%s-%d' % (self._logname, i + 1)
      if os.path.exists(thisfile):
        if os.path.exists(prevfile):
          os.unlink(prevfile)
        os.rename(thisfile, prevfile)
    if os.path.exists(self._logname):
      os.rename(self._logname, '%s-1' % self._logname)

    # Open for writing.
    self._logfile = open(self._logname, 'w')

    # Initial verbosity
    self._verbose = verbose

  def verbose(self, verbosity):
    """ Sets verbosity to the level of the parameter (True or False).
    When False, method debug() doesn't output anything."""

    self._verbose = verbosity

  def _output(self, stdoutfile, tag, msg):
    outputstr = tag + ' ' + msg + '\n'
    stdoutfile.write(outputstr)
    self._logfile.write(time.strftime('%Y-%m-%d %H:%M:%s') + ' ' + outputstr)

  def debug(self, fmt, *args):
    """Outputs to stdout and logs if verbosity is on. The lines are preceded
    by 'DEBUG'."""
    if self._verbose:
      self._output(sys.stdout, 'DEBUG', fmt % args)

  def info(self, fmt, *args):
    """Outputs to stdout and logs. The lines are preceded with 'INFO'."""
    self._output(sys.stdout, 'INFO', fmt %args)

  def warn(self, fmt, *args):
    """Outputs to stderr and logs. The lines are preceded with 'WARN'."""
    self._output(sys.stderr, 'WARN', fmt % args)

  def fatal(self, fmt, *args):
    """Outputs to stderr and logs. The lines are preceded with 'ERROR'.
    Then the program is terminated with exit status 1."""
    self._output(sys.stderr, 'FATAL', fmt % args)
    sys.exit(1)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self._logfile.close()


if __name__ == '__main__':
  # A few unit tests.

  import unittest
  from subprocess import call

  class RLTest(unittest.TestCase):
    def testrotation(self):
      # Unique directory (we hope)
      uniquedir = '/tmp/rotlog/' + str(os.getpid())
      for i in range(20):
        infostring  = 'INFO run=%d' % i
        debugstring = 'DEBUG run=%d' % i
        warnstring  = 'WARN run=%d' % i
        with RotLog(basedir=uniquedir, basename='rl.log') as rl:
          rl.info('run=%d', i)
          rl.warn('run=%d', i)
          if i % 2 == 0:
            rl.verbose(True)
          rl.debug('run=%d', i)
        with open(uniquedir + '/rl.log') as inf:
          infofound = False
          debugfound = False
          warnfound = False
          for line in inf:
            if infostring in line:
              infofound = True
            if warnstring in line:
              warnfound = True
            if debugstring in line:
              debugfound = True
        self.assertTrue(infofound,
                        'expecting ' + infostring + ' in ' +
                        uniquedir + '/rl.log')
        self.assertTrue(warnfound,
                        'expecting ' + warnstring + ' in ' +
                        uniquedir + '/rl.log')
        if i % 2 == 0:
          self.assertTrue(debugfound,
                          'expecting ' + debugstring + ' in ' +
                          uniquedir + '/rl.log')
        else:
          self.assertFalse(debugfound,
                           'not expecting ' + debugstring + ' in ' +
                           uniquedir + '/rl.log')
      # clean up
      call(['rm', '-rf', '/tmp/rotlog'])

  unittest.main()
