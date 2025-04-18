from typing import Annotated
import logging
from fastapi import FastAPI, HTTPException, Depends, Request, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from webapp import database
from fastapi.security import OAuth2PasswordRequestForm
#Setup User Routes
from webapp.users import routes as user_routes
from webapp.users import models as user_models
#Authentication
from webapp.auth import service as auth_service
import uuid


from webapp.users import models



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan_function(app: FastAPI):
    database.create_db_and_tables()
    yield


# Create a FastAPI Application
app = FastAPI(lifespan=lifespan_function)

app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

# Include routers for organization and modularity
app.include_router(user_routes.router, prefix="/api/users", tags=["users"])
# app.include_router(module_routes.router, prefix="/api/module", tags=["modules"])


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


# Home page route
@app.get("/login.html", response_class=HTMLResponse)
def login_view(*,
               request: Request):
    return templates.TemplateResponse(
        request = request, name = "login.html", context = {}
        )
# Login view route
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

            valid_login = auth_service.validate_login(email, password, session)

            if valid_login: 
            # Login Success
                stattus, jwt_token = valid_login

                message = "Login Success"
                message_type = "alert-success"

                # user_email =

                # the_query = select(models.User)
                # the_user = session.exec(qry).ge

                # jwt_token = auth_service.validate_login(email, password, session)
                if result.admin:
                    redirect_url = "/admin"
                else:
                    redirect_url = "/users"
                user_redirect = RedirectResponse(url=redirect_url, status_code=303)
                user_redirect.set_cookie(key="access_token", value=jwt_token, httponly=True)
                return user_redirect

    return templates.TemplateResponse(
        request = request, name = "login.html", context = {"message": message,
                                                           "message_type": message_type}
        )

# OAuth2 token endpoint 
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
    username = form_data.username  
    password = form_data.password

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


# @app.get("/users", response_class=HTMLResponse)
# async def user_view(*,request: Request, the_user: user_models.User = Depends(auth_service.get_user)):

#     return templates.TemplateResponse(
#         request=request, name="users.html", context={"users": the_user}
#     )

@app.get("/users", response_class=HTMLResponse)
async def user_view(
    *,
    request: Request,
    user: user_models.User = Depends(auth_service.get_auth_user),
    token: str = Depends(auth_service.oauth2_scheme)
):
    # user = session.get(user_models.User, user_id)

 
    is_admin = "user access"

    return templates.TemplateResponse(
        request=request, name="users.html", context={"user": user, "token": token, "is_admin": is_admin}
    )



@app.get("/admin", response_class=HTMLResponse)
async def admin_view(
    *,
    request: Request,
    user: user_models.User = Depends(auth_service.get_auth_user),
    token: str = Depends(auth_service.oauth2_scheme),
    session: Session = Depends(database.get_session)
):
    # user = session.get(user_models.User, user_id)
    qry = select(models.User)
    all_users = session.exec(qry).all()
    
    
 
    is_admin = "admin access"

    return templates.TemplateResponse(
        request=request, name="admin.html", context={"user": user, "token": token, "is_admin": is_admin, "all_users": all_users}
    )