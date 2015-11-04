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


"""Automate Phase Testing With Munki

Updates a list of pkgsinfo files with a force_install_after_date value
and unattended_install value of False.
"""


import argparse
import datetime
import os
import sys

import plistlib


def main():
    """Build and parse args, and then kick-off action function."""
    parser = build_argparser()
    args = parser.parse_args()
    args.repo = get_munki_repo(args)
    args.func(args)


def build_argparser():
    """Create our argument parser."""
    description = ("Set the force_install_after_date key and value for any "
                   "number of pkginfo files")
    parser = argparse.ArgumentParser(description=description)

    # Global arguments
    parser.add_argument("-r", "--repo", help="Path to Munki repo. Will use "
                        "munkiimport's configured repo if not specified.")

    subparser = parser.add_subparsers(help="Sub-command help")

    # Collect arguments
    phelp = "Collect available updates and generate markdown listing."
    collect_parser = subparser.add_parser("collect", help=phelp)
    collect_parser.set_defaults(func=collect)

    # Set Pkginfo arguments
    phelp = ("Set the force_install_after_date key and value for any number "
             "of pkginfo files")
    pkginfo_parser = subparser.add_parser("prepare", help=phelp)
    phelp = (
        "Date to use as the value for force_install_after_date. Format is: "
        "'yyyy-mm-ddThh:mm:ssZ'. For example, August 3rd 2011 at 1PM is the "
        "following: '2011-08-03T13:00:00Z'. OR, use a blank string (i.e. '') "
        "to remove the force_install_after_date key/value pair.")
    pkginfo_parser.add_argument("date", help=phelp)
    phelp = ("Any number of paths to pkginfo files to update, or a path to a "
             "file to use for input. Format should have one path per line, "
             "with comments allowed.")
    pkginfo_parser.add_argument("pkginfo", help=phelp, nargs="*")
    pkginfo_parser.set_defaults(func=prepare)

    return parser


def get_munki_repo(args):
    """Use cli arg for repo, otherwise, get from munkiimport prefs."""
    if args.repo:
        return args.repo
    else:
        prefs = plistlib.readPlist(os.path.expanduser(
            "~/Library/Preferences/com.googlecode.munki.munkiimport.plist"))
        return prefs.get("repo_path")


def collect(args):
    """Collect available updates into markdown for presentation."""
    pass


def write_collection_results(markdown_data, path):
    """Write markdown data string to path."""
    with open(path, "w") as markdown_file:
        markdown_file.write(path)


def prepare(args):
    """Set keys relevent to phase deployment."""
    if (len(args.pkginfo) is 1 and
            not args.pkginfo[0].endswith((".plist", ".pkginfo"))):
        # File input
        paths_to_change = get_pkginfo_from_file(args.pkginfo[0])
    else:
        paths_to_change = args.pkginfo

    if not args.date:
        date = None
    elif not is_valid_date(args.date):
        print "Invalid date! Please check formatting."
        sys.exit(1)
    else:
        date = get_datetime(args.date)

    for path in paths_to_change:
        if os.path.exists(path):
            pkginfo = plistlib.readPlist(path)
            set_force_install_after_date(date, pkginfo)
            set_unattended_install(False, pkginfo)
            plistlib.writePlist(pkginfo, path)


def get_pkginfo_from_file(path):
    """Convert file contents into a list of paths, ignoring comments."""
    with open(path) as paths:
        paths_to_change = [
            os.path.expanduser(path.strip("\n\t\"'"))
            for path in paths.readlines() if not path.startswith("#")]
    return paths_to_change


def get_datetime(date):
    """Return a datetime object for correctly formatted string date."""
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")


def is_valid_date(date):
    """Ensure date is in the correct format.

    Format is: 'yyyy-mm-ddThh:mm:ssZ'. For example, August 3rd 2011 at
        1PM is: '2011-08-03T13:00:00Z'.

    date (string): Date string to validate.

    Returns:
        Boolean.
    """
    result = False
    try:
        _ = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        result = True
    except ValueError as err:
        pass
    return result


def set_force_install_after_date(date, pkginfo):
    """Set the force_install_after_date value for pkginfo file.

    Args:
        date (datetime.datetime): Date to force install after.
        pkginfo (plist): File to on which to change date.
    """
    if date:
        pkginfo["force_install_after_date"] = date
    elif pkginfo.get("force_install_after_date"):
        del pkginfo["force_install_after_date"]


def set_unattended_install(val, pkginfo):
    """Set the unattended_install value for pkginfo file.

    Args:
        val (bool): Value to set.
        pkginfo (plist): File to on which to change date.
    """
    set_key("unattended_install", val, pkginfo)


def set_key(key, val, pkginfo):
    """Set pkginfo's key to val.

    Args:
        key (string): The key name.
        val (string, bool, datetime, int, list, dict): Value to set.
            List and dict values may include any combination of other
            valid types from this list.
        pkginfo (plist): The pkginfo plist object to change.
    """
    pkginfo[key] = val


def remove_key(key, pkginfo):
    """Remove a key/value pair from a pkginfo file.

    Args:
        key (string): Key to remove.
        pkginfo (plist): The pkginfo plist object to change.
    """
    if key in pkginfo:
        del pkginfo[key]
    # TODO: This could be restricted to only when files are changed
    # TODO: Output when something is changed/ not changed.


if __name__ == "__main__":
    main()
