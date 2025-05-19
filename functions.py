from math import sin, cos, exp, log

BUILTIN_FUNCTIONS = {
    "sin(x)": sin,
    "cos(x)": cos,
    "exp(x)": exp,
    "ln(1 + x)": lambda x: log(1 + x)
}
