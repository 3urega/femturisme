"""Diagnose UAT cases with 0 results (DEV-604 manual review)."""
from __future__ import annotations

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.db.connection import get_mysql_connection
from app.db.repositories import articles, experiences

LLM_INPUTS = {
    'UAT-ART-01': {'topic': 'Parc Natural del Cadí', 'lang': 'ca'},
    'UAT-ART-02': {'topic': 'enoturisme', 'destination': 'Catalunya', 'lang': 'ca'},
    'UAT-EXP-02': {'destination': 'Garrotxa', 'category': 'Natura', 'lang': 'ca'},
}


def _total(data: dict) -> int:
    try:
        return int(data.get('total', 0) or 0)
    except (TypeError, ValueError):
        return 0


def run_repo_checks() -> None:
    print('=== REPOSITORY CHECKS ===\n')
    for case_id, params in LLM_INPUTS.items():
        print(f'--- {case_id} (LLM input) ---')
        if 'topic' in params or case_id.startswith('UAT-ART'):
            data = articles.search(**{k: v for k, v in params.items() if k != 'category'})
            print(f'  articles.search({params}) -> total={_total(data)}')
        else:
            data = experiences.search(
                destination=params['destination'],
                category=params.get('category'),
                lang=params.get('lang', 'ca'),
            )
            print(f'  experiences.search(...) -> total={_total(data)}')

    print('\n--- UAT-ART-01 variants ---')
    for label, kwargs in [
        ('topic=Cadí', {'topic': 'Cadí'}),
        ('query=Cadí', {'query': 'Cadí'}),
        ('query=Moixeró', {'query': 'Moixeró'}),
        ('topic=parc natural', {'topic': 'parc natural'}),
    ]:
        t = _total(articles.search(**kwargs))
        print(f'  {label} -> total={t}')

    print('\n--- UAT-ART-02 variants ---')
    for label, kwargs in [
        ('topic=enoturisme only', {'topic': 'enoturisme'}),
        ('query=enoturisme only', {'query': 'enoturisme'}),
        ('destination=Catalunya only', {'destination': 'Catalunya'}),
    ]:
        t = _total(articles.search(**kwargs))
        print(f'  {label} -> total={t}')

    print('\n--- UAT-EXP-02 variants ---')
    for label, kwargs in [
        ('Garrotxa no category', {'destination': 'Garrotxa'}),
        ('Garrotxa category=Activitats', {'destination': 'Garrotxa', 'category': 'Activitats'}),
        ('Garrotxa category=Natura (LLM)', {'destination': 'Garrotxa', 'category': 'Natura'}),
    ]:
        t = _total(experiences.search(**kwargs))
        print(f'  {label} -> total={t}')


def run_sql_counts() -> None:
    print('\n=== RAW SQL COUNTS ===\n')
    conn = get_mysql_connection()
    cur = conn.cursor()

    queries = [
        (
            'articles actives',
            """
            SELECT COUNT(*) c FROM noticia_general ng
            WHERE ng.actiu=1 AND (ng.permanent=1 OR ng.data_caducitat >= CURDATE())
            """,
        ),
        (
            'articles titol/cos LIKE %Cadi%',
            """
            SELECT COUNT(DISTINCT ng.id) c
            FROM noticia_general ng
            INNER JOIN noticia_continguts nc ON nc.id_noticia=ng.id AND nc.idioma='ca'
            WHERE ng.actiu=1 AND (ng.permanent=1 OR ng.data_caducitat >= CURDATE())
              AND (nc.titol LIKE '%Cadi%' OR nc.cos LIKE '%Cadi%'
                   OR nc.titol LIKE '%Cadí%' OR nc.cos LIKE '%Cadí%')
            """,
        ),
        (
            'articles LIKE %enoturisme%',
            """
            SELECT COUNT(DISTINCT ng.id) c
            FROM noticia_general ng
            INNER JOIN noticia_continguts nc ON nc.id_noticia=ng.id AND nc.idioma='ca'
            WHERE ng.actiu=1 AND (ng.permanent=1 OR ng.data_caducitat >= CURDATE())
              AND (nc.titol LIKE '%enoturisme%' OR nc.cos LIKE '%enoturisme%')
            """,
        ),
        (
            'articles enoturisme + poble/comarca LIKE Catalunya',
            """
            SELECT COUNT(DISTINCT ng.id) c
            FROM noticia_general ng
            INNER JOIN noticia_continguts nc ON nc.id_noticia=ng.id AND nc.idioma='ca'
            LEFT JOIN noticia_pobles np ON np.id_noticia=ng.id
            LEFT JOIN poble_general pg ON pg.id=np.id_poble
            LEFT JOIN poble_comarques pc ON pc.id=pg.id_comarca
            WHERE ng.actiu=1 AND (ng.permanent=1 OR ng.data_caducitat >= CURDATE())
              AND (nc.titol LIKE '%enoturisme%' OR nc.cos LIKE '%enoturisme%')
              AND (pg.poble LIKE '%Catalunya%' OR pc.comarca LIKE '%Catalunya%')
            """,
        ),
        (
            'ofertes vigents Garrotxa comarca',
            """
            SELECT COUNT(DISTINCT og.id) c
            FROM oferta_general og
            INNER JOIN oferta_continguts oc ON oc.id_oferta=og.id AND oc.idioma='ca'
            LEFT JOIN establiment_general eg ON eg.id=og.id_establiment
            LEFT JOIN poble_general pg ON pg.id=COALESCE(NULLIF(og.id_poble,0), eg.id_poble)
            LEFT JOIN poble_comarques pc ON pc.id=pg.id_comarca
            WHERE og.estat <> 'borrador'
              AND og.data_inicial <= NOW()
              AND (og.data_final IS NULL OR og.data_final < '1000-01-01' OR og.data_final >= NOW())
              AND pc.comarca LIKE '%Garrotxa%'
            """,
        ),
        (
            'ofertes Garrotxa + categoria LIKE %natura%',
            """
            SELECT COUNT(DISTINCT og.id) c
            FROM oferta_general og
            INNER JOIN oferta_continguts oc ON oc.id_oferta=og.id AND oc.idioma='ca'
            LEFT JOIN establiment_general eg ON eg.id=og.id_establiment
            LEFT JOIN poble_general pg ON pg.id=COALESCE(NULLIF(og.id_poble,0), eg.id_poble)
            LEFT JOIN poble_comarques pc ON pc.id=pg.id_comarca
            LEFT JOIN oferta_categories ocat ON ocat.id_oferta=og.id
            LEFT JOIN generic_categoria_oferta gco ON gco.id=ocat.id_categoria
            WHERE og.estat <> 'borrador'
              AND og.data_inicial <= NOW()
              AND (og.data_final IS NULL OR og.data_final < '1000-01-01' OR og.data_final >= NOW())
              AND pc.comarca LIKE '%Garrotxa%'
              AND gco.categoria_ca LIKE '%natura%'
            """,
        ),
        (
            'distinct experience categories',
            """
            SELECT DISTINCT gco.categoria_ca
            FROM generic_categoria_oferta gco
            ORDER BY 1
            """,
        ),
    ]

    for label, sql in queries:
        cur.execute(sql)
        rows = cur.fetchall()
        if label == 'distinct experience categories':
            cats = [r.get('categoria_ca') for r in rows if r.get('categoria_ca')]
            print(f'  {label}: {cats}')
        else:
            print(f'  {label}: {rows[0]["c"]}')

    conn.close()


def main() -> None:
    app = create_app()
    with app.app_context():
        run_repo_checks()
        run_sql_counts()


if __name__ == '__main__':
    main()
