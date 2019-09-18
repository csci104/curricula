from dataclasses import dataclass, field

from ..task import Task


@dataclass
class Result:
    """The result of a test."""

    details: dict = field(default_factory=dict)


@dataclass
class Test(Task[Result]):
    """A general test for a codebase.

    From this class the correctness, complexity, and style tests are
    derived such that they can be run generically. It is intended to
    wrap a raw runnable with metadata used during registration.
    """

    def __str__(self):
        return self.name

    def __hash__(self):
        return super().__hash__()
