from peewee import Field


class MultiField(Field):
    field_type = 'text'

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        if value is None:
            return None
        return value.split(',')
