from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext
import uuid


class Module(SQLModel, table=True):
    #id: int = Field(default = None, primary_key = True)
    module_id: int = Field(primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    module_name: str
    description: str
    complete: bool = Field(default=False)



class PublicModule(SQLModel):
    module_id: int
    module_name: str

class ModuleCreate(SQLModel):
    module_id: int 
    module_name: str
    description: str
    complete: bool 

class ModuleUpdate(SQLModel):
    module_id: int
    module_name: str
    description: str
    complete: bool 
 

