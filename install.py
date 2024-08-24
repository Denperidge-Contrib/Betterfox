from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from shutil import copytree, ignore_patterns
from datetime import datetime
from urllib.request import urlopen
from subprocess import check_output
import curses
from json import loads
from re import compile, IGNORECASE

# (?<=firefox release).*?mozilla.org/.*?/firefox/(?P<version>.*?)/
re_find_version = compile(r"mozilla.org/.*?/firefox/(?P<version>[\d.]*?)/", IGNORECASE)

"""


Limitations;
- Not every github release is loaded in, only the latest ones

"""

REPOSITORY_OWNER = "yokoffing"
REPOSITORY_NAME = "Betterfox"
FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute()  # TODO: Windows
SCROLL_SIZE = 5

scroll_pos = 0

selected_if_backup = None
selected_config = ""


def _get_firefox_version():
    ver_string = check_output(["firefox", "--version"], encoding="UTF-8")
    return ver_string[ver_string.rindex(" ")+1:].strip()

firefox_version = _get_firefox_version()

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
            supported = "107.0"  # TODO, check with yokoffing
        elif "firefox release" in body.lower():
            trim_body = body.lower()[body.lower().index("firefox release"):]
            supported = re_find_version.findall(trim_body)
            if len(supported) == 0:
                print(f"Could not parse release in '{name}'. Please post this error message on https://github.com/{REPOSITORY_NAME}/{REPOSITORY_NAME}/issues")

        else:
            print(f"Could not find firefox release header '{name}'. Please post this error message on https://github.com/{REPOSITORY_NAME}/{REPOSITORY_NAME}/issues")


        print(name, supported)


_get_releases()
exit()


def backup_default_profile():
    src = str(_get_default_profile_folder())
    dest = f"{src}-backup-{datetime.today().strftime('%Y-%m-%d-%H-%M-%S')}"
    
    copytree(src, dest, ignore=ignore_patterns("*lock"))

def key_is_action(key: str):
    """ Converts multiple keys to the same string, to allow multiple controls for the same function """

    # Arrow up, Page Up, Arrow Up (Git Bash), Page Up (Git Bash), w, W, z, Z, 8
    if key in ["KEY_UP", "KEY_PPAGE", "KEY_A2", "KEY_A3", "w", "W", "z", "Z", "8"]:
        return "up"
    # Arrow down, Page Down, Arrow down (Git Bash), Page Down (Git Bash), s, S, 5, 2
    elif key in ["KEY_DOWN", "KEY_NPAGE", "KEY_C2", "KEY_C3", "s", "S", "5", "2"]:
        return "down"
    elif key in ["Return", "\n"]:
        return "select"
    elif key in ["E", "e"]:
        return "exit"
    else:
        return None



select_if_backup = [
    "Backup current profile (Recommended)",
    "Do not backup current profile"
]
SELECT_IF_BACKUP_NO_INDEX = 1


def cli(screen):
    global scroll_pos, cli_options, selected_config
    keep_running = True
    
    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t\t[ENTER] SELECT\t\n", curses.A_REVERSE)
    screen.addstr("\t[ARROW_DOWN/PAGE_DOWN] Move down\t[E] Exit\t\n\n", curses.A_REVERSE)
    screen.addstr(f"\tBETTERFOX INSTALLER\n", curses.A_BOLD)
    screen.addstr(f"\tDETECTED FIREFOX VERSION: {_get_firefox_version()}\n", curses.A_ITALIC)
    screen.addstr(f"\tDETECTED DEFAULT PROFILE: {_get_default_profile_folder().name}\n\n", curses.A_ITALIC)


    #screen.addstr("Select \t\n\n", curses.A_ITALIC)

    
    for option in cli_options[scroll_pos: scroll_pos+SCROLL_SIZE]:
        if cli_options.index(option) == scroll_pos:
            screen.addstr(f"> {option}\n", curses.A_STANDOUT)
        else:
            screen.addstr(f"{option}\n")

    screen.refresh()

    action = key_is_action(screen.getkey())
    if action == "up" and scroll_pos > 0:
        scroll_pos -= 1
    elif action == "down" and scroll_pos < len(cli_options):
        scroll_pos += 1
    elif action == "select":
        if cli_options == select_if_backup:
            if scroll_pos != SELECT_IF_BACKUP_NO_INDEX:
                backup_default_profile()
            #cli_options = select_config

        #elif cli_options == select_config:
        #    selected_config = cli_options[scroll_pos].split("\t")[0]
        #curses.endwin()
        #all_python_releases[scroll_pos].install()
        #start_cli()
        #return
        #elif cli_options == 
        #cli_options[scroll_pos] 
    elif action == "exit":
        keep_running = False

    screen.refresh()
    screen.clear()

    if keep_running:
        cli(screen)


if __name__ == "__main__":
    cli_options = select_if_backup
    curses.wrapper(cli)