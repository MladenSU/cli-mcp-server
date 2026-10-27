import importlib
import os
import tempfile
import unittest


class TestQuotedShellOperators(unittest.TestCase):
    """Shell operators inside quotes are literal text, not operators."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["ALLOWED_DIR"] = self.tempdir.name
        import cli_mcp_server.server as server_module

        self.server = importlib.reload(server_module)
        self.executor = self.server.CommandExecutor(
            allowed_dir=self.tempdir.name,
            security_config=self.server.SecurityConfig(
                allowed_commands={"rg", "echo", "ls"},
                allowed_flags={"-n", "-S"},
                max_command_length=1024,
                command_timeout=5,
            ),
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_single_quoted_pipe_is_accepted(self):
        command, args = self.executor.validate_command(
            "rg -n 'google|gdrive|google_drive|DriveAPI|GoogleDrive|drive' -S"
        )
        self.assertEqual(command, "rg")
        self.assertEqual(
            args,
            ["-n", "google|gdrive|google_drive|DriveAPI|GoogleDrive|drive", "-S"],
        )

    def test_double_quoted_pipe_is_accepted(self):
        command, args = self.executor.validate_command('rg -n "google|drive" -S')
        self.assertEqual((command, args), ("rg", ["-n", "google|drive", "-S"]))

    def test_quoted_operator_runs_without_shell(self):
        result = self.executor.execute("echo 'a|b;c>d'")
        self.assertEqual(result.stdout.strip(), "a|b;c>d")

    def test_unquoted_operator_is_still_rejected(self):
        for cmd in ("echo a | echo b", "echo 'a' | echo b", "echo a; ls", "ls > out"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(self.server.CommandSecurityError):
                    self.executor.validate_command(cmd)

    def test_operator_after_quoted_text_is_still_rejected(self):
        with self.assertRaises(self.server.CommandSecurityError):
            self.executor.execute("echo 'a|b' && ls")

    def test_unbalanced_quote_is_still_rejected(self):
        with self.assertRaises(self.server.CommandSecurityError):
            self.executor.validate_command("echo 'abc")
