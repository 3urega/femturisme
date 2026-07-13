"""Unit tests for app.services.language_guard."""
from __future__ import annotations

from app.services.language_guard import (
    is_catalan_user_message,
    polish_catalan_reply,
    polish_reply_for_user,
)


def test_is_catalan_user_message_detects_catalan():
    assert is_catalan_user_message('Recomaneu-me una ruta de senderisme fàcil en família.') is True


def test_is_catalan_user_message_spanish_false():
    assert is_catalan_user_message('Recomiéndame una ruta de senderismo fácil en familia.') is False


def test_polish_catalan_reply_fixes_dime_ho():
    text = (
        'Si vols una altra proposta per una zona concreta, '
        'amb característiques més específiques, dime-ho!'
    )
    assert polish_catalan_reply(text) == (
        'Si vols una altra proposta per una zona concreta, '
        "amb característiques més específiques, digues-m'ho!"
    )


def test_polish_reply_for_user_only_when_user_catalan():
    reply = 'Si vols més detalls, dime-ho.'
    assert polish_reply_for_user(
        'Recomaneu-me una ruta de senderisme fàcil en família.',
        reply,
    ) == "Si vols més detalls, digues-m'ho."
    assert polish_reply_for_user(
        'Recomiéndame una ruta de senderismo.',
        reply,
    ) == reply
