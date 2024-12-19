import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import zlib
import sys


sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tool import (
    load_config,
    get_branches,
    read_git_object,
    parse_commit_object,
    get_commit_history,
    build_dependency_graph,
    group_files_in_packages,
    generate_plantuml_code
)

class TestDependencyVisualizer(unittest.TestCase):

    def test_load_config(self):
        mock_csv_content = "key1,value1\nkey2,value2\n"
        with patch("builtins.open", mock_open(read_data=mock_csv_content)):
            config = load_config("config.csv")
            self.assertEqual(config, {"key1": "value1", "key2": "value2"})

    @patch("os.listdir")
    @patch("os.path.isfile")
    def test_get_branches(self, mock_isfile, mock_listdir):
        mock_listdir.return_value = ["branch1", "branch2"]
        mock_isfile.side_effect = lambda path: path.endswith("branch1") or path.endswith("branch2")
        branches = get_branches("/fake/repo")
        self.assertEqual(branches, ["branch1", "branch2"])

    @patch("builtins.open", new_callable=mock_open, read_data=zlib.compress(b"test data"))
    def test_read_git_object(self, mock_file):
        with patch("os.path.exists", return_value=True):
            data = read_git_object("/fake/repo", "abcd1234")
            self.assertEqual(data, b"test data")

    def test_parse_commit_object(self):
        raw_commit = (
            b"tree abcdef1234567890\n"
            b"parent 1234567890abcdef\n"
            b"author John Doe <john@example.com> 1234567890 +0000\n"
            b"\nCommit message here.\n"
        )
        parsed = parse_commit_object(raw_commit)
        self.assertEqual(parsed, {
            "tree": "abcdef1234567890",
            "parents": ["1234567890abcdef"],
            "author": "John Doe <john@example.com>",
            "date": 1234567890,
            "message": "Commit message here."
        })

    @patch("tool.read_git_object")
    def test_get_commit_history(self, mock_read_git_object):
        mock_read_git_object.side_effect = [
            b"tree abcdef1234567890\nparent 1234567890abcdef\nauthor John Doe <john@example.com> 1234567890 +0000\n\nFirst commit.\n",
            b"tree abcdef1234567890\nauthor Jane Smith <jane@example.com> 1234560000 +0000\n\nSecond commit.\n",
        ]
        history = get_commit_history("/fake/repo", "abcd1234")
        self.assertEqual(len(history), 2)
        self.assertIn("abcd1234", history)
        self.assertIn("1234567890abcdef", history)

    @patch("tool.read_git_object")
    def test_build_dependency_graph(self, mock_read_git_object):
        mock_read_git_object.return_value = (
            b"100644 blob abcdef1234567890\tfile1.txt\n"
            b"100644 blob 1234567890abcdef\tfile2.txt\n"
        )
        commits = {"abcd1234": {"hash": "abcd1234", "author": "John Doe", "message": "Commit 1", "parents": []}}
        graph = build_dependency_graph("/fake/repo", commits)
        self.assertIn("\"abcd1234\" --> \"file1.txt\" : modifies", graph)
        self.assertIn("\"abcd1234\" --> \"file2.txt\" : modifies", graph)

    def test_group_files_in_packages(self):
        graph = [
            '"abcd1234" --> "folder1/file1.txt" : modifies',
            '"abcd1234" --> "folder2/file2.txt" : modifies',
        ]
        result = group_files_in_packages(graph)
        self.assertIn("package \"folder1\" {", result)
        self.assertIn("\"folder1/file1.txt\" : file", result)

    def test_generate_plantuml_code(self):
        graph = [
            '"abcd1234" --> "file1.txt" : modifies',
            '"12345678" --> "file2.txt" : modifies',
        ]
        plantuml_code = generate_plantuml_code(graph)
        self.assertTrue(plantuml_code.startswith("@startuml"))
        self.assertTrue(plantuml_code.endswith("@enduml"))
        self.assertIn(graph[0], plantuml_code)

if __name__ == "__main__":
    unittest.main()
