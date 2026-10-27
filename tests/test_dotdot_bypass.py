import importlib
import os
import shutil
import tempfile
import unittest


class TestBareDotDotArgument(unittest.TestCase):
    """A bare ".." operand must be confined to ALLOWED_DIR like "../" is."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["ALLOWED_DIR"] = self.tempdir.name
        os.environ.pop("ALLOWED_COMMANDS", None)
        os.environ.pop("ALLOWED_FLAGS", None)
        os.environ.pop("ALLOW_SHELL_OPERATORS", None)
        import cli_mcp_server.server as server_module

        self.server = importlib.reload(server_module)
        self.executor = self.server.CommandExecutor(
            allowed_dir=self.tempdir.name,
            security_config=self.server.SecurityConfig(
                allowed_commands={"ls"},
                allowed_flags={"-l"},
                max_command_length=1024,
                command_timeout=5,
            ),
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_bare_dotdot_is_rejected(self):
        with self.assertRaises(self.server.CommandSecurityError):
            self.executor.validate_command("ls ..")

    def test_dotdot_slash_is_rejected(self):
        with self.assertRaises(self.server.CommandSecurityError):
            self.executor.validate_command("ls ../")

    def test_sibling_with_shared_prefix_is_rejected(self):
        sibling = self.tempdir.name.rstrip(os.sep) + "x"
        os.makedirs(sibling)
        self.addCleanup(shutil.rmtree, sibling, ignore_errors=True)
        relative = "../" + os.path.basename(sibling)
        for arg in (relative, sibling):
            with self.subTest(arg=arg):
                with self.assertRaises(self.server.CommandSecurityError):
                    self.executor.validate_command(f"ls {arg}")
        self.assertFalse(self.executor._is_path_safe(sibling))

    def test_path_inside_allowed_dir_is_allowed(self):
        inner = os.path.join(self.tempdir.name, "sub")
        os.makedirs(inner)
        self.assertTrue(self.executor._is_path_safe(inner))
        _, args = self.executor.validate_command("ls ./sub")
        self.assertEqual(args, [os.path.realpath(inner)])

    def test_dot_is_still_allowed(self):
        command, args = self.executor.validate_command("ls .")
        self.assertEqual(command, "ls")
        self.assertEqual(args, [os.path.realpath(self.tempdir.name)])


if __name__ == "__main__":
    unittest.main()
