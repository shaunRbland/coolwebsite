"""
Functionality Related to Authentication

This is neither a route, or a view as it shouldn't be visible to the
end user.  So we break it into a seperate file.
"""

import datetime
import logging
import uuid

from typing import Optional, Dict, Annotated

from fastapi import Request, HTTPException, status, Depends
from sqlmodel import Session, select


# FastAPI OAUTH2 Imports
from fastapi.security import OAuth2
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel

# For JWT
import jwt
from jwt.exceptions import InvalidTokenError

from webapp.users.models import User
from webapp import database

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

JWT_TOKEN_EXPIRES = 30 #30 Minutes on Expirey
JWT_SECRET_KEY = "FFS_CHANGE_ME"
JWT_ALG = "HS256"


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    Follow the OAUTH2 Model to maintain compatibility with tokens
    and cookies.

    Essentially we overload the OAUTH2 Model to allow cookie based
    authentication to also be used.

    I have disabled auto_error by default,
    as it causes issues when we try to get a user or none 
    (ie if there is a user return info, for example letting the homepage show either user or login pages)

    Error handing and 40x codes are handled in the requires authenticated user etc methods
    """

    
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = False,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # Allow authorization scheme to be either cookie or header based
        log.debug("===== AUTH CALL ====")

        # Deal with cookie based authentication
        authorization: str = request.cookies.get("access_token")
        if authorization:
            # Beacuse I found the bearer prefix in the cookie ugly We dont actually have one.
            # Therefore just return whatever is in the access token field.
            log.debug("Auth via Cookie %s", authorization)
            return authorization

        # If we dont have a cookie try the request header
        if not authorization:
            print("AUTH VIA TOKEN")
            log.debug("--> Auth Via Token")
            authorization: str = request.headers.get("Authorization")

        scheme, param = get_authorization_scheme_param(authorization)
        log.debug("scheme is %s", scheme)
        log.debug("params %s", param)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None

        return param

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")

    
def create_access_token(
    data: dict,
):
    """
    Given a dictionary of information (which should be user details)
    Create a JWT based token, and return it
    """

    to_encode = data.copy()

    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=JWT_TOKEN_EXPIRES)
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(
        to_encode, JWT_SECRET_KEY, algorithm=JWT_ALG
    )
    return encoded_jwt


def decode_token(
    token: str,
    session: Session,
):
    """
    Decode a token and return the relevant user if they exist.
    """
    if token is None:
        return None

    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[JWT_ALG]
        )
        user_id: str = payload.get("sub", None)

    except InvalidTokenError:
        return None

    restored_uuid = uuid.UUID(user_id)
    the_user = session.get(User, restored_uuid)

    return the_user

def validate_login(
    email: str,
    password: str,
    session: Session,
):
    """
    Validate a login

    If the login is correct create a token and return it as a tuple
    of [User, token] otherwise, return [False, Message]
    """

    # Fetch the User from the Database
    qry = select(User).where(User.email == email)
    db_user = session.exec(qry).first()
    if not db_user:
        return False
    # Confirm Password
    if not db_user.verify_password(password):
        return False

    # If we use UUID, our token hates it, so just return he hex
    hex_id = db_user.id.hex

    # Create a new 
    token = create_access_token(data={"sub": hex_id})
    return [db_user, token]


async def get_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(database.get_session),
):
    """
    Return the current user. Or None if they don't exist
    """

    if not token:
        return None

    # Decode the token using the decode token function we defined
    the_user = decode_token(token, session)
    return the_user


async def get_auth_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Session = Depends(database.get_session),
):
    """
    Return the current user,  Raise a Not Authenticated
    Exception if the use does not exist
    """

    if not token:
        raise HTTPException(301, "Not Authenticated")

    the_user = decode_token(token, session)

    if not the_user:
        raise HTTPException(301, "Not Authenticated")
    
    return the_user
    
