import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scaleproof.audit_security import boundary, RULES
from scaleproof.operations import verify_owner

class SecurityTests(unittest.TestCase):
    def test_public_import_graph_has_no_execution_path(self):
        self.assertEqual(boundary(),["api","common","policy","storage"])
    def test_owned_target_refuses_public_host_before_mutation(self):
        with patch("scaleproof.operations.read_json",return_value={"cluster":"scaleproof","target":"https://example.org"}), patch("scaleproof.operations.run") as command:
            with self.assertRaises(ValueError): verify_owner()
            command.assert_not_called()
    def test_owned_target_requires_record(self):
        with patch("scaleproof.operations.read_json",side_effect=FileNotFoundError), patch("scaleproof.operations.run") as command:
            with self.assertRaises(FileNotFoundError): verify_owner()
            command.assert_not_called()
    def test_rules_detect_secret_shapes_without_values(self):
        self.assertIsNotNone(RULES["credential_uri"].search(b"postgresql"+b"://user:example-secret@host/db"))
        self.assertIsNone(RULES["credential_uri"].search(b"postgresql://host/db"))
