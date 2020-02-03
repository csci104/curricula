import json
import jsonschema
import re
from pathlib import Path
from typing import Callable

from ...shared import Files
from .. import validate


Validator = Callable[[str], bool]


def validate_not_empty(string: str) -> bool:
    if len(string) == 0:
        print("Must not be empty!")
        return False
    return True


def validate_datetime(string: str) -> bool:
    if re.match(r"^\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}$", string) is None:
        print("Must be of the form YYYY-MM-DD HH:MM:SS!")
        return False
    return True


def validate_numeric(string: str) -> bool:
    if not string.isnumeric():
        print("Must be a positive integer!")
        return False
    return True


def validate_email(string: str) -> bool:
    if re.match(r"^.+@.+\..+$", string) is None:
        print("Invalid email!")
        return False
    return True


def validate_boolean(string: str) -> bool:
    if string.lower() not in ("y", "n", "yes", "no"):
        print("Must be (y)es or (n)o!")
        return False
    return True


def validate_weight(string: str) -> bool:
    if re.match(r"\d+(\.\d+)?", string) is None:
        print("Must be a float!")
        return False
    if not 0 <= float(string) <= 1:
        print("Must be between 0 and 1 inclusive!")
        return False
    return True


def validated_input(prompt: str = "", *validators: Validator) -> str:
    """Input until validated."""

    while True:
        response = input(prompt)
        if all(validator(response) for validator in validators):
            return response


def generate_assignment_interactive(assignment_path: Path):
    """Generate a new assignment."""

    while True:
        try:
            assignment_json = {
                "title": validated_input("Assignment title: ", validate_not_empty),
                "authors": [
                    {
                        "name": validated_input("Author name: ", validate_not_empty),
                        "email": validated_input("Author email (address@domain.com): ", validate_email)
                    }
                ],
                "dates": {
                    "assigned": validated_input("Date assigned (YYYY-MM-DD HH:MM:SS): ", validate_datetime),
                    "due": validated_input("Date due (YYYY-MM-DD HH:MM:SS): ", validate_datetime)
                },
                "problems": []
            }
        except KeyboardInterrupt:
            print("Cancelling...")
            return

        try:
            jsonschema.validate(assignment_json, validate.ASSIGNMENT_SCHEMA)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            break

    assignment_path.mkdir(parents=True, exist_ok=True)
    with assignment_path.joinpath(Files.ASSIGNMENT).open("w") as file:
        json.dump(assignment_json, file, indent=2)

    print(f"Created assignment {assignment_path.parts[-1]}")


def generate_problem_interactive(assignment_path: Path, problem_relative_path: Path):
    """Generate an assignment within the assignment."""

    while True:
        try:
            problem_json = {
                "title": validated_input("Problem title: ", validate_not_empty),
                "authors": [
                    {
                        "name": validated_input("Author name: ", validate_not_empty),
                        "email": validated_input("Author email (address@domain.com): ", validate_email)
                    }
                ],
                "topics": [
                    *map(str.strip, input("Optional topics (separated by comma): ").split(","))
                ],
                "grading": {
                    "minutes": int(validated_input("Minutes to grade (integral): ", validate_numeric)),
                    "automated": validated_input("Automated grading (y/n): ", validate_boolean).lower().startswith("y"),
                    "review": validated_input("Code review (y/n): ", validate_boolean).lower().startswith("y"),
                    "manual": validated_input("Manual grading (y/n): ", validate_boolean).lower().startswith("y"),
                }
            }
        except KeyboardInterrupt:
            print("Cancelling...")
            return

        try:
            jsonschema.validate(problem_json, validate.PROBLEM_SCHEMA)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            break

    with assignment_path.joinpath(Files.ASSIGNMENT).open("r") as file:
        assignment_json = json.load(file)

    while True:
        try:
            weight = validated_input("Problem weight (0.0-1.0): ", validate_weight)
        except KeyboardInterrupt:
            print("Cancelling...")
            return

        assignment_json["problems"].append({
            "path": str(problem_relative_path),
            "percentage": float(weight),
        })

        try:
            jsonschema.validate(assignment_json, validate.ASSIGNMENT_SCHEMA)
        except jsonschema.ValidationError as exception:
            print(exception)
        else:
            break

    with assignment_path.joinpath(Files.ASSIGNMENT).open("w") as file:
        json.dump(assignment_json, file, indent=2)

    problem_path = assignment_path.joinpath(problem_relative_path)
    problem_path.mkdir(parents=True, exist_ok=True)
    with problem_path.joinpath(Files.PROBLEM).open("w") as file:
        json.dump(problem_json, file, indent=2)

    print(f"Created problem {problem_relative_path}")
