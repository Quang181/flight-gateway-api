from math import ceil
from typing import Any


class Pagination:
    def paginate(self, items: list[Any], page: int, page_size: int) -> dict[str, Any]:
        total_items = len(items)
        total_pages = ceil(total_items / page_size) if total_items > 0 else 0
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "items": items[start:end],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }
