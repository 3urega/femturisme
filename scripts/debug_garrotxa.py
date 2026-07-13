import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.db.connection import get_mysql_connection

app = create_app()
with app.app_context():
    conn = get_mysql_connection()
    cur = conn.cursor()

    queries = [
        ("actiu=1", "SELECT COUNT(*) c FROM establiment_general WHERE actiu=1"),
        ("sense_fitxa=0", "SELECT COUNT(*) c FROM establiment_general WHERE actiu=1 AND sense_fitxa=0"),
        ("amb contingut ca", """
            SELECT COUNT(DISTINCT eg.id) c
            FROM establiment_general eg
            INNER JOIN establiment_continguts ec ON ec.id_establiment=eg.id AND ec.idioma='ca'
            WHERE eg.actiu=1 AND eg.sense_fitxa=0
        """),
        ("passa SQL completa", """
            SELECT COUNT(DISTINCT eg.id) c
            FROM establiment_general eg
            INNER JOIN establiment_continguts ec ON ec.id_establiment=eg.id AND ec.idioma='ca'
            WHERE eg.actiu=1 AND (eg.data_baixa IS NULL OR eg.data_baixa < '1000-01-01')
              AND eg.sense_fitxa=0
        """),
    ]
    for label, sql in queries:
        cur.execute(sql)
        print(label, cur.fetchone()["c"])

    cur.execute(
        """
        SELECT eg.nom, pg.poble, pc.comarca, eg.actiu, eg.sense_fitxa
        FROM establiment_general eg
        LEFT JOIN poble_general pg ON pg.id=eg.id_poble
        LEFT JOIN poble_comarques pc ON pc.id=pg.id_comarca
        WHERE eg.actiu=1
        LIMIT 5
        """
    )
    print("actius sample:", cur.fetchall())

    for domain, table, active_col in [
        ("rutes", "ruta_general", "actiu"),
        ("agenda", "agenda_general", "activa"),
    ]:
        cur.execute(f"SELECT COUNT(*) c FROM {table} WHERE {active_col}=1")
        print(f"{domain} actius:", cur.fetchone()["c"])

    conn.close()
