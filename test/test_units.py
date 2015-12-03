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


"""Unit tests for phasetool."""


import datetime
import os

import mock
from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import

import phasetool  # pylint: disable=import-error


class MockArgs(object):
    """Fake argparser namespace.

    It's easier to fake a namespace by just using attributes.
    """

    def __init__(self, repo, repo_url):
        self.repo = repo
        self.repo_url = repo_url


class TestGlobalUnits(object):
    """Test the phasetool helper units."""

    def test_get_munki_repo_from_args(self):
        """Test locating the munki repo."""
        mock_args = MockArgs("/tmp", "AFP")
        result = phasetool.get_munki_repo(mock_args)
        assert_equal("/tmp", result)

    @mock.patch("phasetool.read_plist")
    def test_get_munki_repo_without_args(self, mock_prefs):
        mock_prefs.return_value = {"repo_path": "/tmp", "repo_url": "AFP"}
        mock_args = MockArgs(False, False)
        result = phasetool.get_munki_repo(mock_args)
        assert_equal("/tmp", result)

    @mock.patch("phasetool.mount")
    def test_get_munki_repo_if_not_mounted(self, mock_mount):
        path = "/nonexistent/path"
        mock_mount.return_value = path
        mock_args = MockArgs(path, "AFP")
        result = phasetool.get_munki_repo(mock_args)
        assert_equal(path, result)
        mock_mount.assert_any_call("AFP")

    def test_is_valid_date(self):
        test_date = "2011-08-03T13:00:00Z"
        invalid_test_dates = ("Both how I'm livin' and my nose are large.",
                              "2011-08-0313:00:00", "February 15th, 2015",
                              "101015")
        assert_true(phasetool.is_valid_date(test_date))
        for invalid_date in invalid_test_dates:
            assert_false(phasetool.is_valid_date(invalid_date))


class TestPrepareUnits(object):
    """Test the phasetool prepare units."""

    def setUp(self):
        self.test_plist = phasetool.plistlib.readPlist(
            "test/resources/repo/pkgsinfo/Crypt-0.7.2.pkginfo")
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(
            self.test_date, "%Y-%m-%dT%H:%M:%SZ")

    def test_set_install_after_date(self):
        """Set a date."""
        phasetool.set_force_install_after_date(
            self.test_datetime, self.test_plist)
        assert_equal(self.test_plist["force_install_after_date"],
                     self.test_datetime)

    def test_del_install_after_date(self):
        """Remove an install date key entirely."""
        phasetool.set_force_install_after_date("", self.test_plist)
        assert_is_none(self.test_plist.get("force_install_after_date"))

    def test_set_unattended_install(self):
        """Test setting unattended."""
        phasetool.set_unattended_install(False, self.test_plist)
        assert_equal(self.test_plist["unattended_install"], False)

    def test_set_catalog(self):
        """Test setting catalog to a single value."""
        phasetool.set_catalog("production", self.test_plist)
        assert_list_equal(self.test_plist["catalogs"], ["production"])


class TestCollectUnits(object):
    """Test the collection units."""

    def test_get_testing_pkginfos(self):
        repo = "test/resources/repo"
        pkginfos = sorted(phasetool.get_testing_pkginfos(repo).keys())
        # This excludes the production and placeholder pkginfos.
        expected_filenames = ["Crypt-0.8.0.pkginfo", "Crypt-0.9.0.pkginfo",
                              "Crypt-1.0.0.pkginfo", "Crypt-1.5.0.pkginfo"]
        expected = sorted(
            [os.path.join("test/resources/repo/pkgsinfo", filename) for
             filename in expected_filenames])
        assert_list_equal(expected, pkginfos)

    def test_is_testing(self):
        catalogs = ("testing", "phase1", "development")
        for catalog in catalogs:
            assert(phasetool.is_testing({"catalogs": [catalog]}))
        assert_false(phasetool.is_testing({"catalogs": ["production"]}))

    def test_is_placeholder(self):
        placeholders = ("Placeholder-1.2.3.pkginfo", "placeholder.plist",
                        "PLACEHOLDER.plist")
        not_placeholders = ("NotPlaceholder-1.2.3.pkginfo", "Donkey.plist")
        for pkginfo in placeholders:
            assert(phasetool.is_placeholder(pkginfo))
        for pkginfo in not_placeholders:
            assert_false(phasetool.is_placeholder(pkginfo))


    # def test_get_catalogs(self):
    #     catalogs = phasetool.get_catalogs("test/resources/repo", "None")
    #     catalog_names = set(catalogs.keys())
    #     # This assumes we want to include ALL updates in phase testing
    #     # except those in production.
    #     assert_not_in("production", catalog_names)
    #     assert_set_equal({"testing", "phase1", "phase2", "phase3"},
    #                      catalog_names)


class TestMDOutput(object):

    def setUp(self):
        self.pkginfos = {"/test/1.pkginfo": {"name": "fancy",
                                             "display_name": "Wicked Fancy",
                                             "version": "0.0.1"},
                         "/test/2.pkginfo": {"name": "a fancy",
                                             "version": "0.0.2"},
                         "/test/4.pkginfo": {"display_name": "z fancy",
                                             "version": "0.0.3"},
                         "/test/3.pkginfo": {"name": u"\U0001F49A",
                                             "version": "0.0.3"}}
        self.test_output_path = "/test/phase_testing.md"
        self.expected_result = ("## November Phase Testing Updates\n\n"
                           "- Wicked Fancy 0.0.1\n"
                           "- a fancy 0.0.2\n"
                           u"- \U0001F49A 0.0.3\n"
                           "- z fancy 0.0.3").encode("utf-8")

    @mock.patch("phasetool.write_file", )
    def test_write_path_list(self, mock_write_file):
        phasetool.write_markdown(self.pkginfos, self.test_output_path)
        assert_equal(self.expected_result, mock_write_file.call_args[0][0])
        assert_equal(self.test_output_path, mock_write_file.call_args[0][1])


class TestPathOutput(object):

    def setUp(self):
        self.test_path = "/test/path"
        self.test_output_path = "/test/phase_testing_files.txt"

    def run_write_file_list(self):
        test_data = {self.test_path: None}
        phasetool.write_path_list(test_data, self.test_output_path)

    @mock.patch("phasetool.write_file", )
    def test_write_path_list(self, mock_write_file):
        self.run_write_file_list()
        assert_equal(self.test_path, mock_write_file.call_args[0][0])
        assert_equal(self.test_output_path, mock_write_file.call_args[0][1])

    @mock.patch("phasetool.write_file", )
    def test_write_unicode_path_list(self, mock_write_file):
        self.test_path += u"\U0001F49A\n"
        self.run_write_file_list()
        expected = self.test_path.encode("utf-8")
        assert_equal(expected, mock_write_file.call_args[0][0])

