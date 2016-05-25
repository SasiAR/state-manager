from datetime import datetime
from statemanager.dao import current_session
from statemanager.domain import ItemVersion
from sqlalchemy import and_, func


def add_to_version(item_type: str, item_id: str):
    session = current_session()
    item_version = session.query(ItemVersion).filter(
        and_(ItemVersion.item_type == item_type, ItemVersion.item_id == item_id)).first()

    if item_version is not None:
        return

    max_version = session.query(func.max(ItemVersion.version_number)).filter(
        ItemVersion.item_type == item_type).first()[0]

    if max_version is None:
        max_version = 1
    else:
        max_version += 1

    session.add(ItemVersion(item_type=item_type,
                            item_id=item_id,
                            version_number=max_version,
                            created_ts=datetime.now()))
    session.flush()
