#!/usr/bin/env python
# Copyright (C) 2015 Shea G Craig <shea.craig@sas.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Functional tests for phasetool.

Since it seems to be a thing to name the user for your user story, we
will name our user Leif.
"""


import datetime
import os
import plistlib
import subprocess
import sys

import mock
from nose.tools import *

import phasetool


class TestPhaseTool():
    """Leif tries to automate his Munki and AutoPkg phase testing."""

    def __init__(self):
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(self.test_date,
                                                        "%Y-%m-%dT%H:%M:%SZ")

    @mock.patch("phasetool.plistlib.writePlist", autospec=True)
    def test_setting_dates(self, mock_write_plist):
        # First, Leif is a bit uneasy about dumping a big chunk of
        # pkginfos into this thing. So he tries just a date.
        output = self.run_phasetool(self.test_date, [])
        assert_equals(output, None)

        # Okay-let's try this for real. Leif is going to update an
        # actual file.
        sys.argv = ["phasetool.py", self.test_date,
                    "test/resources/Crypt-0.7.2.pkginfo"]
        phasetool.main()

        assert_equal(self.test_datetime,
                     mock_plistlib.call_args[0][0]["force_install_after_date"])
        assert_false(mock_plistlib.call_args[0][0]["unattended_install"])

        # Leif is feeling good, so he tries a bunch of files.
        sys.argv = ["phasetool.py", self.test_date]
        sys.argv.extend(2 * [ "test/resources/Crypt-0.7.2.pkginfo"])
        phasetool.main()

        assert_equal(
            self.test_datetime,
            mock_write_plist.call_args_list[1][0][0][
                "force_install_after_date"])
        assert_false(
            mock_write_plist.call_args_list[1][0][0]["unattended_install"])
        assert_equal(
            self.test_datetime,
            mock_write_plist.call_args_list[2][0][0][
                "force_install_after_date"])
        assert_false(
            mock_write_plist.call_args_list[2][0][0]["unattended_install"])

        # Leif decides typing all of those filenames in is no fun, and
        # decides to try passing a filename that contains pkginfo paths.
        mock_files = ["test/resources/Crypt-0.7.2.pkginfo"]
        mock_file_list = mock.patch("phasetool.get_pkginfo_from_file",
                                    return_value=mock_files)
        mock_file_list.start()
        sys.argv = ["phasetool.py", self.test_date, "file list"]
        phasetool.main()
        mock_file_list.stop()

        assert_equal(
            self.test_datetime,
            mock_write_plist.call_args_list[3][0][0][
                "force_install_after_date"])
        assert_false(
            mock_plistlib.call_args_list[3][0][0]["unattended_install"])

    def run_phasetool(self, date, files):
        command = ["python", "phasetool.py", date]
        if isinstance(files, (tuple, list)):
            command.extend(files)
        else:
            command.append(files)
        output = subprocess.check_output(command)