from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends, Request, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from contextlib import asynccontextmanager

from sqlmodel import Session, select

from webapp import database


from fastapi.security import OAuth2PasswordRequestForm

#Setup User Routes
from webapp.users import routes as user_routes
from webapp.users import models as user_models

#Authentication
from webapp.auth import service as auth_service

@asynccontextmanager
async def lifespan_function(app: FastAPI):
    database.create_db_and_tables()
    yield


# Create a FastAPI Application
app = FastAPI(lifespan=lifespan_function)

app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

# And the Router object for the users
app.include_router(
    user_routes.router,
    prefix="/api/users",
    tags=["users"])


# Define a route
@app.get("/", response_class=HTMLResponse)
async def home(*,
               request: Request,
               session: Session = Depends(database.get_session)): 
    """
    Say Hello to the User.
    """
    return templates.TemplateResponse(
        request = request, name = "index.html", context = {}
        )


@app.get("/login.html", response_class=HTMLResponse)
def login_view(*,
               request: Request):
    return templates.TemplateResponse(
        request = request, name = "login.html", context = {}
        )

@app.post("/login.html", response_class=HTMLResponse)
def handle_login_view(*,
                      request: Request,
                      session: Session = Depends(database.get_session),
                      email: Annotated[str, Form()],
                      password: Annotated[str, Form()],
                      ):

    message = "Invalid Login"
    message_type = "alert-danger"
    # Fetch User
    qry = select(user_models.User).where(user_models.User.email == email)
    result = session.exec(qry).first()

    # If we have a User
    if result:
        #Check hashed password
        if result.verify_password(password):
            # Login Success
            message = "Login Success"
            message_type = "alert-success"

    return templates.TemplateResponse(
        request = request, name = "login.html", context = {"message": message,
                                                           "message_type": message_type}
        )


@app.post("/token")
async def get_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(database.get_session),
):
    """
    Conform to OAuth2 Spec, around login forms though a token url
    """
    username = form_data.username  # Part of the spec
    password = form_data.password

    # Get a User, and the Token from the validate_token function
    valid_login = auth_service.validate_login(username, password, session)
    if not valid_login:
        raise HTTPException(401, detail="Invalid User or Password")

    status, token = valid_login
    return {"access_token": token, "token_type": "bearer"}

@app.post("/cookie")
async def get_cookie(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(database.get_session),
):
    """
    Conform to OAuth2 Spec, around login forms though a token url.
    But return a Cookie as well as a token
    """
    username = form_data.username  # Part of the spec
    password = form_data.password

    # Get a User, and the Token from the validate_token function
    valid_login = auth_service.validate_login(username, password, session)
    if not valid_login:
        raise HTTPException(401, detail="Invalid User or Password")

    status, token = valid_login

    response.set_cookie(key="access_token", value=token)
    return {"access_token": token, "token_type": "bearer"}



@app.get("/current_user")
async def get_current_user(
        user: user_models.User = Depends(auth_service.get_user)
        ):
    """
    Return the current User or None
    """

    return {"current_user": user}


@app.get("/auth_user")
async def get_auth_user(
        user: user_models.User = Depends(auth_service.get_auth_user)
        ):
    """
    Return the current User or None
    """

    return {"current_user": user}


## commit time
