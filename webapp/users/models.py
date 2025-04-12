from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext
import uuid

#Create password Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    """
    Helper Function to hash a users password
    """
    return pwd_context.hash(password)

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key = True)
    #id: int = Field(default = None, primary_key = True)
    name: str
    email: str
    password: str

    def verify_password(self, password):
        """
        Confirm password is correct.
        """
        if password is None:  #Prob Redundant but makes it easier to jsut pass JSON
            return False
        return pwd_context.verify(password, self.password)

    def update_password(self, password):
        """
        Set / Update a users password
        """
        if password is None: #Prob Redundant but...
            return False
        elif password != "":
            new_password = hash_password(password)
            self.password = new_password

class PublicUser(SQLModel):
    id: uuid.UUID
    name: str

class UserCreate(SQLModel):
    name: str
    email: str
    password: str

class UserUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None

