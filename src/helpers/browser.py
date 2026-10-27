import re

import undetected_chromedriver as uc
from selenium.common.exceptions import SessionNotCreatedException


def create_driver():
    """Start Chrome, retrying a version mismatch with fresh options."""
    def new_options():
        options = uc.ChromeOptions()
        # options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return options

    try:
        return uc.Chrome(options=new_options())
    except SessionNotCreatedException as error:
        # Automatic selection downloads the latest driver, which can differ
        # from the installed browser. Chrome reports its actual version here.
        browser_version = re.search(
            r"Current browser version is (\d+)\.", str(error)
        )
        if browser_version is None:
            raise
        version_main = int(browser_version.group(1))

    # Retry outside the exception handler so the failed session can be released.
    return uc.Chrome(options=new_options(), version_main=version_main)