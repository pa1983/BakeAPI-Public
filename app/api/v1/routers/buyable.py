from fastapi import APIRouter, Body, Depends
from fastapi_pagination.ext import sqlalchemy

from sqlmodel import Session, select, and_, or_
from starlette import status

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.general import updateDataModel
from app.models.user import User

buyableRouter: APIRouter = APIRouter()

# =======BRAND======== #
@buyableRouter.post("/brand",
                    response_model=ApiResponse[BrandRead | None])
async def post_brand(
        form_data: BrandCreate = Body(...),
        session: Session = Depends(get_session),
        user: User = Depends(get_current_user)
) -> ApiResponse[BrandRead | None]:
    try:
        from_form = form_data.model_dump()
        from_form['organisation_id'] = user.organisation_id
        brand = Brand.model_validate(from_form)
        session.add(brand)

    except Exception as e:
        return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Error validating your brand data - nothing was created: {e}",
                           data=None)

    try:
        session.commit()
        session.refresh(brand)
        response_brand: BrandRead = BrandRead.model_validate(brand)

    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                           message=f"""Brand {brand.brand_name} already exists in your organisation. 
                           Please select the existing entry or choose a different name.""",
                           data=None)

    except Exception as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message=f"Error creating brand: {e}",
                           data=None)

    return ApiResponse(data=response_brand,
                       message=f"Brand {brand.brand_name} created successfully",
                       status_code=status.HTTP_201_CREATED)


@buyableRouter.get("/brand/{id}")
async def get_brand(id: int,
                    session: Session = Depends(get_session),
                    user: User = Depends(get_current_user)) -> ApiResponse[BrandRead | None]:
    res = session.exec(
        select(Brand).where(and_(Brand.brand_id == id, Brand.organisation_id == user.organisation_id))).first()
    if res:
        brand = BrandRead.model_validate(res)
        status_code = status.HTTP_200_OK
    else:
        brand = None

    return ApiResponse(data=brand, message=f"Brand {brand.brand_name} retrieved successfully", status_code=status_code)


@buyableRouter.get("/brands")
async def get_brands(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Get all brands for the current user's organisation.
    :param session:
    :param user:
    :return:
    """
    brands = session.exec(
        select(Brand).where(Brand.organisation_id == user.organisation_id).order_by(Brand.brand_name)).all()
    return ApiResponse(data=brands, message=f"Brands retrieved successfully", status_code=status.HTTP_200_OK)


@buyableRouter.delete("/brand/{id}")
async def delete_brand(id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    brand = session.exec(
        select(Brand).where(and_(Brand.brand_id == id, Brand.organisation_id == user.organisation_id))).first()
    session.delete(brand)
    session.commit()
    return ApiResponse(data=None, message=f"Brand {brand.brand_name} deleted successfully",
                       status_code=status.HTTP_200_OK)


# todo - add PATH - copy logic from the invoices endpoint. Add error handling, type hints
@buyableRouter.patch("/brand/{id}")
async def update_field(
        data: updateDataModel,
        id: int,
        session: Session = Depends(get_session),
        user: User = Depends(get_current_user),
):
    print(data)
    # todo -  check that the data.field name is not a system-only field like ID or datemodified.
    ## todo then test in postman
    brand = session.exec(
        select(Brand).where(and_(Brand.brand_id == id, Brand.organisation_id == user.organisation_id))).first()
    setattr(brand, data.field_name, data.new_value)
    session.commit()

    print(data)
    return ApiResponse(status_code=status.HTTP_204_NO_CONTENT,
                       message=f"brand id {id}, field {data.field_name} updated to {data.new_value}")

# =======BUYABLE======== #
@buyableRouter.get("/")
async def default():
    return {"message": "Got to default router in error?"}

# @PurchasableRouter.post("/")
# async def post_purchasable(
#         form_data: PurchasableBase = Body(...),
#         session: Session = Depends(get_session),
#         user: User = Depends(get_current_user)
# )
#     """
#     Create a new purchasable item.
#     :param form_data:
#     :param session:
#     :param user:
#     :return:
#     """
#     purchasable = Purchasable.model_validate(form_data)
#
