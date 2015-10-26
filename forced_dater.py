#!/usr/bin/env python

# License
"""Update a list of pkgsinfo files with a force_install_by_date value."""


import argparse
import datetime
import os
# pkgsinfo files should not be binary, so standard plistlib is fine.
import plistlib
import re
import sys


def main():
    parser = build_argparser()
    args = parser.parse_args()
    if (len(args.pkginfo) is 1 and
            not args.pkginfo[0].endswith((".plist", ".pkginfo"))):
        # File input
        with open(args.pkginfo[0]) as paths:
            paths_to_change = [
                os.path.expanduser(path.strip("\n\t\"'"))
                for path in paths.readlines() if not path.startswith("#")]
    else:
        paths_to_change = args.pkginfo

    if not is_valid_date(args.date):
        print "Invalid date! Please check formatting."
        sys.exit(1)

    set_force_install_by_date(args.date, paths_to_change)
    # remove_key(args.date, args.pkginfo)


def build_argparser():
    """Create our argument parser."""
    description = ("Set the force_install_by_date key and value for any "
                   "number of pkginfo files")
    parser = argparse.ArgumentParser(description=description)

    phelp = ("Date to use as the value for force_install_by_date. Format is: "
             "'yyyy-mm-ddThh:mm:ssZ'. For example, August 3rd 2011 at 1PM is "
             "the following: '2011-08-03T13:00:00Z'. OR, use a blank string "
             "(i.e. '') to remove the force_install_by_date key/value pair.")
    parser.add_argument("date", help=phelp)

    phelp = ("Any number of paths to pkginfo files to update, or a path to a "
             "file to use for input. Format should have one path per line, "
             "with comments allowed.")

    parser.add_argument("pkginfo", help=phelp, nargs="*")

    return parser


def is_valid_date(date):
    """Ensure date is in the correct format."""
    result = False
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
    match = True if re.match(pattern, date) else False
    if match:
        try:
            converted_date = datetime.datetime.strptime(
                date, "%Y-%m-%dT%H:%M:%SZ")
            result = True
        except ValueError as err:
            print err, err.message, type(err)
    elif not date:
        result = True
    return result


def set_force_install_by_date(date, pkgsinfo):
    """Set the force_install_by_date value for pkginfo files.

    Args:
        date: Date string in the Munki pkginfo format:
            'yyyy-mm-ddThh:mm:ssZ' or "" / None to remove.
            pkgsinfo: List of string paths to pkginfo files.
    """
    for pkginfo_path in pkgsinfo:
        if not pkginfo_path.startswith("#") and os.path.exists(pkginfo_path):
            pkginfo = plistlib.readPlist(pkginfo_path)
            if date:
                pkginfo["force_install_after_date"] = date
            elif pkginfo.get("force_install_after_date"):
                del pkginfo["force_install_after_date"]
            # TODO: This could be restricted to only when files are changed
            # TODO: Output when something is changed/ not changed.
            plistlib.writePlist(pkginfo, pkginfo_path)


def remove_key(key, pkgsinfo):
    """"""
    for pkginfo_path in pkgsinfo:
        if not pkginfo_path.startswith("#") and os.path.exists(pkginfo_path):
            pkginfo = plistlib.readPlist(pkginfo_path)
            if key in pkginfo:
                del pkginfo[key]
            # TODO: This could be restricted to only when files are changed
            # TODO: Output when something is changed/ not changed.
            plistlib.writePlist(pkginfo, pkginfo_path)

if __name__ == "__main__":
    main()