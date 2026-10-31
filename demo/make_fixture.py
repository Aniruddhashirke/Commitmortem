"""Builds demo/sample-dead-repo: a tiny abandoned Python project whose tests fail on modern Python."""
import os, subprocess, shutil
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-dead-repo"); shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
def sh(*a, env=None): subprocess.run(a, cwd=D, check=True, capture_output=True, env={**os.environ, **(env or {})})
def commit(date, who, msg, files):
    for n, t in files.items(): open(os.path.join(D, n), "w").write(t)
    e = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "GIT_AUTHOR_NAME": who, "GIT_COMMITTER_NAME": who, "GIT_AUTHOR_EMAIL": who.lower().replace(" ", ".") + "@example.com", "GIT_COMMITTER_EMAIL": "x@example.com"}
    sh("git", "add", "-A"); sh("git", "commit", "-qm", msg, env=e)
sh("git", "init", "-q")
commit("2016-03-01T10:00:00", "Ravi Kulkarni", "initial commit: tiny config merger", {"README.md": "# confmerge\nMerge dict configs.\n"})
commit("2016-03-09T10:00:00", "Ravi Kulkarni", "add merge() for nested mappings", {"confmerge.py": "import collections\n\ndef merge(a, b):\n    out = dict(a)\n    for k, v in b.items():\n        if isinstance(v, collections.Mapping) and isinstance(out.get(k), collections.Mapping):\n            out[k] = merge(out[k], v)\n        else:\n            out[k] = v\n    return out\n"})
commit("2016-04-02T10:00:00", "Ravi Kulkarni", "tests for merge, fixes nested override bug", {"test_confmerge.py": "import unittest\nfrom confmerge import merge\n\nclass T(unittest.TestCase):\n    def test_nested(self):\n        self.assertEqual(merge({'a': {'x': 1}}, {'a': {'y': 2}}), {'a': {'x': 1, 'y': 2}})\n"})
commit("2016-06-20T10:00:00", "Meera Joshi", "release 1.0: add yaml loader stub", {"loader.py": "# TODO: actually parse yaml\ndef load(path):\n    raise NotImplementedError\n"})
commit("2017-01-11T10:00:00", "Ravi Kulkarni", "why does merge drop lists? leaving as is for now", {"NOTES.txt": "lists are replaced not merged, by design\n"})
commit("2017-02-02T10:00:00", "Ravi Kulkarni", "last commit before holidays, will return", {"README.md": "# confmerge\nMerge dict configs.\n\nStatus: paused.\n"})
print("fixture at", D)
