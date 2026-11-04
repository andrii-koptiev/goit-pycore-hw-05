"""Console assistant bot that stores contacts in memory.

User input errors are handled by the input_error decorator, so a wrong command
prints a message and the bot keeps running.

Contacts are stored as {case-folded name: (name as typed, phone)}, so Bob, bob
and BOB are the same contact, and "all" still shows the original spelling.

Usage: python3 task4_bot.py
Tests: python3 task4_bot.py --test
"""

import sys
from functools import wraps
from typing import Any, Callable

Args = list[str]
Contacts = dict[str, tuple[str, str]]

COMMANDS: list[tuple[str, str]] = [
    ("hello", "greet the bot"),
    ("add <name> <phone>", "save a new contact"),
    ("change <name> <phone>", "update the phone of an existing contact"),
    ("phone <name>", "show the phone of a contact"),
    ("all", "show all contacts"),
    ("help", "show this list of commands"),
    ("close | exit", "leave the bot"),
]

PROMPT = "Enter a command: "
MISSING_ARGUMENT_MESSAGE = "Enter the argument for the command"
NOT_FOUND_MESSAGE = "Contact not found."


def input_error(func: Callable[..., str]) -> Callable[..., str]:
    """Decorate a command handler to turn input errors into messages.

    ValueError and IndexError mean the arguments are wrong or missing.
    KeyError means the contact does not exist. The message is returned, not
    printed, so the bot shows it like any other reply and keeps running.

    Args:
        func: Command handler that returns the reply for the user.

    Returns:
        Wrapped handler with the same name and docstring as func.
    """

    @wraps(func)
    def inner(*args: Any, **kwargs: Any) -> str:
        """Call func and return a message if the user input was wrong."""
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError):
            return MISSING_ARGUMENT_MESSAGE
        except KeyError:
            return NOT_FOUND_MESSAGE

    return inner


def parse_input(user_input: str) -> tuple[str, Args]:
    """Split a line of user input into a command and its arguments.

    Args:
        user_input: Raw line typed by the user.

    Returns:
        The case-folded command and its arguments; ("", []) for a blank line.
    """
    parts = user_input.split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.casefold(), args


@input_error
def add_contact(args: Args, contacts: Contacts) -> str:
    """Save a new contact.

    Args:
        args: Exactly [name, phone]; any other length raises ValueError.
        contacts: Contact storage, changed in place.

    Returns:
        A confirmation, or a notice if the name is already taken.
    """
    name, phone = args
    normalized_name = name.casefold()
    if normalized_name in contacts:
        return "Contact already exists."

    contacts[normalized_name] = (name, phone)
    return "Contact added."


@input_error
def change_contact(args: Args, contacts: Contacts) -> str:
    """Update the phone of an existing contact, keeping its original name.

    Args:
        args: Exactly [name, phone]; any other length raises ValueError.
        contacts: Contact storage, changed in place.

    Returns:
        A confirmation. An unknown name raises KeyError.
    """
    name, phone = args
    normalized_name = name.casefold()
    original_name, _ = contacts[normalized_name]

    contacts[normalized_name] = (original_name, phone)
    return "Contact updated."


@input_error
def show_phone(args: Args, contacts: Contacts) -> str:
    """Return the phone of a contact.

    Args:
        args: The name comes first; an empty list raises IndexError.
        contacts: Contact storage.

    Returns:
        The phone number. An unknown name raises KeyError.
    """
    name = args[0]
    _, phone = contacts[name.casefold()]
    return phone


@input_error
def show_all(contacts: Contacts) -> str:
    """Return all contacts, one "name: phone" line each.

    Args:
        contacts: Contact storage.

    Returns:
        The contacts in insertion order, or a notice if there are none.
    """
    if not contacts:
        return "No contacts."
    return "\n".join(
        f"{original_name}: {phone}" for original_name, phone in contacts.values()
    )


@input_error
def show_help() -> str:
    """Return the list of available commands."""
    width = max(len(usage) for usage, _ in COMMANDS)
    lines = [f"{usage:<{width}}  {description}" for usage, description in COMMANDS]
    return "\n".join(["Available commands:", *lines])


def main() -> None:
    """Read commands from the user until "close" or "exit"."""
    contacts: Contacts = {}
    print("Welcome to the assistant bot!")

    while True:
        command, args = parse_input(input(PROMPT))

        if not command:
            continue

        if command in ("close", "exit"):
            print("Good bye! See you next time")
            break

        if command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, contacts))
        elif command == "change":
            print(change_contact(args, contacts))
        elif command == "phone":
            print(show_phone(args, contacts))
        elif command == "all":
            print(show_all(contacts))
        elif command == "help":
            print(show_help())
        else:
            print("Invalid command. Type 'help' to see the commands.")


# Test cases. Run: python3 task4_bot.py --test
def run_tests() -> None:
    """Run assert-based tests for all functions, including corner cases."""
    import builtins
    import io
    from contextlib import redirect_stdout

    def run_dialog(*lines: str) -> list[str]:
        """Run main() with the given user lines and return the printed lines."""
        answers = iter(lines)
        real_input = builtins.input
        builtins.input = lambda _prompt="": next(answers)
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                main()
        finally:
            builtins.input = real_input
        return output.getvalue().splitlines()

    # --- input_error ---

    @input_error
    def raises(error: Exception) -> str:
        """Raise the given error."""
        raise error

    assert raises(ValueError()) == MISSING_ARGUMENT_MESSAGE
    assert raises(IndexError()) == MISSING_ARGUMENT_MESSAGE
    assert raises(KeyError("Bob")) == NOT_FOUND_MESSAGE

    # Other errors are real bugs, so they are not hidden
    try:
        raises(TypeError())
    except TypeError:
        pass
    else:
        raise AssertionError("TypeError must not be caught")

    # Name and docstring of the handler are kept
    assert add_contact.__name__ == "add_contact"
    assert "Save a new contact." in str(add_contact.__doc__)

    # Every command handler is decorated
    for handler in (add_contact, change_contact, show_phone, show_all, show_help):
        assert hasattr(handler, "__wrapped__"), handler.__name__

    # --- parse_input ---

    assert parse_input("add Bob 123") == ("add", ["Bob", "123"])
    assert parse_input("  add   Bob   123 ") == ("add", ["Bob", "123"])
    assert parse_input("ADD Bob") == ("add", ["Bob"])  # args keep their case
    assert parse_input("all") == ("all", [])
    assert parse_input("") == ("", [])
    assert parse_input("   ") == ("", [])

    # --- add_contact ---

    contacts: Contacts = {}
    assert add_contact(["Bob", "123"], contacts) == "Contact added."
    assert contacts == {"bob": ("Bob", "123")}

    # Same name in any letter case changes nothing
    assert add_contact(["BOB", "999"], contacts) == "Contact already exists."
    assert contacts == {"bob": ("Bob", "123")}

    # Wrong number of arguments changes nothing
    for bad_args in ([], ["Ann"], ["Ann", "1", "2"]):
        assert add_contact(bad_args, contacts) == MISSING_ARGUMENT_MESSAGE
    assert contacts == {"bob": ("Bob", "123")}

    # --- change_contact ---

    assert change_contact(["bOb", "456"], contacts) == "Contact updated."
    assert contacts == {"bob": ("Bob", "456")}  # original spelling is kept

    assert change_contact(["Ann", "1"], contacts) == NOT_FOUND_MESSAGE
    assert "ann" not in contacts

    for bad_args in ([], ["Bob"], ["Bob", "1", "2"]):
        assert change_contact(bad_args, contacts) == MISSING_ARGUMENT_MESSAGE
    assert contacts == {"bob": ("Bob", "456")}

    # --- show_phone ---

    assert show_phone(["Bob"], contacts) == "456"
    assert show_phone(["BOB"], contacts) == "456"
    assert show_phone(["Ann"], contacts) == NOT_FOUND_MESSAGE
    assert show_phone([], contacts) == MISSING_ARGUMENT_MESSAGE

    # Without the decorator, a missing name is an IndexError
    try:
        show_phone.__wrapped__([], contacts)  # type: ignore[attr-defined]
    except IndexError:
        pass
    else:
        raise AssertionError("show_phone must raise IndexError")

    # --- show_all ---

    assert show_all({}) == "No contacts."
    assert show_all(contacts) == "Bob: 456"

    add_contact(["Ann", "789"], contacts)
    assert show_all(contacts) == "Bob: 456\nAnn: 789"  # insertion order

    # --- show_help ---

    for usage, description in COMMANDS:
        assert usage in show_help()
        assert description in show_help()

    # --- main ---

    # The dialog from the task
    assert run_dialog(
        "add", "add Bob", "add Jime 0501234356", "phone", "all", "exit"
    ) == [
        "Welcome to the assistant bot!",
        MISSING_ARGUMENT_MESSAGE,
        MISSING_ARGUMENT_MESSAGE,
        "Contact added.",
        MISSING_ARGUMENT_MESSAGE,
        "Jime: 0501234356",
        "Good bye! See you next time",
    ]

    # The bot survives every kind of error and still works afterwards
    assert run_dialog(
        "phone Bob", "change Bob 1", "change", "add Bob 1", "phone bob", "close"
    )[1:-1] == [
        NOT_FOUND_MESSAGE,
        NOT_FOUND_MESSAGE,
        MISSING_ARGUMENT_MESSAGE,
        "Contact added.",
        "1",
    ]

    # Blank lines are ignored, commands are case-insensitive
    assert run_dialog("", "   ", "HeLLo", "EXIT")[1:] == [
        "How can I help you?",
        "Good bye! See you next time",
    ]

    # Unknown command
    assert "Invalid command" in run_dialog("foo", "exit")[1]

    # Help lists the commands
    assert run_dialog("help", "exit")[1] == "Available commands:"

    # Contacts do not leak between runs
    assert run_dialog("all", "exit")[1] == "No contacts."

    print("All asserts passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        run_tests()
    else:
        main()
