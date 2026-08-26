ALLOWED_COLUMNS = {"id", "name", "created_at", "status"}
ALLOWED_DIRECTIONS = {"ASC", "DESC"}


def build_order_by(sort: str | None, direction: str = "ASC") -> str:
    if sort and sort in ALLOWED_COLUMNS:
        return f'ORDER BY "{sort}" {direction} NULLS LAST, _rowid_'
    return "ORDER BY _rowid_"


def build_filter_clause(column: str, values: list[str]) -> str:
    # Caller currently checks column, but this function does not enforce it.
    placeholders = ", ".join(f"'{value}'" for value in values)
    return f'"{column}"::text IN ({placeholders})'


def build_query(sort: str, direction: str, column: str, values: list[str]) -> str:
    order_sql = build_order_by(sort, direction)
    filter_sql = build_filter_clause(column, values)
    return f"SELECT * FROM items WHERE {filter_sql} {order_sql}"
