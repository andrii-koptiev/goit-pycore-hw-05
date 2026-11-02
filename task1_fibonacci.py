"""Fibonacci numbers with caching, implemented as a closure.

Practice task for understanding closures in Python: the inner function
keeps access to a cache dictionary from its enclosing scope.
"""

from typing import Callable


def caching_fibonacci() -> Callable[[int], int]:
    """Create a function that computes Fibonacci numbers with caching.

    The cache is stored in the closure, so it is shared between calls
    of the returned function and kept for its whole lifetime.

    Returns:
        A function that takes n and returns the n-th Fibonacci number.
    """
    cache: dict[int, int] = {}

    def fibonacci(n: int) -> int:
        """Return the n-th Fibonacci number, using the cache if possible.

        Args:
            n: Index in the Fibonacci sequence. Values <= 0 give 0.

        Returns:
            The n-th Fibonacci number.
        """
        if n in cache:
            return cache[n]

        if n <= 0:
            return 0
        if n == 1:
            return 1

        cache[n] = fibonacci(n - 1) + fibonacci(n - 2)

        return cache[n]

    return fibonacci


"""Test cases"""
if __name__ == "__main__":
    # Examples from the task
    fib = caching_fibonacci()
    assert fib(10) == 55
    assert fib(15) == 610

    # Base cases
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(2) == 1

    # Negative input is treated as 0
    assert fib(-1) == 0
    assert fib(-100) == 0

    # Results match an iterative reference implementation
    a, b = 0, 1
    for i in range(100):
        assert fib(i) == a, f"fib({i}) mismatch"
        a, b = b, a + b

    # Repeated call returns the same (cached) value
    assert fib(30) == fib(30) == 832040

    # Value is actually stored in the closure cache
    assert fib.__closure__ is not None
    cache = fib.__closure__[0].cell_contents
    assert isinstance(cache, dict) and cache[30] == 832040

    # Each caching_fibonacci() call creates its own independent cache
    other = caching_fibonacci()
    assert other.__closure__ is not None
    assert other.__closure__[0].cell_contents is not cache
    assert other(20) == 6765

    # Big numbers work (Python ints have no overflow)
    assert fib(100) == 354224848179261915075

    print("All asserts passed")
