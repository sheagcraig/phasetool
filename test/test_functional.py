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
import sys

import mock
from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import

import phasetool  # pylint: disable=import-error


class TestPhaseTool(object):
    """Leif tries to automate his Munki and AutoPkg phase testing."""

    def __init__(self):
        self.test_file = "test/resources/repo/pkgsinfo/Crypt-0.7.2.pkginfo"
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(self.test_date,
                                                        "%Y-%m-%dT%H:%M:%SZ")

    def test_prepare_setting_dates(self):
        """Test setting deployment info on pkginfo files."""
        # First, Leif is a bit uneasy about dumping a big chunk of
        # pkginfos into this thing. So he tries just a date.
        args = ["prepare", self.test_date, "phase1"]
        result = self.get_phasetool_results(args)
        assert_is_none(result)

        # Okay-let's try this for real. Leif is going to update an
        # actual file.
        args = ["prepare", self.test_date, "phase1", self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["phase1"])

        # Leif is feeling good, so he tries a bunch of files.
        args = ["prepare", self.test_date, "phase1"] + 2 * [self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["phase1"])
        assert_equal(self.test_datetime, result[1]["force_install_after_date"])
        assert_false(result[1]["unattended_install"])
        assert_list_equal(result[1]["catalogs"], ["phase1"])

        # Leif decides typing all of those filenames in is no fun, and
        # decides to try passing a filename that contains pkginfo paths.
        mock_files = [self.test_file]
        mock_file_list = mock.patch("phasetool.get_pkginfo_from_file",
                                    return_value=mock_files)
        mock_file_list.start()
        args = ["prepare", self.test_date, "phase1", "file list"]
        result = self.get_phasetool_results(args)
        mock_file_list.stop()

        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_false(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["phase1"])

    def test_prepare_removing_date(self):
        """Leif wants to remove the force_install_after_date from a
        pkginfo.
        """
        args = ["prepare", "", "phase1", self.test_file]
        result = self.get_phasetool_results(args)

        assert_is_none(result[0].get("force_install_after_date"))

    def test_release_setting_dates(self):
        """Test setting deployment info on pkginfo files."""
        # First, Leif is a bit uneasy about dumping a big chunk of
        # pkginfos into this thing. So he tries just a date.
        args = ["release", self.test_date]
        result = self.get_phasetool_results(args)
        assert_is_none(result)

        # Okay-let's try this for real. Leif is going to update an
        # actual file.
        args = ["release", self.test_date, self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_true(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["production"])

        # Leif is feeling good, so he tries a bunch of files.
        args = ["release", self.test_date] + 2 * [self.test_file]
        result = self.get_phasetool_results(args)
        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_true(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["production"])
        assert_equal(self.test_datetime, result[1]["force_install_after_date"])
        assert_true(result[1]["unattended_install"])
        assert_true(result[1]["unattended_install"])
        assert_list_equal(result[1]["catalogs"], ["production"])

        # Leif decides typing all of those filenames in is no fun, and
        # decides to try passing a filename that contains pkginfo paths.
        mock_files = [self.test_file]
        mock_file_list = mock.patch("phasetool.get_pkginfo_from_file",
                                    return_value=mock_files)
        mock_file_list.start()
        args = ["release", self.test_date, "file list"]
        result = self.get_phasetool_results(args)
        mock_file_list.stop()

        assert_equal(self.test_datetime, result[0]["force_install_after_date"])
        assert_true(result[0]["unattended_install"])
        assert_list_equal(result[0]["catalogs"], ["production"])

    @mock.patch("phasetool.write_file", autospec=True)
    def test_collect_updates(self, mock_repo):
        """Test collecting updates from a repo for phase testing."""
        expected_result = ("## November Phase Testing Updates\n\n"
                           "- Crypt - enables FileVault encryption 0.8.0\n"
                           "- Crypt - enables FileVault encryption 0.9.0\n"
                           "- Crypt - enables FileVault encryption 1.0.0\n"
                           "- Crypt - enables FileVault encryption 1.5.0")
        expected_files = ("test/resources/repo/pkgsinfo/Crypt-0.8.0.pkginfo\n"
                          "test/resources/repo/pkgsinfo/Crypt-0.9.0.pkginfo\n"
                          "test/resources/repo/pkgsinfo/Crypt-1.0.0.pkginfo\n"
                          "test/resources/repo/pkgsinfo/Crypt-1.5.0.pkginfo")
        # Leif is testing the collection of updates to see what it
        # finds
        sys.argv = build_args(["--repo", "test/resources/repo", "collect"])
        phasetool.main()
        result_content = mock_repo.call_args_list[0][0][0]
        result_files = mock_repo.call_args_list[1][0][0]
        assert_equal(expected_result, result_content)
        assert_equal(expected_files, result_files)

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
        sys.argv = build_args(args)
        phasetool.main()
        result = ([call[0][0] for call in mock_write_plist.call_args_list] if
                  mock_write_plist.called else None)
        return result


def build_args(args):
    """Build arguments to add to sys.argv.

    Args:
        args (list of strings): Command line arguments to run
            phasetool with.
    Returns:
        List of strings with script name properly prepended.
    """
    return ["phasetool.py"] + args
