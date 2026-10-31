"""CLI: python3 -m harness.run <skill> [key=value ...]   e.g. scan-repo source=demo/sample-dead-repo"""
import sys, json
from .core import Harness
def main(argv):
    h = Harness()
    if not argv or argv[0] == "list": print(json.dumps(h.list(), indent=2)); return
    args = {}
    for kv in argv[1:]:
        k, v = kv.split("=", 1); args[k] = int(v) if v.isdigit() else v
    print(json.dumps(h.run(argv[0], **args), indent=2, default=str)[:4000])
if __name__ == "__main__": main(sys.argv[1:])
