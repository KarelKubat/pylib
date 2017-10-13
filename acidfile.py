"""
ACIDWriteFile provides a file-like interface for writing files with some
level of ACIDity. An ACIDWriteFile doesn't "exist" until it is closed:

  import acidfile

  with f as ACIDWriteFile('myfile'):
    f.write('something')
    # though 'myfile' doesn't exist here, it is hidden as
    # 'myfile-something-acid' during its scope
  # Now suddenly 'myfile' appears

ACIDReadFile provides something similar. Once it grabs a file, it renames
it to a temporary name so that other ACIDReadFile instances cannot grab it:

  with f as ACIDReadFile('myfile'):
    buf = f.read()
    # other = ACIDReadFile('myfile') will now cause an exception
  # Now 'myfile' appears back since it's no longer being used:
  other = ACIDReadFile('myfile')  # succeeds



import glob
import os
import os.path

class ACIDWriteFile:

  def __init__(self, filename):
    self._filename = filename
    self._tmpname  = '%s.%d.acid' % (filename, os.getpid())

    # Destructive write: remove output if it already exists
    if os.path.exists(filename):
      os.unlink(filename)

    # Open a tmp file for writing instead.
    self._outfile  = open(self._tmpname, 'wb')

  def outfile(self):
    return self._outfile

  def write(self, stuff):
    return self._outfile.write(stuff)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    # Close the tmpfile we've been writing to and atomically create
    # the user-requested output file.
    self._outfile.close()
    os.rename(self._tmpname, self._filename)

class ACIDReadFile:

  def __init__(self, filename):
    self._filename = filename
    self._tmpname  = '%s.%d.acid' % (filename, os.getpid())

    # Force exception when the source file does not exist
    if not os.path.exists(filename):
      open(filename, 'rb')

    # Rename source to tmp name and open that instead
    os.rename(filename, self._tmpname)
    self._infile = open(self._tmpname, 'rb')

  def infile(self):
    return self._outfile

  def read(self, nchars=None):
    if not nchars:
      return self._infile.read()
    return self._infile.read(nchars)

  def readline(self, nthline=None):
    if not nthline:
      return self._infile.readline()
    return self._infile.readline(nthline)

  def readlines(self):
    return self._infile.readlines()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    # Close the tmpfile we've been reading from and rename it back
    # to the original requested input file.
    self._infile.close()
    os.rename(self._tmpname, self._filename)

class ACIDDir:

  def __init__(self, directory):
    self._dir = directory

  def glob(self, mask='*'):
    files = glob.glob('%s/%s' % (self._dir, mask))
    i = 0
    while i < len(files):
      if files[i].endswith('acid'):
        files = files[:i] + files[i + 1:]
      else:
        i += 1
    return files

  def cleanup(self):
    for f in glob.glob('%s/%s' % (self._dir, '*')):
      if f.endswith('acid'):
        os.unlink(f)

if __name__ == '__main__':
  # Some unit tests.

  import unittest
  from subprocess import call

  class AFTest(unittest.TestCase):

    def testWriteFile(self):
      directory = '/tmp/AFTest/%d/writefiletest' % os.getpid()

      if not os.path.exists(directory):
        os.makedirs(directory)

      # Write some stuff into myfile1. It should not appear in the glob
      # list because it's written as myfile1-bla-acid.
      fname = '%s/myfile1' % directory
      with ACIDWriteFile(fname) as wf:
        wf.write('Hello World\n')
        self.assertFalse(fname in glob.glob('%s/*' % directory),
                         'not expecting %s in %s/*' % (fname, directory))
      self.assertTrue(fname in glob.glob('%s/*' % directory),
                      'expecting %s in %s/*' % (fname, directory))

      # Write some more stuff. When creating myfile2, myfile1 should still
      # be there.
      fname = '%s/myfile2' % directory
      with ACIDWriteFile(fname) as wf:
        wf.write('Hello World\n')
        self.assertFalse(fname in glob.glob('%s/*' % directory),
                         'not expecting %s in %s/*' % (fname, directory))
        self.assertTrue('%s/myfile1' % directory in
                          glob.glob('%s/*' % directory),
                        'expecting %s/myfile1 in %s/* when writing next file' %
                          (directory, directory))

        # ACIDDir should now only show myfile1
        ad = ACIDDir(directory)
        self.assertTrue('%s/myfile1' % directory in ad.glob(),
                        'expecting %s/myfile1 in ACIDDir(%s)' % (
                            directory, directory))
      self.assertTrue(fname in glob.glob('%s/*' % directory),
                      'expecting %s in %s/*' % (fname, directory))
      self.assertTrue('%s/myfile1' % directory in ad.glob(),
                      'expecting %s/myfile1 in ACIDDir(%s)' % (
                          directory, directory))
      self.assertTrue('%s/myfile2' % directory in ad.glob(),
                      'expecting %s/myfile2 in ACIDDir(%s)' % (
                          directory, directory))


  # Run the tests
  unittest.main()

  # Cleanup
  call(['rm', '-rf', '/tmp/AFTest'])
