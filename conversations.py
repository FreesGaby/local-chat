import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
CONVERSATIONS_DIR = BASE_DIR / "conversations"
ACTIVE_HISTORY_FILE = BASE_DIR / "history.json"


def validate_conversation_name(name):
    name = name.strip()

    if not name:
        return False, "Le nom ne peut pas être vide."

    if "/" in name or "\\" in name:
        return False, "Le nom ne peut pas contenir / ou \\."

    if ".." in name:
        return False, "Le nom ne peut pas contenir '..'."

    if "\0" in name:
        return False, "Le nom contient un caractère invalide."

    if len(name) > 100:
        return False, "Le nom est trop long."

    return True, None


def conversation_path(name):
    valid, error = validate_conversation_name(name)

    if not valid:
        raise ValueError(error)

    return CONVERSATIONS_DIR / f"{name}.json"


def normalize_history(history, system_prompt):
    """
    Remplace l'ancien system prompt par le system prompt actuel.
    """

    messages = [
        message
        for message in history
        if message.get("role") != "system"
    ]

    return [
        system_prompt.copy(),
        *messages
    ]


def new_history(system_prompt):
    return [system_prompt.copy()]


def save_active_history(history):
    with ACTIVE_HISTORY_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )


def load_active_history(system_prompt):
    if not ACTIVE_HISTORY_FILE.exists():
        return new_history(system_prompt)

    try:
        with ACTIVE_HISTORY_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            history = json.load(file)

        return normalize_history(
            history,
            system_prompt
        )

    except (json.JSONDecodeError, OSError):
        return new_history(system_prompt)


def save_conversation(history, name):
    valid, error = validate_conversation_name(name)

    if not valid:
        return False, error

    CONVERSATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = conversation_path(name)

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )

    return True, None


def load_conversation(name, system_prompt):
    valid, error = validate_conversation_name(name)

    if not valid:
        return None, error

    path = conversation_path(name)

    if not path.exists():
        return None, f'Conversation "{name}" introuvable.'

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            history = json.load(file)

        history = normalize_history(
            history,
            system_prompt
        )

        return history, None

    except json.JSONDecodeError:
        return None, f'La conversation "{name}" est corrompue.'


def list_conversations():
    if not CONVERSATIONS_DIR.exists():
        return []

    conversations = []

    for path in CONVERSATIONS_DIR.glob("*.json"):
        conversations.append(path.stem)

    return sorted(
        conversations,
        key=str.lower
    )


def rename_conversation(old_name, new_name):
    old_valid, old_error = validate_conversation_name(old_name)

    if not old_valid:
        return False, old_error

    new_valid, new_error = validate_conversation_name(new_name)

    if not new_valid:
        return False, new_error

    old_path = conversation_path(old_name)
    new_path = conversation_path(new_name)

    if not old_path.exists():
        return False, f'Conversation "{old_name}" introuvable.'

    if new_path.exists():
        return False, f'Une conversation "{new_name}" existe déjà.'

    old_path.rename(new_path)

    return True, None