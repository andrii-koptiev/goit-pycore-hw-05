"""Analyze a log file: count entries per level and show level details.

Usage: python3 task3_logger.py <file_path> [<level>]
Tests: python3 task3_logger.py --test
"""

import sys
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Optional, TypedDict


class LogLine(TypedDict):
    """A single parsed log line."""

    date_time: str
    level: str
    message: str


class LogsCount(TypedDict):
    """Number of log entries for each standard level."""

    info: int
    debug: int
    error: int
    warning: int


def handle_file_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate a CLI function to handle file errors and exit cleanly.

    Catches file-related errors raised by func, prints a readable message
    instead of a traceback and exits with code 1.

    Args:
        func: Function to wrap, usually main().

    Returns:
        Wrapped function with the same name and docstring as func.
    """

    @wraps(func)
    def inner(*args, **kwargs) -> Any:
        """Call func and turn known errors into messages."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(
                f"Error: The file '{e.filename}' was not found. "
                "Check the path and try again."
            )
            sys.exit(1)
        except PermissionError as e:
            print(
                "Error: Permission denied. "
                f"You do not have access rights to read '{e.filename}'."
            )
            sys.exit(1)
        except UnicodeDecodeError:
            print(
                "Error: Cannot read text encoding. Ensure file is stored in UTF-8 format."
            )
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected system exception occurred while processing logs: {e}")
            sys.exit(1)

    return inner


def parse_log_line(line: str) -> LogLine:
    """Split a log line into date and time, level and message.

    Malformed lines do not raise; missing parts get placeholder values.

    Args:
        line: Log line in the format "<date> <time> <LEVEL> <message>".

    Returns:
        A LogLine with date_time, level and message.
    """
    # Split by spaces up to the 3rd space to isolate date, time, and level safely
    parts = line.split(" ", 3)

    # Protect against short/malformed log lines
    if len(parts) < 4:
        return {
            "date_time": parts[0] if len(parts) > 0 else "UNKNOWN_DATE",
            "level": parts[1] if len(parts) > 1 else "UNKNOWN",
            "message": parts[2] if len(parts) > 2 else line,
        }

    date_time = f"{parts[0]} {parts[1]}"
    level = parts[2]
    message = parts[3]

    return {"date_time": date_time, "level": level, "message": message}


def filter_logs_by_level(logs: list[LogLine], level: str) -> list[LogLine]:
    """Return the logs that have the given level.

    Args:
        logs: Parsed log lines.
        level: Level to keep, case-insensitive.

    Returns:
        Matching logs, in their original order.
    """
    return list(filter(lambda log: log["level"].casefold() == level.casefold(), logs))


def count_logs_by_level(lines: list[LogLine]) -> LogsCount:
    """Count logs for each standard level.

    Args:
        lines: Parsed log lines.

    Returns:
        Counts for info, debug, error and warning; other levels are ignored.
    """
    # Use defaultdict to handle case-insensitive or missing keys safely
    counts: defaultdict[str, int] = defaultdict(int)

    for line in lines:
        # Normalize to lowercase to match the LogsCount keys (e.g., "INFO" -> "info")
        level_key = line["level"].lower()
        counts[level_key] += 1

    # Construct the strict TypedDict structure explicitly
    # The defaultdict gives 0 for levels that did not appear in the logs
    return {
        "info": counts["info"],
        "debug": counts["debug"],
        "error": counts["error"],
        "warning": counts["warning"],
    }


def display_log_counts(
    counts: LogsCount, logs: list[LogLine], target_level: Optional[str] = None
) -> None:
    """Print a table of counts and, optionally, the logs for one level.

    Args:
        counts: Counts per level, from count_logs_by_level().
        logs: All parsed log lines.
        target_level: Level whose logs to print; None prints the table only.
    """
    # Print the table header
    print(f"{'Log Level':<16} | {'Count'}")
    print(f"{'-' * 16}-|{'-' * 10}")

    # Print each log level row
    for level, count in counts.items():
        print(f"{level.upper():<16} | {count}")

    # Display additional details if a target level argument was supplied
    if target_level:
        # Check if the requested level is valid or empty
        valid_levels = {"info", "debug", "error", "warning"}
        if target_level.lower() not in valid_levels:
            print(f"\n[Warning] '{target_level}' is not a standard log level tracker.")

        filtered = filter_logs_by_level(logs, target_level)
        print(f"\nLog details for level '{target_level.upper()}':")

        if not filtered:
            print("No matching logs found for this severity level.")
        else:
            for log in filtered:
                print(f"{log['date_time']} - {log['message']}")


def load_logs(file_path: str) -> list[LogLine]:
    """Read a log file and parse its non-empty lines.

    Args:
        file_path: Path to a UTF-8 log file.

    Returns:
        Parsed log lines.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return [parse_log_line(line.strip()) for line in file if line.strip()]


@handle_file_errors
def main() -> None:
    """Read CLI arguments, load the log file and print the report."""
    if len(sys.argv) < 2:
        print("Usage: python script.py <file_path> [<display_level>]")
        sys.exit(1)

    file_path = sys.argv[1]
    display_level = sys.argv[2] if len(sys.argv) > 2 else None

    logs = load_logs(file_path)

    if not logs:
        print(f"File '{file_path}' was read successfully but contains no data.")
        sys.exit(0)

    level_count = count_logs_by_level(logs)
    display_log_counts(level_count, logs, display_level)


# Test cases. Run: python3 task3_logger.py --test
def run_tests() -> None:
    """Run assert-based tests for all functions, including corner cases."""
    import io
    import os
    import tempfile
    from contextlib import redirect_stdout

    sample = (
        "2024-01-22 08:30:01 INFO User logged in successfully.\n"
        "2024-01-22 08:45:23 DEBUG Attempting to connect to the database.\n"
        "2024-01-22 09:00:45 ERROR Database connection failed.\n"
        "2024-01-22 09:15:10 INFO Data export completed.\n"
        "2024-01-22 10:30:55 WARNING Disk usage above 80%.\n"
        "2024-01-22 11:05:00 DEBUG Starting data backup process.\n"
        "2024-01-22 11:30:15 ERROR Backup process failed.\n"
        "2024-01-22 12:00:00 INFO User logged out.\n"
        "2024-01-22 12:45:05 DEBUG Checking system health.\n"
        "2024-01-22 13:30:30 INFO Scheduled maintenance.\n"
    )
    zero_counts = {"info": 0, "debug": 0, "error": 0, "warning": 0}

    def write_file(directory: str, name: str, content: bytes) -> str:
        """Create a file with the given bytes and return its path."""
        path = os.path.join(directory, name)
        with open(path, "wb") as file:
            file.write(content)
        return path

    def capture(func, *args) -> str:
        """Call func and return everything it printed."""
        output = io.StringIO()
        with redirect_stdout(output):
            func(*args)
        return output.getvalue()

    def run_main(*args: str) -> tuple[int, str]:
        """Run main() with CLI args and return (exit code, printed output)."""
        old_argv = sys.argv
        sys.argv = ["task3_logger.py", *args]
        output = io.StringIO()
        code = 0
        try:
            with redirect_stdout(output):
                main()
        except SystemExit as error:
            code = error.code if isinstance(error.code, int) else 1
        finally:
            sys.argv = old_argv
        return code, output.getvalue()

    # --- parse_log_line ---

    # Normal line
    assert parse_log_line("2024-01-22 08:30:01 INFO User logged in.") == {
        "date_time": "2024-01-22 08:30:01",
        "level": "INFO",
        "message": "User logged in.",
    }

    # Message keeps its inner spaces (split stops after the 3rd space)
    line = "2024-01-22 08:30:01 ERROR a  b   c"
    assert parse_log_line(line)["message"] == "a  b   c"

    # Message with special characters
    line = "2024-01-22 10:30:55 WARNING Disk 80%: /dev/sda1"
    assert parse_log_line(line)["message"] == "Disk 80%: /dev/sda1"

    # Malformed lines do not crash and return all three keys
    for bad_line in ["", "garbage", "2024-01-22", "2024-01-22 08:30:01"]:
        parsed = parse_log_line(bad_line)
        assert set(parsed) == {"date_time", "level", "message"}, bad_line

    # --- filter_logs_by_level ---

    logs = [parse_log_line(line) for line in sample.splitlines()]

    assert len(filter_logs_by_level(logs, "ERROR")) == 2
    assert len(filter_logs_by_level(logs, "info")) == 4  # case-insensitive
    assert len(filter_logs_by_level(logs, "WaRnInG")) == 1
    assert filter_logs_by_level(logs, "CRITICAL") == []  # unknown level
    assert filter_logs_by_level([], "INFO") == []  # no logs

    # Order of the original logs is kept
    errors = filter_logs_by_level(logs, "error")
    assert [log["date_time"] for log in errors] == [
        "2024-01-22 09:00:45",
        "2024-01-22 11:30:15",
    ]

    # --- count_logs_by_level ---

    assert count_logs_by_level(logs) == {
        "info": 4,
        "debug": 3,
        "error": 2,
        "warning": 1,
    }

    # Empty input -> all levels present with 0
    assert count_logs_by_level([]) == zero_counts

    # Level case does not matter
    mixed = [
        parse_log_line(f"2024-01-22 08:00:00 {level} m")
        for level in ("info", "Info", "INFO")
    ]
    assert count_logs_by_level(mixed)["info"] == 3

    # Unknown levels are ignored, result keeps exactly 4 keys
    unknown = [parse_log_line("2024-01-22 08:00:00 CRITICAL boom")]
    assert count_logs_by_level(unknown) == zero_counts

    # --- display_log_counts ---

    counts = count_logs_by_level(logs)

    # Table only, no details without a level
    out = capture(display_log_counts, counts, logs)
    assert "INFO             | 4" in out
    assert "WARNING          | 1" in out
    assert "Log details" not in out

    # Empty string level behaves like no level
    assert "Log details" not in capture(display_log_counts, counts, logs, "")

    # Details for a level, any case
    out = capture(display_log_counts, counts, logs, "error")
    assert "Log details for level 'ERROR':" in out
    assert "2024-01-22 09:00:45 - Database connection failed." in out
    assert "2024-01-22 11:30:15 - Backup process failed." in out
    assert "User logged in" not in out

    # Unknown level -> warning and "no matching logs"
    out = capture(display_log_counts, counts, logs, "critical")
    assert "[Warning]" in out
    assert "No matching logs found" in out

    # --- load_logs + main (real temporary files) ---

    with tempfile.TemporaryDirectory() as tmp:
        # Normal file
        sample_path = write_file(tmp, "sample.log", sample.encode("utf-8"))
        assert len(load_logs(sample_path)) == 10

        # Blank lines, surrounding whitespace and Windows line endings
        messy = (
            "\n  \n2024-01-22 08:30:01 INFO ok\r\n\n\t2024-01-22 09:00:00 DEBUG x  \n"
        )
        messy_logs = load_logs(write_file(tmp, "messy.log", messy.encode()))
        assert len(messy_logs) == 2
        assert messy_logs[0]["message"] == "ok"  # no trailing "\r"
        assert messy_logs[1]["date_time"] == "2024-01-22 09:00:00"

        # No newline at the end of the file
        content = b"2024-01-22 08:30:01 INFO last"
        path = write_file(tmp, "no_newline.log", content)
        assert load_logs(path)[0]["message"] == "last"

        # Non-ASCII text in UTF-8
        text = "2024-01-22 08:30:01 INFO Привіт, світ"
        path = write_file(tmp, "utf8.log", text.encode("utf-8"))
        assert load_logs(path)[0]["message"] == "Привіт, світ"

        # main: happy path with and without level
        code, out = run_main(sample_path)
        assert code == 0 and "ERROR            | 2" in out
        code, out = run_main(sample_path, "debug")
        assert code == 0 and "Log details for level 'DEBUG':" in out

        # main: no arguments -> exit 1
        code, _ = run_main()
        assert code == 1

        # main: file does not exist
        code, _ = run_main(os.path.join(tmp, "missing.log"))
        assert code == 1

        # main: empty and whitespace-only files -> exit 0
        for name, content in [("empty.log", b""), ("blank.log", b"\n \n\t\n")]:
            code, _ = run_main(write_file(tmp, name, content))
            assert code == 0, name

        # main: file is not UTF-8
        code, _ = run_main(write_file(tmp, "bad.log", b"\xff\xfe\x00bad"))
        assert code == 1

        # main: path is a directory -> handled, exit 1
        code, _ = run_main(tmp)
        assert code == 1

        # main: no read permission (skipped for root, who can read anything)
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            locked = write_file(tmp, "locked.log", sample.encode("utf-8"))
            os.chmod(locked, 0)
            try:
                code, _ = run_main(locked)
                assert code == 1
            finally:
                os.chmod(locked, 0o644)

    print("All asserts passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        run_tests()
    else:
        main()
