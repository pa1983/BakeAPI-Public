from app.models.invoice import Invoice, LineItem
from app.models.user import User
from session import db_session
from sqlmodel import select, and_
from sqlalchemy.orm import selectinload

from sqlmodel import select
user = User(organisation_id=2)
id = 6
with db_session() as session:
    full_invoice_details = ((session.exec(select(Invoice)
    .options(selectinload(Invoice.line_items))
    .where(and_(
        (Invoice.id == id),
        Invoice.organisation_id == user.organisation_id))))
                            .first())
    print(full_invoice_details)