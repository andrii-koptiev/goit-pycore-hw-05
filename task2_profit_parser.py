"""Sum income amounts found in text, using a generator.

Practice task for understanding generators in Python.
"""

import re
from typing import Callable, Iterator

NUMBER_PATTERN = re.compile(r"(?<!\S)\d+(?:\.\d+)?(?!\S)")


def generator_numbers(text: str) -> Iterator[float]:
    """Yield real numbers from text that are separated by whitespace.

    Args:
        text: Text to search for numbers.

    Yields:
        Each number as a float, in order of appearance.
    """
    matches: Iterator[re.Match[str]] = NUMBER_PATTERN.finditer(text)
    for match in matches:
        yield float(match.group())


def sum_profit(text: str, func: Callable[[str], Iterator[float]]) -> float:
    """Calculate the total income in text.

    Args:
        text: Text containing income amounts.
        func: Function that yields the numbers from text.

    Returns:
        Sum of all numbers found.
    """
    return sum(func(text))


# Test cases
if __name__ == "__main__":
    import inspect
    import math

    text = "Загальний дохід працівника складається з декількох частин: 1000.01 як основний дохід, доповнений додатковими надходженнями 27.45 і 324.00 доларів."

    # Example from the task
    assert math.isclose(sum_profit(text, generator_numbers), 1351.46)

    # generator_numbers must be a generator (uses yield)
    assert inspect.isgenerator(generator_numbers(text))

    # It yields the numbers as floats, in order
    assert list(generator_numbers(text)) == [1000.01, 27.45, 324.0]

    # Integers count as real numbers too
    assert list(generator_numbers("got 100 and 25 today")) == [100.0, 25.0]

    # A number at the very start or end of the text
    assert list(generator_numbers("100 at start")) == [100.0]
    assert list(generator_numbers("at end 7.5")) == [7.5]

    # Any whitespace counts as a separator (tab, newline)
    assert list(generator_numbers("a\t3.5\nb 2")) == [3.5, 2.0]

    # Not separated by spaces on both sides -> not a number
    assert list(generator_numbers("abc123 12abc 5, (5) .5 5. 1.2.3")) == []

    # Negative values are not income
    assert list(generator_numbers("loss -30 here")) == []

    # No numbers / empty text -> sum is 0
    assert sum_profit("no numbers here", generator_numbers) == 0
    assert sum_profit("", generator_numbers) == 0

    # Sum of many small values is still accurate
    assert math.isclose(sum_profit(" ".join(["0.1"] * 10), generator_numbers), 1.0)

    print("All asserts passed")
