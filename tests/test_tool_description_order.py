import asyncio
import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock


class TestToolDescriptionOrder(unittest.TestCase):
    """The run_command description lists commands and flags in sorted order."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

        # Restore the environment afterwards, and neutralise ambient settings
        # that would change the reloaded module's configuration.
        env = mock.patch.dict(os.environ, {"ALLOWED_DIR": self.tempdir.name})
        env.start()
        self.addCleanup(env.stop)
        for name in ("ALLOWED_COMMANDS", "ALLOWED_FLAGS", "ALLOW_SHELL_OPERATORS"):
            os.environ.pop(name, None)

        # Import a private copy of the server module. patch.dict puts the
        # original sys.modules entry back, so the module (and its executor
        # bound to the temp dir) does not leak into other tests.
        package = importlib.import_module("cli_mcp_server")
        self.package = package
        self.original_module = sys.modules["cli_mcp_server.server"]
        self.original_attr = package.server
        modules = mock.patch.dict(sys.modules)
        modules.start()
        self.addCleanup(modules.stop)
        # Re-importing also rebinds the `server` attribute on the parent
        # package, which patch.dict(sys.modules) does not restore. Patch it too,
        # because `from cli_mcp_server import server` resolves through it.
        attr = mock.patch.object(package, "server", create=True)
        attr.start()
        self.addCleanup(attr.stop)
        sys.modules.pop("cli_mcp_server.server", None)
        self.server = importlib.import_module("cli_mcp_server.server")

    def test_private_import_does_not_leak(self):
        self.assertIsNot(self.server, self.original_module)
        self.assertIs(self.package.server, self.server)
        self.doCleanups()
        self.assertIs(sys.modules["cli_mcp_server.server"], self.original_module)
        self.assertIs(self.package.server, self.original_attr)

    def test_commands_and_flags_are_sorted(self):
        self.server.executor.security_config = self.server.SecurityConfig(
            allowed_commands={"zcat", "ls", "echo", "cat", "rg"},
            allowed_flags={"-n", "-a", "--help", "-S", "-l"},
            max_command_length=1024,
            command_timeout=5,
        )
        tools = asyncio.run(self.server.handle_list_tools())
        description = next(t for t in tools if t.name == "run_command").description
        self.assertIn("Available commands: cat, echo, ls, rg, zcat\n", description)
        self.assertIn("Available flags: --help, -S, -a, -l, -n\n", description)


if __name__ == "__main__":
    unittest.main()
