import os
from http import HTTPStatus

from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi_pagination import Page, paginate
from fastapi_pagination.ext.sqlmodel import paginate as sqlmodel_paginate  # SQLModel-specific paginate

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_, or_

from app.core.logging_config import logger
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.gemini.gemini import parse_invoice
from app.models.brand import Brand

from app.models.common import ApiResponse
from app.models.currency import Currency
from app.models.general import updateDataModel
from app.models.invoice import Invoice, InvoiceListResponse, LineItem, InvoiceRead
from app.models.supplier import Supplier
from app.models.user import User
from app.models.ingredient import Ingredient, Ingredient_Image, IngredientRead, IngredientBase
# come back to figure out ingredient read and how to handle it
from app.models.ingredient_image import *
from app.models.uom import *
from app.models.image import *
from app.models.user import *
from app.models.organisation import *
from app.services import s3_handler
from app.dependencies.user_dependencies import get_current_user
from app.services.s3_handler import delete_s3_object

InvoiceRouter: APIRouter = APIRouter()


# prefix: /invoice



@InvoiceRouter.get("/{invoice_id}/file_url")
async def get_invoice_file_url(invoice_id: int,
                               session: Session = Depends(get_session),
                               user: User = Depends(get_current_user)):
    """
    Could be more efficient and take a S3 key to request PSK directly, but this is a security risk.
    Safer to look up invoice id and authenticated user id in the DB, get the key there, and then request
    PSK from S3
    :param session:
    :param user:
    :return:
    """
    doc_data = session.exec(
        select(Invoice.id, Invoice.image_id, Invoice.organisation_id, Image.s3_key, Image.file_ext, Image.file_name)
        .join(Image, Invoice.image_id == Image.image_id)
        .where(and_(
            (Invoice.organisation_id == user.organisation_id),
            (Invoice.id == invoice_id)))
    ).first()

    if not doc_data:
        return ApiResponse(status_code=HTTPStatus.NOT_FOUND, message="Invoice does not exist")
    else:
        # get the psk
        logger.debug(f'generating psk link for image ID {doc_data.image_id} - {doc_data.s3_key}')
        filename: str = f'{doc_data.file_name}.{doc_data.file_ext}'
        s3_psk_url = s3_handler.get_psk(doc_data.s3_key, filename)
        logger.debug(s3_psk_url)
        return ApiResponse(status_code=HTTPStatus.OK, message="Invoice Found", data=s3_psk_url)


@InvoiceRouter.post("/")
async def invoice_upload_post(file: UploadFile = File(...),
                              session: Session = Depends(get_session),
                              user: User = Depends(get_current_user)
                              ) -> ApiResponse[Invoice | None]:
    """
    Upload an invoice file for processing.
    Will be saved to S3, then parsed by Gemini
    :param file:
    :param session:
    :param user:
    :return:
    """
    try:
        file_bytes = await file.read()

        # s3_key = s3_handler.push_UploadFile_to_s3(file, directory="invoice")
        s3_key = s3_handler.push_file_bytes_to_s3(file_bytes, directory="invoice")
        logger.debug(f"Invoice File pushed to S3: {s3_key}")

        filename, extension = os.path.splitext(file.filename)
        image = Image(
            file_name=filename,
            file_ext=extension,
            file_size=file.size,
            mime_type=file.content_type,
            organisation_id=user.organisation_id,
            s3_key=s3_key)
        session.add(image)
        session.flush()
        logger.debug(f'uploaded invoice s3 ID: {image.image_id}')

        invoice = Invoice(
            organisation_id=user.organisation_id,
            image_id=image.image_id,
        )

        session.add(invoice)
        session.flush()
        session.commit()  # check image_id is present here
        logger.debug(f'new invoice entry created: {invoice.id}. Now send to gemini for processing.')
        # todo - move the parser to an async func
        try:
            invoice = parse_invoice(pdf_file_data_bytes=file_bytes, invoice_id=invoice.id,
                                    organisation_id=user.organisation_id)
        except Exception as e:
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR,
                                f"Could not parse invoice. Please upload file to try again. Error: {e}")
            # todo - is the built-in httpexception the right option here, or should i use a custome API Response with suitable status code?
        return ApiResponse(data=invoice, message="Invoice uploaded successfully", status=200)

    except Exception as e:
        session.rollback()
        try:
            # delete s3 object to avoid orphaned data
            delete_s3_object(image.s3_key)
        except Exception as e:
            pass  # tried and failed to delete - doesn't matter
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error uploading invoice file - please try again: {e}")


@InvoiceRouter.get("/invoices")
async def get_invoices(session: Session = Depends(get_session),
                       user: User = Depends(get_current_user)):
    # todo - add pagination; add buttons on list page, or 'infinite scrolling' to load additional responses for older invoices
    invoice_list = (session.exec(select(Invoice)
                                 .where(Invoice.organisation_id == user.organisation_id)
                                 .options(selectinload(Invoice.invoice_status),
                                          selectinload(Invoice.invoice_image))
                                 .order_by(Invoice.date_added.desc())
                                 )
                    .all())
    response_data = [
        InvoiceListResponse(
            id=invoice.id,
            date_added=invoice.date_added,
            date_modified=invoice.date_modified,
            supplier_name=invoice.supplier_name,
            invoice_number=invoice.invoice_number,
            status=invoice.invoice_status,
            image=invoice.invoice_image
        )
        for invoice in invoice_list

    ]

    return ApiResponse(data=response_data)


class invoice_form_data(BaseModel):
    currencies: List[Currency]
    suppliers: List[Supplier]


@InvoiceRouter.get("/formdata")
async def get_invoice_form_data(session: Session = Depends(get_session),
                                user: User = Depends(get_current_user)):
    suppliers = session.exec(
        select(Supplier).where(Supplier.organisation_id == user.organisation_id)
    ).all()

    currencies = session.exec(
        select(Currency)
    ).all()
    brands = session.exec(
        select(Brand).where(Brand.organisation_id == user.organisation_id)
    ).all()
    res = invoice_form_data(currencies=currencies, suppliers=suppliers, brands=brands)
    return ApiResponse(data=res, message="Invoice Form Data pulled")


@InvoiceRouter.get("/{id}")
async def get_invoice(id: int, session: Session = Depends(get_session),
                      user: User = Depends(get_current_user)
                      ) -> ApiResponse[InvoiceRead | None]:
    full_invoice_details = session.exec(select(Invoice)

    .options(selectinload(Invoice.line_items))
    .where(and_(
        (Invoice.id == id),
        Invoice.organisation_id == user.organisation_id))
    .options(
        selectinload(Invoice.invoice_status),
        selectinload(Invoice.line_items),
        selectinload(Invoice.invoice_image)

    )).first()
    response_model = InvoiceRead.model_validate(full_invoice_details, from_attributes=True)
    res = ApiResponse(data=response_model, message=f'invoice {id} retrieved', status=HTTPStatus.OK)
    return res


@InvoiceRouter.delete("/{id}")
async def delete_invoice(id: int, session: Session = Depends(get_session),
                         user: User = Depends(get_current_user)
                         ) -> ApiResponse[None]:
    # delete invoice, line items and image file references
    # also delete s3 file to prevent storage of orphaned data
    # todo - come back to this once have viewer working so can see detials of elements that SHOULD be deleted when this runs to confirm completion successfully.
    # todo - write a unit test for the same - upload a well structured set of data, confirm it's there, then confirm it's fully deleted afterwards

    try:
        s3_key = None
        invoice = (session.exec(select(Invoice)
        .where(and_(
            Invoice.id == id,
            Invoice.organisation_id == user.organisation_id)))
                   .first())
        if invoice.image_id:
            image = session.get(Image, invoice.image_id)
            s3_key = image.s3_key
        session.delete(invoice)
        session.commit()

        # line items and invoice images are set to cascade delete via invoice relationship declarations, so no action is required to delete these

        # image files must be deleted from s3 separately - only completes once the image entry is deleted - will be skipped if DB changes throw an exception
        if s3_key:
            s3_handler.delete_s3_object(s3_key)
    except Exception as e:
        msg = f"Error deleting invoice {id} - changes rolled back and s3 object untouched"
        logger.exception(f"{msg} : {e}")
        return ApiResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg, data=None)
    return ApiResponse(status_code=HTTPStatus.NO_CONTENT, message=f"Invoice {id} deleted successfully", data=None)


# class updateDataModel(BaseModel):
#     field_name: str
#     new_value: str | int | float | datetime | None | bool


@InvoiceRouter.patch("/lineitem/{id}")
async def update_invoice_line_item_field(data: updateDataModel,
                                         id: int, session: Session = Depends(get_session),
                                         user: User = Depends(get_current_user), ):
    line_item = session.exec(select(LineItem).join(Invoice).where(
        and_(LineItem.id == id, Invoice.organisation_id == user.organisation_id))).first()
    setattr(line_item, data.field_name, data.new_value)
    session.commit()


@InvoiceRouter.patch("/{id}")
async def update_invoice_field(
        data: updateDataModel,
        id: int, session: Session = Depends(get_session),
        user: User = Depends(get_current_user),
):
    print(data)
    invoice = session.exec(
        select(Invoice).where(and_(Invoice.id == id, Invoice.organisation_id == user.organisation_id))).first()
    setattr(invoice, data.field_name, data.new_value)
    session.commit()

    print(data)
    return ApiResponse(status_code=HTTPStatus.NO_CONTENT,
                       message=f"invoice id {id}, field {data.field_name} updated to {data.new_value}")
