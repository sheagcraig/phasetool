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


import copy
import datetime

from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import

import phasetool  # pylint: disable=import-error


class TestPhaseToolUnits(object):
    """Test the phasetool prepare units."""

    def __init__(self):
        self.test_plist = phasetool.plistlib.readPlist(
            "test/resources/Crypt-0.7.2.pkginfo")
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(
            self.test_date, "%Y-%m-%dT%H:%M:%SZ")

    def test_set_install_after_date(self):
        """Set a date."""
        target_plist = copy.deepcopy(self.test_plist)
        phasetool.set_force_install_after_date(
            self.test_datetime, target_plist)
        assert_equal(target_plist["force_install_after_date"],
                     self.test_datetime)

    def test_del_install_after_date(self):
        """Remove an install date key entirely."""
        target_plist = copy.deepcopy(self.test_plist)
        phasetool.set_force_install_after_date("", target_plist)
        assert_is_none(target_plist.get("force_install_after_date"))

    def test_set_unattended_install(self):
        """Test setting unattended."""
        target_plist = copy.deepcopy(self.test_plist)
        phasetool.set_unattended_install(False, target_plist)
        assert_equal(target_plist["unattended_install"], False)
