"""
Module rotlog provides simple text logfiles that are rotated to keep the total
amount of logged data in check:
- A maximum file size defines how large the log may grow
- A number of historical versions defines how many rotated-away logs you
  keep.

Logged messages are expanded a-la printf() and sent to the log and to
stdout/stderr.

Synopsis / example:
  import rotlog

  # logs to stdout and to file
  rotlog.info('Start of run, number of threads is %d', 2+5)

  # logs to stderr and to file
  rotlog.warn('Cannot open file %s for reading', myfilename)

  # logs to stderr and to file, and aborts the program
  rotlog.fatal('Aborting)

  # Turns verbosity on and logs to file and stdout
  rotlog.verbose(True)
  rotlog.debug('Some debugging message')

  rotlog.verbose(False)
  rotlog.debug('This does not appear')

  # After this, info/warn/fatal/debug messages will include a program name
  rotlog.progname('myprog')

  # Example of exception formatting:
  try:
    ...
  except:
    rotlog.warn(rotlog.formatexception())
"""  

import os
import sys
import time
import traceback

_verbosity   = False
_logfname    = None
_logversions = None
_maxsize     = None
_logfile     = None
_progname    = None

def _stamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def _outputline(stdstream, line):
    # Output just one line, possibly rotate logs
    global _logfname
    global _logversions
    global _maxsize
    global _logfile

    stdstream.write(line)
    
    # Not logging to file? No need to output/rotate.
    if not _logfile:
        return
    
    _logfile.write(bytes(line, 'utf-8'))

    # Rotate logs if needed
    if not _maxsize or _maxsize < 1 or _logfile.tell() < _maxsize:
        return
    _logfile.close()

    for i in range(_logversions - 1, 0, -1):
        thislog = '%s-%d' % (_logfname, i)
        nextlog = '%s-%d' % (_logfname, i + 1)
        if os.path.exists(nextlog):
            os.unlink(nextlog)
        if os.path.exists(thislog):
            os.rename(thislog, nextlog)
    nextlog = '%s-%d' % (_logfname, 1)
    os.rename(_logfname, nextlog)

    _logfile = open(_logfname, 'ab')

def _output(stdstream, tag, fmt, *args):
    global _progname

    # Expand message string, split up by lines
    if args:
        msg = fmt % args
    else:
        msg = fmt
    for l in msg.split('\n'):
        if l == '':
            continue
        line = _stamp() + ' ' + tag
        if _progname:
            line += ' ' + _progname
        line += l + '\n'
        _outputline(stdstream, line)

def formatexception():
    """ Returns the current exception formatted with a stacktrace so
    it may be logged."""
    
    tp, vl, tb = sys.exc_info()
    return ''.join(traceback.format_exception(tp, vl, tb))

def logfile(filename, maxsize=100000, versions=10, progname=None):
    """ Sets the logfile parameters. The directory part of 'filename' is
    created if it does not yet exist. Historical logfiles (rotated-away)
    will get a suffix -1, -2 and so on up to 'versions'. Parameter 'maxsize'
    is the size that a log file may reach, after that it is rotated away.
    Setting 'progname' causes the label to be prepended to messages."""
    
    global _logfname
    global _maxsize
    global _logversions
    global _logfile
    global _progname

    _logfname    = filename
    _maxsize     = maxsize
    _logversions = versions
    _progname    = progname
    
    os.makedirs(os.path.dirname(_logfname), exist_ok=True)
    _logfile = open(_logfname, 'ab')

def progname(p):
    """ Defines the program name that is prepended to messages. Set to
    None to suppress. """
    
    global _progname
    _progname = p
    
def verbose(verbosity=True):
    """ Turns verbosity on or off. When verbosity is off, debug() does not
    log anything."""
    
    global _verbosity
    _verbosity = verbosity

def info(fmt, *args):
    """ Logs an informational message to the logfile and to stdout."""
    
    _output(sys.stdout, 'INFO ', fmt, *args)

def warn(fmt, *args):
    """ Logs a warning message to the logfile and to stderr."""
    _output(sys.stderr, 'WARN ', fmt, *args)

def fatal(fmt, *args):
    """ Logs a fatal message to the logfile and to stderr, and halts the
    program with an exit status of 1."""
    
    _output(sys.stderr, 'FATAL', fmt, *args)
    sys.exit(1)

def debug(fmt, *args):
    """ Logs an informational message to stdout and to the logfile if
    verbosity is turned on."""
    
    if _verbosity:
        _output(sys.stdout, 'DEBUG', fmt, *args)

if __name__ == '__main__':
    # some stdout logging

    verbose()
    debug('five plus %d = %d', 3, 5+3)
            
    logfile('/tmp/rotlog.log', maxsize=100)
    for i in range(1000):
        debug('message nr %d', i)

    # exception test
    a = 10
    b = 0
    try:
        print(a / b)
    except:
        warn(formatexception())
