import shlex

from config import SYSTEM_PROMPT
from llm import ask

from conversations import (
    load_active_history,
    save_active_history,
    save_conversation,
    load_conversation,
    list_conversations,
    rename_conversation,
    new_history,
)


def show_history(history):
    messages = [
        message
        for message in history
        if message.get("role") != "system"
    ]

    if not messages:
        print("Historique vide.")
        return

    print("\n--- Historique ---")

    for i, message in enumerate(messages, start=1):
        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            name = "Toi"
        else:
            name = "Mistral"

        print(f"\n{i}. {name} > {content}")

    print("\n------------------")


# Chargement de la conversation active
history = load_active_history(SYSTEM_PROMPT)


print("LocalChat lancé.")
print(
    "Commandes : "
    "/history, "
    '/save "nom", '
    "/list, "
    '/load "nom", '
    '/rename "ancien nom" "nouveau nom", '
    "/new, "
    "/clear, "
    "/quit"
)


while True:
    question = input("\nToi > ").strip()

    if not question:
        continue

    # -------------------------
    # QUITTER
    # -------------------------

    if question == "/quit":
        print("À bientôt 👋")
        break

    # -------------------------
    # HISTORIQUE
    # -------------------------

    if question == "/history":
        show_history(history)
        continue

    # -------------------------
    # LISTE DES CONVERSATIONS
    # -------------------------

    if question == "/list":
        conversations = list_conversations()

        if not conversations:
            print("Aucune conversation sauvegardée.")
        else:
            print("\nConversations sauvegardées :")

            for name in conversations:
                print(f"- {name}")

        continue

    # -------------------------
    # NOUVELLE CONVERSATION
    # -------------------------

    if question == "/new":
        history = new_history(SYSTEM_PROMPT)

        save_active_history(history)

        print("Nouvelle conversation créée.")
        continue

    # -------------------------
    # EFFACER L'HISTORIQUE
    # -------------------------

    if question == "/clear":
        history = new_history(SYSTEM_PROMPT)

        save_active_history(history)

        print("Historique effacé.")
        continue

    # -------------------------
    # SAUVEGARDER
    # -------------------------

    if question.startswith("/save"):
        try:
            parts = shlex.split(question)
        except ValueError:
            print(
                "Erreur : vérifie que tes guillemets "
                "sont bien fermés."
            )
            continue

        if len(parts) != 2:
            print(
                'Utilisation : /save "nom de la conversation"'
            )
            continue

        name = parts[1]

        success, error = save_conversation(
            history,
            name
        )

        if success:
            print(
                f'Conversation "{name}" sauvegardée.'
            )
        else:
            print(f"Erreur : {error}")

        continue

    # -------------------------
    # CHARGER
    # -------------------------

    if question.startswith("/load"):
        try:
            parts = shlex.split(question)
        except ValueError:
            print(
                "Erreur : vérifie que tes guillemets "
                "sont bien fermés."
            )
            continue

        if len(parts) != 2:
            print(
                'Utilisation : /load "nom de la conversation"'
            )
            continue

        name = parts[1]

        loaded_history, error = load_conversation(
            name,
            SYSTEM_PROMPT
        )

        if loaded_history is None:
            print(f"Erreur : {error}")
        else:
            history = loaded_history

            save_active_history(history)

            print(
                f'Conversation "{name}" chargée.'
            )

        continue

    # -------------------------
    # RENOMMER
    # -------------------------

    if question.startswith("/rename"):
        try:
            parts = shlex.split(question)
        except ValueError:
            print(
                "Erreur : vérifie que tes guillemets "
                "sont bien fermés."
            )
            continue

        if len(parts) != 3:
            print(
                'Utilisation : '
                '/rename "ancien nom" "nouveau nom"'
            )
            continue

        old_name = parts[1]
        new_name = parts[2]

        success, error = rename_conversation(
            old_name,
            new_name
        )

        if success:
            print(
                f'Conversation "{old_name}" '
                f'renommée en "{new_name}".'
            )
        else:
            print(f"Erreur : {error}")

        continue

    # -------------------------
    # MESSAGE NORMAL
    # -------------------------

    history.append(
        {
            "role": "user",
            "content": question
        }
    )

    answer = ask(history)

    if answer is None:
        # On retire le message utilisateur,
        # puisque Mistral n'a pas répondu.
        history.pop()

        continue

    history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    save_active_history(history)