#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import os.path as path
import sys
import json
import shutil


from sys import stderr
from argparse import ArgumentParser

import yaml
import cerberus
import jinja2 as jinja


NOTEBOOK_REGISTRY_FILE = path.realpath(
    path.join(path.dirname(__file__), "..", "notebooks.yaml")
)
NOTEBOOK_REGISTRY_SCHEMA = {
    "notebooks": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "file": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "description": {"type": "string", "required": True},
            },
        },
    }
}

INDEX_TEMPLATE_FILE = path.realpath(
    path.join(path.dirname(__file__), "template", "index.html.j2")
)
INDEX_ASSETS_DIR = path.realpath(
    path.join(path.dirname(__file__), "template", "assets")
)


def parse_args():
    """Parse and enforce command-line arguments."""

    # Disable the automatic "-h/--help" argument to customize its message...
    parser = ArgumentParser(
        description="Generate an index page for exported (HTML) notebooks.",
        add_help=False,
    )

    parser.add_argument(
        "-h", "--help", action="help", help="Show the available options and exit."
    )
    parser.add_argument(
        "-l",
        "--lint",
        dest="lint",
        action="store_true",
        help="Ensure all referenced notebooks exist and none is left unreferenced.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Don't actually write any output files.",
    )

    parser.add_argument(
        "export_path",
        metavar="export_path",
        help="Where to find the exported (HTML) notebooks.",
    )
    parser.add_argument(
        "output_path",
        metavar="output_path",
        help="Where to write the index page and related files.",
    )

    return parser.parse_args()


def lint_notebook_references(export_path, filenames):
    errors = 0

    for filename in filenames:
        if not filename.endswith(".html"):
            print("ERROR: Exported notebook is not HTML: %s" % filename, file=stderr)
            errors += 1

        if not path.isfile(path.join(export_path, filename)):
            print("ERROR: Exported notebook does not exist: %s" % filename, file=stderr)
            errors += 1

    for filename in os.listdir(export_path):
        if not filename.endswith(".html"):
            continue

        if filename not in filenames:
            print(
                "ERROR: Missing reference for exported notebook: %s" % filename,
                file=stderr,
            )
            errors += 1

    return errors


def main():
    args = parse_args()

    export_path = path.realpath(args.export_path)
    output_path = path.realpath(args.output_path)

    if not export_path.startswith(output_path):
        print(
            "ERROR: The output path must be a prefix of the exported notebooks path.",
            file=stderr,
        )
        sys.exit(1)

    if not path.isdir(export_path):
        print(
            "ERROR: The exported notebooks path does not exist: %s" % args.export_path,
            file=stderr,
        )
        sys.exit(1)

    with open(NOTEBOOK_REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    if not (v := cerberus.Validator(NOTEBOOK_REGISTRY_SCHEMA)).validate(registry):
        print(
            "ERROR: The notebook registry YAML has errors:",
            json.dumps(v.errors, indent=2),
            file=stderr,
        )
        sys.exit(1)

    if args.lint:
        if num_errors := lint_notebook_references(
            export_path, {e["file"] for e in registry["notebooks"]}
        ):
            print(
                "ERROR: Linting found %d errors (see above)." % num_errors, file=stderr
            )
            sys.exit(1)

    with open(INDEX_TEMPLATE_FILE, "r") as f:
        template = jinja.Template(f.read())

    index_page = template.render(
        {
            "root_path": export_path.removeprefix(output_path).strip("/"),
            "notebooks": registry["notebooks"],
        }
    )

    if args.dry_run:
        sys.exit(0)

    os.makedirs(output_path, exist_ok=True)

    with open(path.join(output_path, "index.html"), "w+") as f:
        f.write(index_page + "\n")

    shutil.copytree(
        INDEX_ASSETS_DIR,
        path.join(output_path, path.basename(INDEX_ASSETS_DIR)),
        dirs_exist_ok=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass


# vim: set expandtab ts=4 sw=4:
