# [[ schema.title ]]

[%- for problem_short, problem in schema.problems.items() %]
[%- set problem_summary = summary.problems[problem_short] %]

## [[ problem.title ]] ([[ problem.percentage | percentage ]])

Tests score: [[ problem_summary.tests_correct | length ]]/[[ problem_summary.tests_total ]] ([[ problem_summary.tests_percentage | percentage ]])
[% if problem_summary.setup_failed %]
Setup failed:

```
[[ problem_summary.setup_error | trim ]]
```
[% else %]
[%- for test_missed in problem_summary.tests_incorrect %]
- -1 for [[ test_missed.name ]]
[%- endfor -%]
[%- endif -%]
[%- endfor -%]