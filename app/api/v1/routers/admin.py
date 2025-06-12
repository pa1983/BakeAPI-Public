from fastapi import APIRouter

AdminRouter: APIRouter = APIRouter()

# todo - create:
# modify user role
# modify role-permission (list of check boxes per role)

# look up permissions by user.  Users might be able to VIEW this, but not modify.
# Admin will have both get and post access
# what does this look like in sql model?  need custom response type to merge multiple tables?


