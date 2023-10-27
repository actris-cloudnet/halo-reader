import sqlite3
from collections import defaultdict


def adapt_list(obj: list) -> str:
    return ";".join(obj)


def convert_tags(obj: bytes) -> list:
    return obj.split(b";")


sqlite3.register_adapter(list, adapt_list)
sqlite3.register_converter("tags", convert_tags)


class Database:
    def __init__(self) -> None:
        self.con = sqlite3.connect("halodata.db")

    def sites(self) -> list:
        cur = self.con.cursor()
        cur.execute("""SELECT DISTINCT "siteId" from raw ORDER BY "siteId" """)
        return [s for s, in cur.fetchall()]

    def summary(self) -> dict:
        cur = self.con.cursor()
        cur.execute(
            """
                    SELECT
                        "siteId",
                        strftime('%Y', "measurementDate") as year,
                        sum(size) as tsize from raw
                        GROUP BY siteId, year
                    """
        )
        res = cur.fetchall()
        data: dict = defaultdict(dict)
        for site, year, total_size in res:
            data[site][int(year)] = total_size
        return data
