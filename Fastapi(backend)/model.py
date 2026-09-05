from pydantic import BaseModel

class Chat(BaseModel):
    """채팅 메시지 전송 모델"""
    token: str
    msg: str
    color_id: str

class Tllm(BaseModel):
    """텍스트 LLM 립스틱 추천 요청 모델"""
    token: str
    msg: str
    sex: str
    year: int

class User(BaseModel):
    """회원가입 요청 모델"""
    pw: str
    name: str
    email: str
    sex: str
    year: int

class Update(BaseModel):
    """회원 정보 수정 요청 모델"""
    token: str
    pw: str | None = None
    name: str | None = None
    sex: str
    year: int

class Login(BaseModel):
    """로그인 요청 모델"""
    email: str
    pw: str

class Lipstick(BaseModel):
    """대표 립스틱 변경 요청 모델"""
    token: str
    hex_code: str

class Email(BaseModel):
    """비밀번호 초기화 이메일 요청 모델"""
    email: str