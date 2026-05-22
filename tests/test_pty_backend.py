import unittest
from unittest import mock

from twiglterm.pty_backend import shell_command


class PtyBackendTests(unittest.TestCase):
    def test_explicit_command_wins(self):
        self.assertEqual(shell_command("auto", ["python", "-V"]), ["python", "-V"])

    @mock.patch("twiglterm.pty_backend.shutil.which", return_value="/bin/zsh")
    def test_named_shell_resolves_path(self, _):
        self.assertEqual(shell_command("zsh"), ["/bin/zsh"])


if __name__ == "__main__":
    unittest.main()

