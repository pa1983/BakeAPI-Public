from app.models.image import Image
from app.models.invoice import Invoice, LineItem, InvoiceRead
from app.models.user import User
from session import db_session
from sqlmodel import select, and_
from sqlalchemy.orm import selectinload

from sqlmodel import select
user = User(organisation_id=2)
id = 38


with db_session() as session:
    res = session.exec(select(Invoice)
                       .options(selectinload(Invoice.line_items))
                       .where(and_(
        (Invoice.id == id),
        Invoice.organisation_id == user.organisation_id))
                       .options(
        selectinload(Invoice.invoice_status),
                                selectinload(Invoice.line_items),
        selectinload(Invoice.invoice_image),
        selectinload(Invoice.organisation)

    )).first()


    rr = InvoiceRead.model_validate(res, from_attributes=True)

    print(res)


    # full_invoice_details = ((session.exec(select(Invoice)
    # .options(selectinload(Invoice.line_items))
    # .where(and_(
    #     (Invoice.id == id),
    #     Invoice.organisation_id == user.organisation_id))))
    #                         .first())
    # print(full_invoice_details)