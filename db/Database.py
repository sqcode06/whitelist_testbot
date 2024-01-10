import logging
import sqlite3

from db import utils


class Column:
    def __init__(self, name: str, col_type: any, is_primary_key: bool):
        self._name = name
        self._col_type = col_type
        self._is_primary_key = is_primary_key

    def __str__(self):
        string = f"{self._name} {utils.convert_type(self._col_type)}"
        if self._is_primary_key:
            string += " PRIMARY KEY"
        return string

    @property
    def name(self) -> str:
        return self._name

    @property
    def col_type(self) -> any:
        return self._col_type


class Table:
    def __init__(self, name: str, cols: tuple[Column, ...]) -> None:
        self._name = name
        self._cols = cols
        self._cursor = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def cols(self) -> tuple[Column, ...]:
        return self._cols

    @property
    def cursor(self) -> sqlite3.Cursor:
        return self._cursor

    @cursor.setter
    def cursor(self, cursor: sqlite3) -> None:
        self._cursor = cursor


class Database:
    def __init__(self, filename: str) -> None:
        self._conn = sqlite3.connect(filename)
        self._cursor = self._conn.cursor()

    def add_table(self, table) -> None:
        table.cursor = self._cursor
        self._cursor.execute(f"CREATE TABLE IF NOT EXISTS {table.name}\n({', '.join(str(col) for col in table.cols)})")

    def close(self) -> None:
        self._conn.close()
        del self._cursor

    def insert(self, table: Table, data: dict[Column, any]) -> bool:
        if not utils.check_value_dict(data):
            logging.error(f"Invalid insertion data: {data}")
            return False
        query = f"INSERT INTO {table.name} ("
        value_tuple = tuple(data.values())
        query += f"{', '.join(col.name for col in data.keys())}) VALUES ({', '.join(['?'] * len(data))})"

        self._cursor.execute(query, value_tuple)
        self._conn.commit()
        return True

    def query(self, table: Table, target_cols: tuple[Column, ...], condition: dict[Column, any], operator: list,
              is_sum_query: bool) -> list:
        if is_sum_query and len(target_cols) > 1:
            logging.error(f"Cannot sum over multiple columns: {target_cols}")
            return []
        if is_sum_query and target_cols[0].col_type is not int:
            logging.error(f"Cannot sum over non-integer column: {target_cols[0]}")
        if condition == utils.NO_CONDITION:
            if is_sum_query:
                query = f"SELECT SUM({target_cols[0].name}) FROM {table.name};"
            else:
                query = f"SELECT {', '.join(col.name for col in target_cols)} FROM {table.name}"
            self._cursor.execute(query)
        else:
            if not utils.check_value_dict(condition):
                logging.error(f"Invalid query condition: {condition}")
                return []
            condition_string = '\nAND '.join(
                f"{col.name} {operator[list(condition.keys()).index(col)]} ?" for col, val in condition.items())
            if is_sum_query:
                query = f"SELECT SUM({target_cols[0].name}) FROM {table.name} WHERE {condition_string};"
            else:
                query = f"SELECT {', '.join(col.name for col in target_cols)} FROM {table.name} WHERE {condition_string};"
            self._cursor.execute(query, tuple(condition.values()))

        rows = self._cursor.fetchall()
        return rows

    def update(self, table: Table, data: dict[Column, any], condition: dict[Column, any]) -> bool:
        if not utils.check_value_dict(condition):
            logging.error(f"Invalid update condition: {condition}")
            return False
        data_string = ' '.join(f"{col.name} = ?" for col, val in data.items())
        condition_string = '\nAND '.join(f"{col.name} = ?" for col, val in condition.items())
        query = f"UPDATE {table.name} SET {data_string} WHERE {condition_string};"

        self._cursor.execute(query, (tuple(data.values()) + tuple(condition.values())))
        self._conn.commit()
        return True

    def count_rows(self, table: Table):
        query = f"SELECT COUNT(*) FROM {table.name};"
        self._cursor.execute(query)
        return self._cursor.fetchall()[0]
