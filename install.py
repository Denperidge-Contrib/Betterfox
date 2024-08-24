from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from shutil import copytree, ignore_patterns
from datetime import datetime
from urllib.request import urlopen
from subprocess import check_output
import curses
from json import loads
from re import compile, IGNORECASE
from zipfile import ZipFile
from io import BytesIO
from argparse import ArgumentParser

# (?<=firefox release).*?mozilla.org/.*?/firefox/(?P<version>.*?)/
re_find_version = compile(r"mozilla.org/.*?/firefox/(?P<version>[\d.]*?)/", IGNORECASE)

"""


Limitations;
- Not every github release is loaded in, only the latest ones

"""

REPOSITORY_OWNER = "yokoffing"
REPOSITORY_NAME = "Betterfox"
FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute()  # TODO: Windows

selected_if_backup = None
selected_config = ""
userjs_path = None


def _get_firefox_version():
    ver_string = check_output(["firefox", "--version"], encoding="UTF-8")
    return ver_string[ver_string.rindex(" ")+1:].strip()


# STEP 0
def _get_default_profile_folder():
    config_path = FIREFOX_ROOT.joinpath("profiles.ini")
    
    print(f"Reading {config_path}...")

    config_parser = ConfigParser(strict=False)
    config_parser.read(config_path)

    for section in config_parser.sections():
        if "Default" in config_parser[section]:
            print("Default detected: " + section)
            return FIREFOX_ROOT.joinpath(config_parser[section]["Path"])


def _get_releases():
    releases = []
    raw_releases = loads(urlopen(f"https://api.github.com/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/releases").read())
    for raw_release in raw_releases:
        name = raw_release["name"] or raw_release["tag_name"]  # or fixes 126.0 not being lodaded
        body = raw_release["body"]


        # Find which firefox releases are supported. Manual overrides for ones that don't have it written in their thing!
        if name == "user.js v.122.1":
            supported = ["120.0", "120.0.1", "121.0", "121.0.1", "122.0", "122.0.1"]  # Assumed from previous release. TODO check with yokoffing
        elif name == "user.js 116.1":
            supported = ["116.0", "116.0.1", "116.0.2", "116.0.3"]  # Assumed from previous release. TODO check with yokoffing
        elif name == "Betterfox v.107":
            supported = ["107.0"]  # TODO, check with yokoffing
        elif "firefox release" in body.lower():
            trim_body = body.lower()[body.lower().index("firefox release"):]
            supported = re_find_version.findall(trim_body)
            if len(supported) == 0:
                print(f"Could not parse release in '{name}'. Please post this error message on https://github.com/{REPOSITORY_NAME}/{REPOSITORY_NAME}/issues")
                continue
        else:
            print(f"Could not find firefox release header '{name}'. Please post this error message on https://github.com/{REPOSITORY_NAME}/{REPOSITORY_NAME}/issues")
            continue

        releases.append({
            "name": name,
            "url": raw_release["zipball_url"],
            "supported": supported,
        })
    return releases

def _get_latest_compatible_release(releases):
    for release in releases:
        if firefox_version in release["supported"]:
            return release
    return None    
    

def backup_profile(src):
    dest = f"{src}-backup-{datetime.today().strftime('%Y-%m-%d-%H-%M-%S')}"
    
    copytree(src, dest, ignore=ignore_patterns("*lock"))
    print("Backed up profile to " + dest)


def download_betterfox(url):
    data = BytesIO()
    data.write(urlopen(url).read())
    return data  

def extract_betterfox(data, profile_folder):
    zipfile = ZipFile(data)
    userjs_zipinfo = None
    for file in zipfile.filelist:
        if file.filename.endswith("user.js"):
            userjs_zipinfo = file
            userjs_zipinfo.filename = Path(userjs_zipinfo.filename).name

    if not userjs_zipinfo:
        raise BaseException("Could not find user.js!")
    
    return zipfile.extract(userjs_zipinfo, profile_folder)


def list_releases(releases, only_supported=False, add_index=False):
    print()
    print(f"Listing {'compatible' if only_supported else 'all'} Betterfox releases:")
    print(f"Releases marked with '> ' are documented to be compatible with your Firefox version ({firefox_version})")
    print()

    i = 0
    for release in releases:
        supported = firefox_version in release["supported"]
        if not only_supported or (only_supported and supported):
            print(f"{f'[{i}]' if add_index else ''}{'> ' if supported else '  '}{release['name'].ljust(20)}\t\t\tSupported: {','.join(release['supported'])}")
        i+=1
    

if __name__ == "__main__":
    firefox_version = _get_firefox_version()
    releases = _get_releases()
    latest_compatible_release = _get_latest_compatible_release(releases)
    selected_release = None

    default_profile_folder = _get_default_profile_folder()
    argparser = ArgumentParser(

    )
    argparser.add_argument("--betterfox-version", "-bv", default=latest_compatible_release, help=f"Which version of Betterfox to install. Defaults to the latest compatible release for your installed Firefox version {latest_compatible_release['name'] if latest_compatible_release else f'(N/A. No compatible release found for Firefox version {firefox_version})'}")
    argparser.add_argument("--profile-dir", "-p", "-pd", default=default_profile_folder, help=f"Which profile dir to install user.js in. Defaults to {default_profile_folder}")
    argparser.add_argument("--no-backup", "-nb", action="store_true", default=False, help="disable backup of current profile (not recommended)"),
    
    listfuncs = argparser.add_mutually_exclusive_group()
    listfuncs.add_argument("--list", action="store_true", default=False, help=f"List all Betterfox releases compatible with your version of Firefox ({firefox_version})")
    listfuncs.add_argument("--list-all", action="store_true", default=False, help=f"List all Betterfox releases")
    listfuncs.add_argument("--interactive", "-i", action="store_true", default=False, help=f"Interactively select Betterfox version")

    args = argparser.parse_args()

    if args.list or args.list_all:
        list_releases(releases, args.list)
        exit()

    if not args.no_backup:
        backup_profile(args.profile_dir)



    if args.betterfox_version:
        # If not None AND not string, default value has been used
        if not isinstance(args.betterfox_version, str):
            selected_release = args.betterfox_version
            print(f"Using latest compatible Betterfox version ({selected_release['name']})...")
        # If string has been passed
        else:
            selected_release = next(rel for rel in releases if rel['name'] == args.betterfox_version)
            print(f"Using manually selected Betterfox version ({selected_release['name']})")
    
    if not args.betterfox_version:
        print("Could not find a compatible Betterfox version for your Firefox installation.")
        
        list_releases(releases, False, True)

        selection = int(input(f"Select Betterfox version, or press enter without typing a number to cancel [0-{len(releases) - 1}]: "))

        selected_release = releases[selection]

    



    userjs_path = extract_betterfox(
        download_betterfox(selected_release["url"]),
        args.profile_dir
    )
    print(f"Installed user.js to {userjs_path} !")
