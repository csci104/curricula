import jinja2
import json
from pathlib import Path
from typing import Dict, Union, List
from dataclasses import dataclass

from ..mapping.markdown import jinja2_create_environment
from ..mapping.models import Assignment, Problem
from ..mapping.shared import Files, Paths
from ..library import files


@dataclass(repr=False, eq=False)
class Context:
    """Build context."""

    environment: jinja2.Environment
    material_path: Path
    options: Dict[str, str]


def compile_readme(
        context: Context,
        assignment: Assignment,
        template_relative_path: str,
        destination_path: Path) -> Path:
    """Compile a README from an assignment.

    This function returns the final path of the README, which may be
    different if the provided destination is a directory.
    """

    template = context.environment.get_template(f"template/{template_relative_path}")
    if destination_path.is_dir():
        destination_path = destination_path.joinpath(Files.README)
    with destination_path.open("w") as file:
        file.write(template.render(assignment=assignment))
    return destination_path


def merge_contents(assignment: Assignment, contents_relative_path: Path, destination_path: Path):
    """Compile subdirectories from problems into a single directory."""

    destination_path.mkdir(exist_ok=True)

    assignment_contents_path = assignment.path.joinpath(contents_relative_path)
    if assignment_contents_path.exists():
        files.copy_directory(assignment_contents_path, destination_path)

    for problem in assignment.problems:
        problem_contents_path = problem.path.joinpath(contents_relative_path)
        if problem_contents_path.exists():
            files.copy_directory(problem_contents_path, destination_path, merge=True)


def aggregate_contents(assignment: Assignment, contents_relative_path: Path, destination_path: Path) -> List[Path]:
    """Compile subdirectories from problems to respective directories.

    This method returns a list of the resultant folders that were
    copied into the destination.
    """

    destination_path.mkdir(exist_ok=True)

    assignment_contents_path = assignment.path.joinpath(contents_relative_path)
    if assignment_contents_path.exists():
        files.copy_directory(assignment_contents_path, destination_path)

    copied_paths = []
    for problem in assignment.problems:
        problem_contents_path = problem.path.joinpath(contents_relative_path)
        if problem_contents_path.exists():
            problem_destination_path = destination_path.joinpath(problem.short)
            copied_paths.append(problem_destination_path)
            files.copy_directory(problem_contents_path, problem_destination_path)

    return copied_paths


def build_instructions(context: Context, assignment: Assignment, path: Path):
    """Build all site components."""

    instructions_path = path.joinpath(Paths.INSTRUCTIONS)
    instructions_path.mkdir(exist_ok=True)
    compile_readme(context, assignment, "instructions/assignment.md", instructions_path)
    merge_contents(assignment, Paths.ASSETS, instructions_path.joinpath(Paths.ASSETS))


def build_resources(context: Context, assignment: Assignment, path: Path):
    """Compile resources files."""

    resources_path = path.joinpath(Paths.RESOURCES)
    resources_path.mkdir(exist_ok=True)
    aggregate_contents(assignment, Paths.RESOURCES, resources_path)


def build_solution_readme(context: Context, assignment: Assignment, path: Path):
    """Generate the composite README."""

    assignment_template = context.environment.get_template("template/solution/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_solution_code(assignment: Assignment, path: Path):
    """Compile only submission files of the solution."""

    for problem in assignment.problems:
        problem_solution_path = problem.path.joinpath(Paths.SOLUTION)
        if problem_solution_path.exists() and problem.submission:
            for submission_path in map(Path, problem.submission):
                relative_source_path = problem.path.joinpath(Paths.SOLUTION, *submission_path.parts[1:])
                relative_destination_path = path.joinpath(problem.short, *submission_path.parts[1:])
                relative_destination_path.parent.mkdir(parents=True, exist_ok=True)
                files.copy(relative_source_path, relative_destination_path)


def build_solution(context: Context, assignment: Assignment, path: Path):
    """Compile cheatsheets."""

    solution_path = path.joinpath(Paths.SOLUTION)
    solution_path.mkdir(exist_ok=True)
    build_solution_readme(context, assignment, solution_path)
    build_solution_code(assignment, solution_path)


def build_grading_readme(context: Context, assignment: Assignment, path: Path):
    """Aggregate README for rubric."""

    assignment_template = context.environment.get_template("template/grading/assignment.md")
    with path.joinpath(Files.README).open("w") as file:
        file.write(assignment_template.render(assignment=assignment))


def build_grading_schema(assignment: Assignment, path: Path):
    """Generate a JSON data file with grading metadata."""

    # Generate a grading schema JSON
    percentages = {}
    automated = []

    for problem in assignment.problems:
        percentages[problem.short] = problem.percentage
        if "automated" in problem.grading.process:
            automated.append(problem.short)

    with path.joinpath(Files.GRADING).open("w") as file:
        json.dump(dict(percentages=percentages, automated=automated), file, indent=2)


def build_grading(context: Context, assignment: Assignment, path: Path):
    """Compile rubrics."""

    grading_path = path.joinpath(Paths.GRADING)
    grading_path.mkdir(exist_ok=True)
    build_grading_readme(context, assignment, grading_path)
    build_grading_schema(assignment, grading_path)
    copied_paths = aggregate_contents(assignment, Paths.GRADING, grading_path)

    # Delete extra READMEs
    for copied_path in copied_paths:
        readme_path = copied_path.joinpath(Files.README)
        if readme_path.exists():
            files.delete(readme_path)


BUILD_STEPS = (
    build_instructions,
    build_resources,
    build_solution,
    build_grading
)


@jinja2.environmentfilter
def get_readme(environment: jinja2.Environment, item: Union[Problem, Assignment], *component: str) -> str:
    """Render a README with options for nested path."""

    context: Context = environment.globals["context"]  # Not jinja2 context, our context
    readme_path = item.path.joinpath(*component, Files.README).relative_to(context.material_path)

    if isinstance(item, Assignment):
        return environment.get_template(str(readme_path)).render(assignment=item)
    elif isinstance(item, Problem):
        return environment.get_template(str(readme_path)).render(assignment=item.assignment, problem=item)


def has_readme(item: Union[Problem, Assignment], *component: str) -> bool:
    """Check whether a problem has a solution README."""

    return item.path.joinpath(*component, Files.README).exists()


def jinja2_create_build_environment(**options) -> jinja2.Environment:
    """Add a couple filters for content building."""

    environment = jinja2_create_environment(**options)
    environment.filters.update(get_readme=get_readme, has_readme=has_readme)
    return environment


def build(material_path: Path, **options):
    """Build the assignment at a given path."""

    if not material_path.is_dir():
        raise ValueError("material path does not exist!")

    environment = jinja2_create_build_environment(loader=jinja2.FileSystemLoader(str(material_path)))
    context = Context(environment, material_path, options)
    environment.globals["context"] = context

    artifacts_path = material_path.parent.joinpath("artifacts")
    artifacts_path.mkdir(exist_ok=True)

    for assignment_path in material_path.joinpath("assignment").glob("*/"):
        if not assignment_path.is_dir():
            continue

        assignment = Assignment.load(assignment_path)
        if assignment_path.parts[-1] == options.get("assignment"):
            continue

        assignment_artifacts_path = artifacts_path.joinpath(assignment_path.parts[-1])
        files.replace_directory(assignment_artifacts_path)

        for step in BUILD_STEPS:
            step(context, assignment, assignment_artifacts_path)
