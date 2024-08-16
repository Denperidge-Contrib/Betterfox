from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from shutil import copytree, ignore_patterns
from datetime import datetime
from urllib import request
import curses

FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute()  # TODO: Windows
SCROLL_SIZE = 5

scroll_pos = 0

selected_if_backup = None
selected_config = ""




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
    
select_config = [
        "Fastfox\t- Increase Firefox's browsing speed. Give Chrome a run for its money!",
        "Securefox\t- Protect user data without causing site breakage.",
        "Peskyfox\t- Provide a clean, distraction-free browsing experience.",
        "Smoothfox\t- Get Edge-like smooth scrolling on your favorite browser — or choose something more your style.",
        "user.js\t\t- All the essentials. None of the breakage. This is your user.js."
    ]


def cli(screen):
    global scroll_pos, cli_options
    keep_running = True
    
    screen.addstr("\t[ARROW_UP/PAGE_UP] Move up\t\t[ENTER] SELECT\t\n", curses.A_REVERSE)
    screen.addstr("\t[ARROW_DOWN/PAGE_DOWN] Move down\t[E] Exit\t\n\n", curses.A_REVERSE)


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
            if scroll_pos != 1:
                backup_default_profile()
            cli_options = select_config

        elif cli_options == select_config:
            pass
        #curses.endwin()
        #all_python_releases[scroll_pos].install()
        #start_cli()
        #return
        pass
        cli_options[scroll_pos] 
    elif action == "exit":
        keep_running = False

    screen.refresh()
    screen.clear()

    if keep_running:
        cli(screen)


if __name__ == "__main__":
    cli_options = select_if_backup
    curses.wrapper(cli)