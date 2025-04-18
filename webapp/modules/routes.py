import logging
import uuid
from typing import List

# New Import for API Routers
from fastapi import APIRouter

# As Main but without FastAPI
from fastapi import HTTPException, Depends, Request, Form

from sqlmodel import Session, select

from webapp import database

# Named import of module Models
from webapp.modules import models


log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model = List[models.Publicmodule])
def get_modules( *, session: Session = Depends(database.get_session)):
    """ Get a List of modules """
    qry = select(models.module)
    result = session.exec(qry).all()

    return result



@router.get("/{item_id}", response_model = models.Publicmodule)
def get_module(*,
             item_id: uuid.UUID,
             session: Session = Depends(database.get_session)):
    """ Get a Specific module """
    db_item = session.get(models.module, item_id)
    if not db_item:
        raise HTTPException(status_code = 404)
    return db_item


@router.post("/", response_model=models.Publicmodule)
async def create_module(
    *,
    session: Session = Depends(database.get_session),
    new_item: models.moduleCreate
    ):
    """ Create a new module in the DB """
    # Create a new module model from the JSON supplied by the module
    hashed_password = models.hash_password(new_item.password)
    extra_data = {"password": hashed_password}

    # Add hashed PW as extra_data when validating the model
    db_item = models.module.model_validate(new_item, update=extra_data)        
    # Add it to the Database and Commit
    session.add(db_item)
    session.commit()
    
    # Update ID's before returning the Item
    session.refresh(db_item)
    return db_item


@router.patch("/{item_id}", response_model=models.Publicmodule)
async def update_module(
    *,
    session: Session = Depends(database.get_session),
    item_id: uuid.UUID,
    the_item: models.moduleUpdate,
):
    """ Update an Existing module in the DB """
    # Get the module by ID
    db_item = session.get(models.module, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Not Found")

    # Update the model from the DB
    item_data = the_item.model_dump(exclude_unset=True)

    # Update the Password if it exists
    if "password" in item_data:
        password = item_data["password"]
        hashed_password = models.hash_password(password)
        item_data["password"] = hashed_password

    # Add Item to Session
    db_item.sqlmodel_update(item_data)
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
async def delete_module(
    *,
    session: Session = Depends(database.get_session),
    item_id: uuid.UUID,
):

    """ Remove a module from  the DB """
    db_item = session.get(models.module, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Not Found")

    session.delete(db_item)
    session.commit()
    return {"ok": True}
