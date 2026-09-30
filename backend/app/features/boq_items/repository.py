import re
from typing import List, Optional

from sqlmodel import Session, select

from app.features.boq_items.model import BOQItem

# Keys the quote engine looks up directly -- these must always exist and
# are never deletable through the API.
BUILT_IN_KEYS = {"fibre", "rack", "router", "bandwidth"}


def list_items(session: Session, active_only: bool = False) -> List[BOQItem]:
    query = select(BOQItem)
    if active_only:
        query = query.where(BOQItem.is_active == True)  # noqa: E712
    return list(session.exec(query))


def get_item(session: Session, item_id: int) -> Optional[BOQItem]:
    return session.get(BOQItem, item_id)


def get_item_by_key(session: Session, key: str) -> Optional[BOQItem]:
    return session.exec(select(BOQItem).where(BOQItem.key == key)).first()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "item"


def _generate_unique_custom_key(session: Session, name: str) -> str:
    base = f"custom_{_slugify(name)}"
    key = base
    suffix = 2
    while get_item_by_key(session, key) is not None:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def create_custom_item(session: Session, item: BOQItem) -> BOQItem:
    item.key = _generate_unique_custom_key(session, item.name)
    item.is_custom = True
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item: BOQItem) -> None:
    session.delete(item)
    session.commit()