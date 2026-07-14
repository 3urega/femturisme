"""Unit tests for app.services.user_language."""
from __future__ import annotations

from app.services.user_language import detect_user_language, language_label


def test_detect_catalan():
    assert detect_user_language("Quines rutes hi ha a l'Empordà?") == 'ca'
    assert detect_user_language('Recomaneu-me una ruta de senderisme fàcil.') == 'ca'


def test_detect_spanish():
    assert detect_user_language('¿Qué rutas hay en el Empordà?') == 'es'
    assert detect_user_language('Recomiéndame restaurantes en Girona.') == 'es'


def test_detect_english():
    assert detect_user_language('What routes are there in Empordà?') == 'en'
    assert detect_user_language('Can you recommend hotels in Barcelona?') == 'en'


def test_detect_french():
    assert detect_user_language('Quelles randonnées y a-t-il en Catalogne?') == 'fr'
    assert detect_user_language('Où dormir dans les Pyrénées?') == 'fr'


def test_detect_empty_defaults_catalan():
    assert detect_user_language('') == 'ca'
    assert detect_user_language('   ') == 'ca'


def test_language_label():
    assert language_label('fr') == 'francès'
    assert language_label('unknown') == 'català'
