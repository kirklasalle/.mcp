import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.network_safety import validate_public_https_url


class NetworkSafetyTests(unittest.TestCase):
    def test_rejects_non_https_and_local_ip_literals(self):
        for url in (
            "http://example.org/data",
            "https://127.0.0.1/admin",
            "https://[::1]/admin",
            "https://user:pass@example.org/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_public_https_url(url)

    @patch("shared.network_safety.socket.getaddrinfo")
    def test_rejects_private_dns_resolution(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("10.0.0.5", 443))]
        with self.assertRaisesRegex(ValueError, "non_public_network_destination"):
            validate_public_https_url("https://example.org/data")

    @patch("shared.network_safety.socket.getaddrinfo")
    def test_accepts_public_https_resolution(self, getaddrinfo):
        getaddrinfo.return_value = [(None, None, None, None, ("8.8.8.8", 443))]
        self.assertEqual(
            validate_public_https_url("https://example.org/data"),
            "https://example.org/data",
        )


if __name__ == "__main__":
    unittest.main()
