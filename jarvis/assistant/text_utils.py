import re


COMMAND_START_WORDS = {
    "add",
    "ask",
    "battery",
    "change",
    "clear",
    "date",
    "delete",
    "exit",
    "goodbye",
    "google",
    "jarvis",
    "lock",
    "mute",
    "open",
    "quit",
    "read",
    "reboot",
    "restart",
    "search",
    "set",
    "shutdown",
    "stop",
    "take",
    "time",
    "volume",
    "what",
    "write",
    "youtube",
}


def normalize_command_text(command):
    """
    Normalize recognized speech without rewriting normal sentences.

    This mainly collapses repeated full command phrases caused by speech
    recognition echo, such as "open notepad open notepad open notepad".
    """

    if not command:
        return ""

    cleaned = re.sub(r"\s+", " ", command).strip().lower()

    if not cleaned:
        return ""

    return _collapse_repeated_full_command(cleaned)


def _collapse_repeated_full_command(command):
    tokens = command.split()

    if len(tokens) < 2:
        return command

    for phrase_length in range(1, (len(tokens) // 2) + 1):
        if len(tokens) % phrase_length != 0:
            continue

        phrase = tokens[:phrase_length]

        if phrase[0] not in COMMAND_START_WORDS:
            continue

        repeated = phrase * (len(tokens) // phrase_length)

        if repeated == tokens:
            return " ".join(phrase)

    return command
