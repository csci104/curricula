import argparse
import json
from pathlib import Path

from .grader import Grader
from .resource import Context
from .shell.summarize import summarize
from ..plugin import Plugin

MODES = ("parallel", "linear")


def single(grader: Grader, args: dict):
    """Run tests on a single target and print report."""

    context = Context(Path(args.pop("target")).absolute(), args)
    report = grader.run(context=context)
    with Path(args.pop("report")).open("w") as file:
        json.dump(report.dump(), file, indent=2)


class GradePlugin(Plugin):
    """Implement grade plugin."""

    name = "grade"
    help = "Manage assignment grading for submissions"

    @classmethod
    def setup(cls, parser: argparse.ArgumentParser):
        """Setup argument parser for grade command."""

        subparsers = parser.add_subparsers(required=True, dest="command")

        single_parser = subparsers.add_parser("single")
        single_parser.add_argument("target", help="run tests on a single target")
        single_parser.add_argument("report", help="where to write the report to")

        summarize_parser = subparsers.add_parser("summarize")
        summarize_parser.add_argument("reports", help="the directory containing the grade reports")

    @classmethod
    def run(cls, parser: argparse.ArgumentParser, args: argparse.Namespace):
        """Start the grader."""

        command = args.pop("command")
        if command == "single":
            single(grader, args)
        elif command == "summarize":
            summarize(grader, args)
