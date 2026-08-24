from typing import List, Any, Tuple
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def paginate_list(items: List[Any], page: int = 1, page_size: int = 10) -> Tuple[List[Any], int, int]:
    """Returns (page_items, total_pages, current_page)."""
    if not items:
        return [], 1, 1
    total_pages = (len(items) + page_size - 1) // page_size
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages, page

def build_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    extra_buttons: List[List[InlineKeyboardButton]] = None
) -> InlineKeyboardMarkup:
    buttons = []
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{callback_prefix}_{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="noop"))
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{callback_prefix}_{current_page + 1}"))

    if len(nav_row) > 1 or (len(nav_row) == 1 and nav_row[0].callback_data != "noop"):
        buttons.append(nav_row)

    if extra_buttons:
        buttons.extend(extra_buttons)

    return InlineKeyboardMarkup(buttons)
