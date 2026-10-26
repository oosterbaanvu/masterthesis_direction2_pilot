"""Validate arguments as well as constructor syntax before the original GX evaluator."""

import math

from dqpilot_free.worker import parse_constructor

COMMON = {"column", "column_A", "column_B", "column_list"}
PARAMS = {
    "ExpectColumnValuesToNotBeNull": set(),
    "ExpectColumnValuesToBeBetween": {"min_value", "max_value", "strict_min", "strict_max"},
    "ExpectColumnValuesToBeInSet": {"value_set"},
    "ExpectColumnValuesToBeUnique": set(),
    "ExpectColumnValuesToMatchRegex": {"regex"},
    "ExpectColumnValuesToNotMatchRegex": {"regex"},
    "ExpectColumnValueLengthsToBeBetween": {"min_value", "max_value", "strict_min", "strict_max"},
    "ExpectColumnValuesToBeOfType": {"type_"},
    "ExpectColumnPairValuesToBeEqual": {"ignore_row_if"},
    "ExpectColumnPairValuesAToBeGreaterThanB": {"or_equal", "ignore_row_if"},
    "ExpectMulticolumnSumToEqual": {"sum_total", "ignore_row_if"},
    "ExpectCompoundColumnsToBeUnique": {"ignore_row_if"},
}


def validate(code, columns):
    name, kwargs, selected = parse_constructor(code, columns)
    if set(kwargs) - COMMON - PARAMS[name]:
        raise ValueError("UNSUPPORTED_ARGUMENTS_ROW_CONDITIONS_FORBIDDEN")

    def literal(value, depth=0):
        if depth > 3:
            return False
        if value is None or type(value) in {bool, int}:
            return True
        if type(value) is float:
            return math.isfinite(value)
        if isinstance(value, str):
            return len(value) <= 2048
        return (
            isinstance(value, (list, tuple, set))
            and len(value) <= 1000
            and all(literal(v, depth + 1) for v in value)
        )

    if not all(literal(v) for v in kwargs.values()):
        raise ValueError("UNBOUNDED_OR_NONFINITE_ARGUMENT")
    if "regex" in kwargs and len(kwargs["regex"]) > 256:
        raise ValueError("REGEX_SIZE_LIMIT")
    return name, kwargs, selected
