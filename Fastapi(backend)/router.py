from typing import Annotated
import pandas as pd
from fastapi import APIRouter, Form, Path
from psycopg2.errors import UniqueViolation
from model import Chat, User, Update, Lipstick
from tool import connect, to_response, hashpw, JWT, SendEmail

chat = APIRouter(tags=['chat'], prefix='/chat')
user = APIRouter(tags=['user'], prefix='/user')

WELCOME_MSG = """안녕하세요, Toniverse에 오신 것을 진심으로 환영합니다!
당신만의 퍼스널컬러와 상황에 맞는 AI 기반 가상 메이크업 서비스를 경험해보세요.
Toniverse 개발자 드림"""

@user.get("/{token}")
def get_user(token: Annotated[str, Path()]) -> dict:
    try:
        data = JWT.decode(token)
        with connect() as conn:
            df = pd.read_sql('select * from v_user_lipstick where email=%s and pw=%s', conn, params=[data['email'], data['pw']])
        df['token'] = token
        return df.to_dict(orient="records")[0]
    except Exception as e:
        return to_response(str(e))

@chat.get("/{color}")
def get_chat(color: Annotated[str, Path()]) -> dict:
    try:
        with connect() as conn:
            df = pd.read_sql('select * from v_user_chat_lipstick where color_id=%s', conn, params=[color])
        return to_response(df)
    except Exception as e:
        return to_response(str(e))

@chat.post("")
def post_chat(chat_data: Annotated[Chat, Form()]) -> dict | None:
    try:
        data = JWT.decode(chat_data.token)
        with connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("insert into chat(email,msg,color_id) values(%s,%s,%s)", (data['email'], chat_data.msg, chat_data.color_id))
                conn.commit()
    except Exception as e:
        return to_response(str(e))

@user.post("")
def post_user(user_data: Annotated[User, Form()]) -> dict:
    try:
        email = user_data.email.lower()
        hashed_pw = hashpw(user_data.pw)
        token = JWT.encode(email, hashed_pw)
        with connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute('insert into "user"(email,pw,name,sex,year) values (%s,%s,%s,%s,%s)',
                               (email, hashed_pw, user_data.name, user_data.sex, user_data.year))
                conn.commit()
        SendEmail(email, 'Toniverse에 오신 것을 환영합니다', WELCOME_MSG)
        return {"token": token, "result": ""}
    except UniqueViolation:
        return {"result": "이미 존재하는 이메일입니다"}
    except Exception as e:
        return {"result": f"개발자 오류 : {e}"}

@user.put("")
def put_user(update: Update) -> dict:
    try:
        data = JWT.decode(update.token)
        email, pw = data['email'], data['pw']
        new_pw = hashpw(update.pw) if update.pw else pw
        with connect() as conn:
            with conn.cursor() as cursor:
                sql = 'UPDATE "user" SET pw=%s, name=%s, sex=%s, year=%s WHERE email=%s and pw=%s' if update.pw else 'UPDATE "user" SET sex=%s, year=%s WHERE email=%s and pw=%s'
                params = (new_pw, update.name, update.sex, update.year, email, pw) if update.pw else (update.sex, update.year, email, pw)
                cursor.execute(sql, params)
                conn.commit()
        res = to_response("수정 완료")
        res['token'] = JWT.encode(email, new_pw)
        return res
    except Exception as e:
        return to_response(str(e))

@user.put("/lipstick")
def put_user_lipstick(lipstick: Lipstick) -> dict:
    try:
        data = JWT.decode(lipstick.token)
        with connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute('update "user" set hex_code=%s where email=%s and pw=%s',
                               (lipstick.hex_code, data['email'], data['pw']))
                conn.commit()
        return to_response("수정 완료")
    except Exception as e:
        return to_response(str(e))

@user.delete("/{token}")
def delete_user(token: Annotated[str, Path()]) -> dict:
    try:
        data = JWT.decode(token)
        with connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute('delete from chat where email=%s; delete from "user" where email=%s and pw=%s;',
                               (data['email'], data['email'], data['pw']))
                conn.commit()
                return to_response("" if cursor.rowcount > 0 else "존재하지 않는 이메일입니다")
    except Exception as e:
        return to_response(str(e))

