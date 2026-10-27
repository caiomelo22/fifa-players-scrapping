import unittest
from unittest.mock import patch, sentinel

from selenium.common.exceptions import SessionNotCreatedException

from src.helpers.browser import create_driver


class CreateDriverTests(unittest.TestCase):
    @patch("src.helpers.browser.uc.Chrome")
    def test_automatic_selection(self, chrome):
        chrome.return_value = sentinel.driver

        self.assertIs(create_driver(), sentinel.driver)

        chrome.assert_called_once()
        self.assertNotIn("version_main", chrome.call_args.kwargs)
        self.assertIn("--no-sandbox", chrome.call_args.kwargs["options"].arguments)
        self.assertIn(
            "--disable-dev-shm-usage", chrome.call_args.kwargs["options"].arguments
        )

    @patch("src.helpers.browser.uc.Chrome")
    def test_mismatch_retries_reported_version_with_fresh_options(self, chrome):
        chrome.side_effect = [
            SessionNotCreatedException(
                "This version of ChromeDriver only supports Chrome version 139\n"
                "Current browser version is 156.0.8078.48"
            ),
            sentinel.driver,
        ]

        self.assertIs(create_driver(), sentinel.driver)

        first, second = chrome.call_args_list
        self.assertEqual(second.kwargs["version_main"], 156)
        self.assertIsNot(first.kwargs["options"], second.kwargs["options"])
        self.assertEqual(
            first.kwargs["options"].arguments, second.kwargs["options"].arguments
        )

    @patch("src.helpers.browser.uc.Chrome")
    def test_unrelated_session_error_is_not_retried(self, chrome):
        error = SessionNotCreatedException("Chrome failed to start")
        chrome.side_effect = error

        with self.assertRaises(SessionNotCreatedException) as raised:
            create_driver()

        self.assertIs(raised.exception, error)
        chrome.assert_called_once()

    @patch("src.helpers.browser.uc.Chrome")
    def test_retry_failure_is_propagated(self, chrome):
        error = SessionNotCreatedException("Retry failed")
        chrome.side_effect = [
            SessionNotCreatedException("Current browser version is 156.0.8078.48"),
            error,
        ]

        with self.assertRaises(SessionNotCreatedException) as raised:
            create_driver()

        self.assertIs(raised.exception, error)
        self.assertEqual(chrome.call_count, 2)


if __name__ == "__main__":
    unittest.main()