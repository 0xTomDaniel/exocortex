import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("node", Path(__file__).parents[1] / "scripts/herdr_inventory_node.py")
node = importlib.util.module_from_spec(spec)
spec.loader.exec_module(node)


class InventoryTests(unittest.TestCase):
    def test_allowed(self):
        self.assertEqual(node.command_for({"operation": "agents"}), ["agent", "list"])
        self.assertEqual(node.command_for({"operation": "workspaces"}), ["workspace", "list"])

    def test_denied(self):
        for request in [None, [], {}, {"operation": []}, {"operation": "stop"},
                        {"operation": "agents; touch /tmp/pwned"},
                        {"operation": "agents", "args": ["--session", "other"]},
                        {"operation": "prompt"}, {"operation": "run"}]:
            with self.subTest(request=request), self.assertRaises(ValueError):
                node.command_for(request)


if __name__ == "__main__":
    unittest.main()
