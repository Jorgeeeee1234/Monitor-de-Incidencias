from datetime import date, datetime

from sqlalchemy import MetaData, Table, func, inspect, select
from sqlalchemy.orm import Session


class ViewBDService:
    def __init__(self, db: Session):
        self.db = db
        self.bind = db.get_bind()

    def _table_names(self):
        inspector = inspect(self.bind)
        return sorted(inspector.get_table_names())

    def _serialize_row(self, row: dict):
        serialized = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

    def list_tables(self):
        inspector = inspect(self.bind)
        tables_data = []

        for table_name in self._table_names():
            table = Table(table_name, MetaData(), autoload_with=self.bind)
            row_count = self.db.execute(
                select(func.count()).select_from(table)
            ).scalar_one()
            columns = [column["name"] for column in inspector.get_columns(table_name)]
            tables_data.append(
                {
                    "name": table_name,
                    "row_count": row_count,
                    "columns": columns,
                }
            )

        return {"tables": tables_data}

    def get_table_rows(self, table_name: str, limit: int = 100):
        if table_name not in self._table_names():
            raise ValueError("Table not found")

        table = Table(table_name, MetaData(), autoload_with=self.bind)
        query = select(table)
        if "id" in table.c:
            query = query.order_by(table.c.id.desc())

        rows = self.db.execute(query.limit(limit)).mappings().all()
        total_rows = self.db.execute(
            select(func.count()).select_from(table)
        ).scalar_one()

        return {
            "table_name": table_name,
            "columns": [column.name for column in table.columns],
            "rows": [self._serialize_row(dict(row)) for row in rows],
            "total_rows": total_rows,
            "returned_rows": len(rows),
        }
