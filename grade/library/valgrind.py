import os
from xml.etree.ElementTree import Element, parse
from typing import Optional, List, TextIO
from dataclasses import dataclass, field

from . import process

VALGRIND_ARGS = ("valgrind", "--tool=memcheck", "--leak-check=yes", "--xml=yes")
VALGRIND_XML_FILE = "valgrind.xml"



@dataclass
class ValgrindWhat:
    """Explanation of error, can have dynamic tags."""

    text: str
    fields: dict = field(default_factory=dict)

    @classmethod
    def load(cls, element: Optional[Element]) -> "Optional[ValgrindWhat]":
        """Load either what or xwhat."""

        if element is None:
            return None

        if element.tag == "what":
            return ValgrindWhat(element.text)
        else:
            text = ""
            fields = dict()
            for child in element:
                if child.tag == "tag":
                    text = child.text
                else:
                    fields[child.tag] = child.text
            return ValgrindWhat(text, fields)


@dataclass
class ValgrindError:
    """Represents an error tag from a Valgrind XML report."""

    unique: int
    tid: int
    kind: str
    what: Optional[ValgrindWhat]

    @classmethod
    def load(cls, element: Element) -> "ValgrindError":
        """Load an error from an element."""

        unique = int(element.find("unique").text, 16)
        tid = int(element.find("tid").text)
        kind = element.find("kind").text
        what = ValgrindWhat.load(element.find("what") or element.find("xwhat"))
        return cls(unique, tid, kind, what)


@dataclass
class ValgrindReport:
    """Include data about memory lost and errors."""

    runtime: process.Runtime
    errors: Optional[List[ValgrindError]]

    def memory_lost(self) -> (int, int):
        """Count up bytes and blocks lost."""

        leaked_bytes = 0
        leaked_blocks = 0
        for error in self.errors:
            if error.kind in ("Leak_DefinitelyLost", "Leak_IndirectlyLost", "Leak_PossiblyLost"):
                leaked_bytes += int(error.what.fields["leakedbytes"])
                leaked_blocks += int(error.what.fields["leakedblocks"])
        return leaked_bytes, leaked_blocks


def run(*args: str, timeout: float) -> Optional[ValgrindReport]:
    """Run valgrind on the program and return IR count."""

    runtime = process.run(*VALGRIND_ARGS, f"--xml-file={VALGRIND_XML_FILE}", *args, timeout=timeout)
    if os.path.exists(VALGRIND_XML_FILE):
        errors = []
        with open(VALGRIND_XML_FILE) as file:
            root = parse(file).getroot()
            for child in root:
                if child.tag == "error":
                    errors.append(ValgrindError.load(child))
        os.remove(VALGRIND_XML_FILE)
        return ValgrindReport(runtime, errors)
    return ValgrindReport(runtime, None)
