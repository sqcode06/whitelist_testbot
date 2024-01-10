from collections import OrderedDict

NO_CONDITION = {"No_condition": -1}
NO_OPERATOR = "="

OPERATORS = OrderedDict({
    "is": "=",
    "not": "<>",
    "greater": ">",
    "greater or is": ">=",
    "less": "<",
    "less or is": "<="
})


class Column:
    def __init__(self):
        self._name = ""
        self._col_type = None
        self._is_primary_key = False

    @property
    def col_type(self):
        return self._col_type


def check_value_dict(value_dict: dict[Column, any]) -> bool:
    for column, value in value_dict.items():
        if type(value) is not column.col_type:
            return False
    return True


def convert_type(col_type: any):
    return {int: 'INTEGER',
            str: 'VARCHAR(255)',
            bool: 'BOOLEAN'
            }[col_type]
