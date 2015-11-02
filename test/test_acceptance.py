import subprocess
import unittest

from mock import Mock, patch
from nose.tools import *

class TestForcedDater(object):

    def run_forced_dater(self, date, files):
        command = ["python", "forced_dater.py", date]
        if isinstance(files, (tuple, list)):
            command.extend(files)
        else:
            command.append(files)
        output = subprocess.check_output(command)

    def test_setting_dates(self):
        import os
        print os.getcwd()

        # Run with a properly formed date, but no files.
        date = "2011-08-03T13:00:00Z"
        output = self.run_forced_dater(date, [])
        assert_equals(output, None)