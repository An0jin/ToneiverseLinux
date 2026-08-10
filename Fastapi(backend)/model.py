from pydantic import BaseModel

class Chat(BaseModel):
    token: str
    msg: str
    color_id: str

class Tllm(BaseModel):
    token: str
    msg: str
    sex: str
    year: int

class User(BaseModel):
    pw: str
    name: str
    email: str
    sex: str
    year: int

class Update(BaseModel):
    token: str
    pw: str | None = None
    name: str | None = None
    sex: str
    year: int

class Login(BaseModel):
    email: str
    pw: str

class Lipstick(BaseModel):
    token: str
    hex_code: str

class Email(BaseModel):
    email: str