from test_hook.utils import parse_log

# BUG: forgot to pass threshold after parse_log signature was updated.
# Pyright will report: Expected 2 positional arguments, but got 1.
results = parse_log("app.log")
