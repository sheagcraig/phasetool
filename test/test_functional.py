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
        self.test_file = "test/resources/Crypt-0.7.2.pkginfo"
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(self.test_date,
                                                        "%Y-%m-%dT%H:%M:%SZ")

    @mock.patch("phasetool.plistlib.writePlist", autospec=True)
    def test_setting_dates(self, mock_write_plist):
        # First, Leif is a bit uneasy about dumping a big chunk of
        # pkginfos into this thing. So he tries just a date.
        args = [self.test_date]
        result = self.get_phasetool_results(args)
        assert_is_none(result)

        # Okay-let's try this for real. Leif is going to update an
        # actual file.
        args = [self.test_date, self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])

        # Leif is feeling good, so he tries a bunch of files.
        args = [self.test_date] + 2 * [self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])
        assert_equal(self.test_datetime, result[1]["force_install_after_date"])
        assert_false(result[1]["unattended_install"])

        # Leif decides typing all of those filenames in is no fun, and
        # decides to try passing a filename that contains pkginfo paths.
        mock_files = [self.test_file]
        mock_file_list = mock.patch("phasetool.get_pkginfo_from_file",
                                    return_value=mock_files)
        mock_file_list.start()
        args = [self.test_date, "file list"]
        result = self.get_phasetool_results(args)
        mock_file_list.stop()

        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])

    @mock.patch("phasetool.plistlib.writePlist", autospec=True)
    def test_removing_date(self, mock_write_plist):
        """Leif wants to remove the force_install_after_date from a
        pkginfo.
        """
        args = ["", self.test_file]
        result = self.get_phasetool_results(args)

        assert_is_none(result[0].get("force_install_after_date"))

    @mock.patch("phasetool.plistlib.writePlist", autospec=True)
    def get_phasetool_results(self, args, mock_write_plist):
        """Put args into sys.argv and run phasetool.

        Args:
            args (list of strings): Positional args, flags, commands,
                supplied as commandline arguments to phasetool.

        Returns:
            Takes mock.MagicMock object's call_args_list for mocked
            plistlib.writePlist and returns a list of just the plist
            files that were "written".
        """
        sys.argv = ["phasetool.py"] + args
        phasetool.main()
        result = ([call[0][0] for call in mock_write_plist.call_args_list] if
                  mock_write_plist.called else None)
        return result
