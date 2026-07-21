"""SQL integration tests — geo_radius origin resolution."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_resolve_origin_coordinates_calella(app):
    geo_radius = pytest.importorskip('app.db.geo_radius')
    with app.app_context():
        origin = geo_radius.resolve_origin_coordinates('Calella')

    if origin is None:
        pytest.skip('Calella coordinates not available in staging MySQL')

    assert -90 <= origin.lat <= 90
    assert -180 <= origin.lng <= 180
    assert origin.source in {'poble_general', 'generic_ubicacions'}


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_haversine_predicate_runs_on_experiences_coords(app):
    geo_radius = pytest.importorskip('app.db.geo_radius')
    with app.app_context():
        origin = geo_radius.resolve_origin_coordinates('Calella')
        if origin is None:
            pytest.skip('Calella coordinates not available in staging MySQL')

        clause, params = geo_radius.build_radius_filter(
            origin,
            lat_expr="COALESCE(NULLIF(eg.latitud, ''), pg.latitud)",
            lng_expr="COALESCE(NULLIF(eg.longitud, ''), pg.longitud)",
            max_km=50,
        )

        from app.db.connection import get_mysql_connection

        sql = f"""
            SELECT COUNT(*) AS total
            FROM oferta_general og
            LEFT JOIN establiment_general eg ON eg.id = og.id_establiment
            LEFT JOIN poble_general pg ON pg.id = COALESCE(NULLIF(og.id_poble, 0), eg.id_poble)
            WHERE og.estat <> 'borrador'
              AND ({clause})
        """
        conn = get_mysql_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
        finally:
            conn.close()

    assert int(row['total']) >= 0
