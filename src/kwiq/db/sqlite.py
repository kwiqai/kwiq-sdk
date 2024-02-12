from sqlite3 import Connection, Cursor

from typing import Optional, Any

from pathlib import Path

import sqlite3

from pydantic import BaseModel


class DB(BaseModel):
    name: str = "db-sqlite"

    db_path: Path
    __conn: Optional[Connection] = None
    __cursor: Optional[Cursor] = None

    @property
    def conn(self):
        if self.__conn is None:
            self.__conn = sqlite3.connect(self.db_path)

        return self.__conn

    @property
    def cursor(self):
        if self.__cursor is None:
            self.__cursor = self.conn.cursor()

        return self.__cursor

    def command(self, sql: str, parameters: Optional[tuple] = None):
        if parameters is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, parameters)
        self.conn.commit()

    def select(self, sql: str, parameters: Optional[tuple] = None) -> Any:
        if parameters is None:
            self.cursor.execute(sql)
        else:
            self.cursor.execute(sql, parameters)

        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


def test():
    command = DB(db_path='translation_cache.db')
    command.command(sql='''
    CREATE TABLE IF NOT EXISTS translations (
        original_text TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        PRIMARY KEY (original_text)
    )
    ''')

    command.command(sql='''
    INSERT INTO translations (original_text, translated_text)
        VALUES (?, ?)
        ON CONFLICT(original_text) DO UPDATE SET
        translated_text = excluded.translated_text
    ''',
                    parameters=('original1', 'translated1')
                    )

    command.close()


if __name__ == '__main__':
    test()
