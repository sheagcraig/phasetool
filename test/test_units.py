import copy
import datetime

from nose.tools import *

import phasetool


class TestPhaseToolUnits(object):
    """"""

    def __init__(self):
        self.test_plist = phasetool.plistlib.readPlist(
            "test/resources/Crypt-0.7.2.pkginfo")
        self.test_date = "2011-08-03T13:00:00Z"
        self.test_datetime = datetime.datetime.strptime(self.test_date,
                                                        "%Y-%m-%dT%H:%M:%SZ")

    def test_set_force_install_after_date(self):
        target_plist = copy.deepcopy(self.test_plist)
        phasetool.set_force_install_after_date(self.test_date, target_plist)
        assert_equals(target_plist["force_install_after_date"],
                      self.test_datetime)
