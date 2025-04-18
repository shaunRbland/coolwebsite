"""
HTML based views for Users
"""

from fastapi import HTTPException, Depends, Request, Form
from sqlmodel import Session, select

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# We have to redefine the template directory here, to avoid circular import
templates = Jinja2Templates(directory="webapp/templates")


