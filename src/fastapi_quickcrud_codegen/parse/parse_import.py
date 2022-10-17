import ast
from collections import namedtuple

Import = namedtuple("Import", ["module", "name", "alias"])

def get_imports(path):
    with open(path) as fh:
       root = ast.parse(fh.read(), path)

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split('.')
        else:
            continue

        for n in node.names:
            if not module:
                yield f'import {n.name} '
            elif n.asname:
                yield f'from {".".join(module)} import {n.name} as {n.asname}'
            else:
                yield f'from {".".join(module)} import {n.name} '
