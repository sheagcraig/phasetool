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
import plistlib
import subprocess
import sys
from xml.parsers.expat import ExpatError

try:
    import mount_shares_better
except ImportError:
    mount_shares_better = None


# TODO: Get this from Munki preferences.
PKGINFO_EXTENSIONS = (".pkginfo", ".plist")
# TODO (Shea): this should be a preference.
TESTING_CATALOGS = {"development", "testing", "phase1", "phase2", "phase3"}


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
    parser.add_argument("-u", "--repo_url", help="Full mount URL to Munki "
                        "repo. Will attempt to mount if the share is missing.")

    subparser = parser.add_subparsers(help="Sub-command help")

    # Collect arguments
    phelp = ("Collect available updates and generate markdown listing. "
             "Product names that begin with 'Placeholder' (case-insensitive) "
             "will be ignored.")
    collect_parser = subparser.add_parser("collect", help=phelp)
    collect_parser.set_defaults(func=collect)
    phelp = "Path to save output files."
    collect_parser.add_argument("output_path", help=phelp)

    # Prepare arguments
    phelp = ("Set the force_install_after_date and unattended_install value "
             "for any number of pkginfo files to be phase tested.")
    prepare_parser = subparser.add_parser("prepare", help=phelp)
    phelp = (
        "Date to use as the value for force_install_after_date. Format is: "
        "'yyyy-mm-ddThh:mm:ssZ'. For example, August 3rd 2011 at 1PM is the "
        "following: '2011-08-03T13:00:00Z'. OR, use a blank string (i.e. '') "
        "to remove the force_install_after_date key/value pair.")
    prepare_parser.add_argument("date", help=phelp)
    phelp = "Catalog to set on pkginfo files."
    prepare_parser.add_argument("phase", help=phelp)
    phelp = ("Any number of paths to pkginfo files to update, or a path to a "
             "file to use for input. Format should have one path per line, "
             "with comments allowed.")
    prepare_parser.add_argument("pkginfo", help=phelp, nargs="*")
    prepare_parser.set_defaults(func=prepare)

    # release subcommand
    phelp = ("Set the force_install_after_date and unattended_install for any "
             "number of pkginfo files to be released to production.")
    release_parser = subparser.add_parser("release", help=phelp)
    phelp = (
        "Date to use as the value for force_install_after_date. Format is: "
        "'yyyy-mm-ddThh:mm:ssZ'. For example, August 3rd 2011 at 1PM is the "
        "following: '2011-08-03T13:00:00Z'. OR, use a blank string (i.e. '') "
        "to remove the force_install_after_date key/value pair.")
    release_parser.add_argument("date", help=phelp)
    phelp = ("Any number of paths to pkginfo files to update, or a path to a "
             "file to use for input. Format should have one path per line, "
             "with comments allowed.")
    release_parser.add_argument("pkginfo", help=phelp, nargs="*")
    release_parser.set_defaults(func=release)

    # bulk subcommand
    phelp = "Set a top-level key on any number of pkginfo files."
    bulk_parser = subparser.add_parser("bulk", help=phelp)
    phelp = "Key to set."
    bulk_parser.add_argument("key", help=phelp)
    phelp = "Value to set on key, or '-' (literal hyphen) to remove the key."
    bulk_parser.add_argument("val", help=phelp)
    phelp = ("Any number of paths to pkginfo files to update, or a path to a "
             "file to use for input. Format should have one path per line, "
             "with comments allowed.")
    bulk_parser.add_argument("pkginfo", help=phelp, nargs="*")
    bulk_parser.set_defaults(func=bulk)

    return parser


def get_munki_repo(args):
    """Use cli arg for repo, otherwise, get from munkiimport prefs."""
    prefs = read_plist(
        "~/Library/Preferences/com.googlecode.munki.munkiimport.plist")
    repo = args.repo if args.repo else prefs.get("repo_path")
    repo_url = args.repo_url if args.repo_url else prefs.get("repo_url")

    if not is_mounted(repo):
        repo = mount(repo_url)

    return repo


def read_plist(path):
    """Read the plist at path."""
    return plistlib.readPlist(os.path.expanduser(path))


def is_mounted(path):
    """Return whether path is attached to the current filesystem."""
    return os.path.exists(path)


def mount(path):
    """Mount the share specified by path."""
    mount_location = None
    if not is_mounted(path):
        if hasattr(mount_shares_better, "mount_share"):
            try:
                mount_location = mount_shares_better.mount_share(path)
            except mount_shares_better.MountException as error:
                print error.message
        else:
            if os.uname() == "Darwin":
                mount_base = "/Volumes"
            else:
                mount_base = "/mnt"
            mount_point = os.path.join(mount_base, os.path.basename(path))
            args = ["mount_afp", path, mount_point]
            try:
                subprocess.check_call(args)
            except subprocess.CalledProcessError as error:
                raise PhasetoolError(
                    "Unable to mount {} at {} with error '{}'.".format(
                        path, mount_point, error.meesage))
            mount_location = mount_point

    return mount_location


def collect(args):
    """Collect available updates."""
    pkginfos = get_testing_pkginfos(args.repo)
    output_path = os.path.expanduser(args.output_path)
    prefix = os.path.join(output_path,
                          datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))

    write_markdown(pkginfos, "{}-phase_testing.md".format(prefix))
    write_path_list(pkginfos, "{}-phase_testing_files.txt".format(prefix))


def get_testing_pkginfos(repo):
    """Return all pkginfo files with testing catalogs."""
    pkginfos = {}
    pkginfo_dir = os.path.join(repo, "pkgsinfo")
    for dirpath, _, filenames in os.walk(pkginfo_dir):
        for pfile in [fname for fname in filenames if is_pkginfo(fname)]:
            try:
                path = os.path.join(dirpath, pfile)
                pkginfo_file = read_plist(path)
            except ExpatError:
                continue

            if (is_testing(pkginfo_file) and
                    not is_placeholder(pkginfo_file.get("name"))):
                pkginfos[path] = pkginfo_file

    return pkginfos


def is_testing(pkginfo):
    """Return whether a pkginfo file specifies any testing catalogs."""
    catalogs = pkginfo.get("catalogs")
    return any(catalog in TESTING_CATALOGS for catalog in catalogs)


def is_placeholder(record_name):
    """Return whether a name is considered a placeholder."""
    return record_name.upper().startswith("PLACEHOLDER")


def is_pkginfo(candidate):
    """Return whether a filename is a pkginfo by extension."""
    return os.path.splitext(candidate)[-1].lower() in PKGINFO_EXTENSIONS


def write_markdown(data, path):
    """Write markdown data string to path."""
    # TODO: Add template stuff.
    month = datetime.datetime.now().strftime("%B")
    output = [u"## {} Phase Testing Updates\n".format(month)]
    for _, item_val in sorted(data.items()):
        output.append(u"- {} {}".format(
            item_val.get("display_name") or item_val.get("name"),
            item_val["version"]))
    output_string = u"\n".join(output).encode("utf-8")
    write_file(output_string, path)


def write_path_list(data, path):
    """Write pkginfo path data to path."""
    output_string = u"\n".join(sorted(data.keys())).encode("utf-8")
    write_file(output_string, path)


def write_file(output_string, path):
    """Write output_string to path."""
    with open(path, "w") as markdown_file:
        markdown_file.write(output_string)


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
            pkginfo = read_plist(path)
            set_force_install_after_date(date, pkginfo)
            set_unattended_install(False, pkginfo)
            set_catalog(args.phase, pkginfo)
            plistlib.writePlist(pkginfo, path)


def release(args):
    """Set keys relevent to production deployment."""
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
            pkginfo = read_plist(path)
            set_force_install_after_date(date, pkginfo)
            set_unattended_install(True, pkginfo)
            set_catalog("production", pkginfo)
            plistlib.writePlist(pkginfo, path)


def bulk(args):
    """Set a key on multiple pkginfo files."""
    if (len(args.pkginfo) is 1 and
            not args.pkginfo[0].endswith((".plist", ".pkginfo"))):
        # File input
        paths_to_change = get_pkginfo_from_file(args.pkginfo[0])
    else:
        paths_to_change = args.pkginfo

    for path in paths_to_change:
        if os.path.exists(path):
            pkginfo = read_plist(path)
            if args.val == "-":
                remove_key(args.key, pkginfo)
            else:
                set_key(args.key, args.val, pkginfo)
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
    except ValueError:
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


def set_catalog(val, pkginfo):
    """Set the catalog value to val, clearing other entries.

    Args:
        val (string): Catalog to set.
        pkginfo (plist): File to on which to change date.
    """
    catalogs = []
    if val:
        catalogs.append(val)
    set_key("catalogs", [val], pkginfo)


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
