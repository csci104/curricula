import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))
from grade import Grader
from grade.report import Report
from grade.resource import *
from grade.test.correctness import CorrectnessResult
from grade.library.process import run


grader = Grader()
root = Path(__file__).absolute().parent


def overwrite_directory(path: Path):
    shutil.rmtree(str(path))
    path.mkdir()


@grader.check()
def check_program(context: Context, report: Report):
    """Check if the program has been submitted."""

    if not context.target.joinpath("test.cpp").exists():
        report.entry("note", "check_program", "File test.cpp is missing")


@grader.build(name="program")
def build_program(context: Context):
    """Compile program with GCC."""

    source = context.target.joinpath("program.cpp")
    build = root.joinpath("build")
    overwrite_directory(build)
    executable = build.joinpath("program")
    runtime = run("g++", "-Wall", "-o", str(executable), str(source), timeout=5)
    if runtime.code == 0:
        return Executable(str(executable))
    raise Exception()


@grader.test()
def test_pass(program: Executable):
    """Basic pass."""

    runtime = program.execute("pass", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_fail(log: Logger, program: Executable):
    """Basic pass with fail."""

    runtime = program.execute("fail", timeout=1)
    passing = runtime.stdout.strip() == "pass"
    result = CorrectnessResult(passing, runtime)
    if not passing:
        log[2]("expected pass, got", runtime.stdout.strip())
    return result


@grader.test()
def test_error(log: Logger, program: Executable):
    """Basic pass with error handling."""

    runtime = program.execute("error", timeout=1.0)
    if runtime.code != 0:
        log[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            log[4](line)
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    log[2]("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_fault(log: Logger, program: Executable):
    """Basic pass with fault detection."""

    runtime = program.execute("fault", timeout=1.0)
    if runtime.code != 0:
        log[2]("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            log[4](line)
        if runtime.code == -11:
            log[4]("segmentation fault")
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    log("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


@grader.test()
def test_timeout(log: Logger, program: Executable):
    """Basic pass with timeout."""

    runtime = program.execute("hang", timeout=1.0)

    if runtime.timeout:
        return CorrectnessResult(False, runtime)

    if runtime.code != 0:
        log("received return code", runtime.code)
        for line in filter(None, runtime.stderr.split("\n")):
            log[2](line)
        if runtime.code == -11:
            log[2]("segmentation fault")
        return CorrectnessResult(False, runtime)

    passing = runtime.stdout.strip() == "pass"
    log("expected pass, got fail")
    return CorrectnessResult(passing, runtime)


if __name__ == "__main__":
    from grade.shell import main
    main(grader)
