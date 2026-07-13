"""Debug establishment filters without actiu."""
import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.db.connection import get_mysql_connection
from app.db.repositories import establishments

app = create_app()
with app.app_context():
    conn = get_mysql_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) c FROM establiment_general")
    print("total rows:", cur.fetchone()["c"])

    cur.execute(
        """
        SELECT COUNT(*) c FROM establiment_general
        WHERE (data_baixa IS NULL OR data_baixa < '1000-01-01')
          AND sense_fitxa = 0
        """
    )
    print("no baixa + sense_fitxa=0 (sin actiu):", cur.fetchone()["c"])

    cur.execute(
        """
        SELECT COUNT(DISTINCT eg.id) c
        FROM establiment_general eg
        INNER JOIN establiment_continguts ec
            ON ec.id_establiment = eg.id AND ec.idioma = 'ca'
        WHERE (eg.data_baixa IS NULL OR eg.data_baixa < '1000-01-01')
          AND eg.sense_fitxa = 0
        """
    )
    print("con contingut ca (sin actiu):", cur.fetchone()["c"])

    cur.execute(
        """
        SELECT eg.id, eg.nom, eg.actiu, eg.data_baixa, eg.sense_fitxa, pg.poble, pc.comarca
        FROM establiment_general eg
        LEFT JOIN poble_general pg ON pg.id = eg.id_poble
        LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
        WHERE (eg.data_baixa IS NULL OR eg.data_baixa < '1000-01-01')
          AND eg.sense_fitxa = 0
        LIMIT 5
        """
    )
    print("sample sin actiu:", cur.fetchall())

    cur.execute(
        """
        SELECT COUNT(*) c FROM establiment_general
        WHERE data_baixa IS NOT NULL AND data_baixa >= '1000-01-01'
        """
    )
    print("explicitament de baixa:", cur.fetchone()["c"])

    data = establishments.search(destination="Garrotxa", type="restaurant")
    print("search Garrotxa restaurant total:", data["total"])
    if data["results"]:
        print("first:", data["results"][0]["title"], data["results"][0]["url"])

    conn.close()
