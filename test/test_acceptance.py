"""Acceptance tests for forced_dater. Since it seems to be a thing to
name the user for your user story, we will name our user Leif.
"""


import datetime
import os
import plistlib
import subprocess
import sys
import unittest

import mock
from nose.tools import *

import forced_dater

class TestForcedDater():
    """Leif tries to automate his Munki and AutoPkg phase testing."""

    def __init__(self):
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(self.test_date,
                                                        "%Y-%m-%dT%H:%M:%SZ")

    @mock.patch("forced_dater.plistlib.writePlist", autospec=True)
    def test_setting_dates(self, mock_plistlib):
        # First, Leif is a bit uneasy about dumping a big chunk of
        # pkginfos into this thing. So he tries just a date.
        output = self.run_forced_dater(self.test_date, [])
        assert_equals(output, None)

        # Okay-let's try this for real. Leif is going to update an
        # actual file.
        sys.argv = ["forced_dater.py", self.test_date,
                    "test/resources/Crypt-0.7.2.pkginfo"]
        forced_dater.main()

        assert_equal(self.test_datetime,
                     mock_plistlib.call_args[0][0]["force_install_after_date"])

        # Leif is feeling good, so he tries a bunch of files.
        sys.argv = ["forced_dater.py", self.test_date]
        sys.argv.extend(2 * [ "test/resources/Crypt-0.7.2.pkginfo"])
        forced_dater.main()

        assert_equal(
            self.test_datetime,
            mock_plistlib.call_args_list[1][0][0]["force_install_after_date"])
        assert_equal(
            self.test_datetime,
            mock_plistlib.call_args_list[2][0][0]["force_install_after_date"])

        # Leif decides typing all of those filenames in is no fun, and
        # decides to try passing a filename that contains pkginfo paths.
        mock_files = ["test/resources/Crypt-0.7.2.pkginfo"]
        mock_file_list = mock.patch("forced_dater.get_pkginfo_from_file",
                                    return_value=mock_files)
        mock_file_list.start()
        sys.argv = ["forced_dater.py", self.test_date, "file list"]
        forced_dater.main()
        mock_file_list.stop()

        assert_equal(
            self.test_datetime,
            mock_plistlib.call_args_list[3][0][0]["force_install_after_date"])

    def run_forced_dater(self, date, files):
        command = ["python", "forced_dater.py", date]
        if isinstance(files, (tuple, list)):
            command.extend(files)
        else:
            command.append(files)
        output = subprocess.check_output(command)