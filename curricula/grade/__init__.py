"""Grade is a combined library for grading C++ problem sets.

Grade is capable of testing three main aspects of C++ programs:
correctness, efficiency, and style. It includes tools for testing the
output of the code under various conditions, measuring its runtime
performance and memory usage, and running style checks.
"""

import timeit

from pathlib import Path
from typing import Iterator, Iterable, Tuple

from ..log import log
from .models import GradingAssignment, GradingProblem
from .report import AssignmentReport
from .resource import Submission, Context


root = Path(__file__).absolute().parent
include = root.joinpath("include")


def run(assignment: GradingAssignment, assignment_path: Path, **options) -> AssignmentReport:
    """Run all tests on a submission and return a dict of results."""

    log.info(f"running {assignment_path}")
    reports = AssignmentReport()

    start = timeit.default_timer()

    for problem in filter(lambda p: p.grading.is_automated, assignment.problems):
        log.debug(f"running problem {problem.short}")
        submission = Submission(
            assignment_path=assignment_path,
            problem_path=assignment_path.joinpath(problem.relative_path))
        context = Context(options=options)
        reports[problem.short] = problem.grader.run(submission=submission, context=context)

    elapsed = timeit.default_timer() - start
    log.debug(f"finished in {round(elapsed, 5)} seconds")

    return reports


def run_batch(self, target_paths: Iterable[Path], **options) -> Iterator[Tuple[Path, AssignmentReport]]:
    """Run multiple reports, map directory to report."""

    # Start timer
    start = timeit.default_timer()

    for target_path in target_paths:
        yield target_path, self.run_single(target_path, **options)

    elapsed = timeit.default_timer() - start
    log.info(f"finished batch in {round(elapsed, 5)} seconds")
