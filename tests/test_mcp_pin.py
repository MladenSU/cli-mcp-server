import re
import unittest
from importlib import metadata
from pathlib import Path


class TestMcpCompatibility(unittest.TestCase):
    def test_installed_mcp_has_decorator_api(self):
        from mcp.server import Server

        server = Server("probe")
        self.assertTrue(hasattr(server, "list_tools"))
        self.assertTrue(hasattr(server, "call_tool"))

    def test_mcp_dependency_is_capped_below_2(self):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        match = re.search(r'"(mcp[^"]*)"', pyproject.read_text())
        self.assertIsNotNone(match)
        self.assertIn("<2", match.group(1).replace(" ", ""))
        self.assertLess(int(metadata.version("mcp").split(".")[0]), 2)


if __name__ == "__main__":
    unittest.main()
