import datetime
import os
import plistlib
import subprocess
import sys
import unittest

import mock
from nose.tools import *

sys.path.insert(0, os.path.abspath(".."))
import forced_dater

class TestForcedDater(object):

    def run_forced_dater(self, date, files):
        command = ["python", "forced_dater.py", date]
        if isinstance(files, (tuple, list)):
            command.extend(files)
        else:
            command.append(files)
        output = subprocess.check_output(command)

    @mock.patch("forced_dater.plistlib.writePlist")
    def test_setting_dates(self, mock_plistlib):
        # Run with a properly formed date, but no files.
        test_date = "2011-08-03T13:00:00Z"
        test_datetime = datetime.datetime.strptime(test_date,
                                                   "%Y-%m-%dT%H:%M:%SZ")
        output = self.run_forced_dater(test_date, [])
        assert_equals(output, None)
        # import pdb;pdb.set_trace()

        # Okay-let's try this for real. Update an actual file.
        sys.argv = ["forced_dater.py", test_date,
                    "test/resources/Crypt-0.7.2.pkginfo"]
        forced_dater.main()
        assert_equal(test_datetime,
                     mock_plistlib.call_args[0][0]["force_install_after_date"])



def fakeWritePlist(data_object, path):
    pass