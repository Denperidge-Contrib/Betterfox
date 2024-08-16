from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from shutil import copytree, ignore_patterns
from datetime import datetime

FIREFOX_ROOT = Path.home().joinpath(".mozilla/firefox").absolute()  # TODO: Windows

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


if __name__ == "__main__":
    backup_default_profile()