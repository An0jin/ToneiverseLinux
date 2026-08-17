import os, re
from io import BytesIO
from typing import Annotated
from PIL import Image
import pandas as pd, numpy as np
import torch
from torchvision import transforms
from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, File, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from ultralytics import YOLO

from router import chat, user
from model import Login, Tllm, Email
from tool import connect, to_response, hashpw, JWT, SendEmail, TextLLM, CVLLM

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
@app.on_event('startup')
async def on_startup():    
    
    face_model = YOLO('face.pt')
    pcolor_model = torch.load('personal_color.pt', map_location='cpu')
    if hasattr(pcolor_model, 'eval'): pcolor_model.eval()
    
    with open('classes.txt', encoding='utf-8') as f:
        CLASSES = [line.strip() for line in f if line.strip()]
    
    pcolor_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

@app.post('/login')
async def login(login_data: Annotated[Login, Form()]) -> dict:
    try:
        email, hashed = login_data.email.lower(), hashpw(login_data.pw)
        with connect() as conn:
            df = pd.read_sql('select email,name,hex_code,color_id,cname,year,sex from v_user_lipstick where email=%s and pw=%s', conn, params=[email, hashed])
        if len(df) == 1:
            res = df.to_dict(orient="records")[0]
            res.update({"msg": "성공", "token": JWT.encode(email, hashed)})
            return res
        return {"msg": "이메일과 암호를 확인해주세요", "token": None}
    except Exception as e:
        return to_response(str(e))

def sync_processor(img_byte: bytes, token: str | None) -> dict:
    img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
    boxes = face_model.predict(img_pil, iou=0.1, agnostic_nms=True, imgsz=640)[0].boxes
    if len(boxes) != 1:
        return {"color_id": "한사람만 테스트할수 있습니다" if len(boxes) > 1 else "얼굴을 찾을 수 없습니다", "hex_code": "", "cname": ""}
    color_id=boxes.cls[0]
    with connect() as conn:
        df = pd.read_sql('SELECT color_id, hex_code, cname FROM lipstick where color_id=%s', conn, params=(color_id,))
        res = df.to_dict(orient="records")[0] if len(df) > 0 else {"color_id": color_id, "hex_code": "", "cname": ""}
        if token and (data := JWT.decode(token)):
            with conn.cursor() as cur:
                cur.execute('UPDATE "user" SET hex_code=%s WHERE email=%s and pw=%s', (res['hex_code'], data['email'], data['pw']))
                conn.commit()
    return res

@app.post('/predict')
async def predict_image(img: Annotated[UploadFile, File()], token: Annotated[str | None, Form()] = None) -> dict:
    try:
        img_byte = await img.read()
        return await run_in_threadpool(sync_processor, img_byte, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/lipstick/{color}')
async def lipstick(color: Annotated[str, Path()]) -> dict:
    with connect() as conn:
        df = pd.read_sql('select hex_code,cname from lipstick where color_id=%s', conn, params=[color])
    return to_response(df.to_dict(orient='records'))

@app.post('/llm')
async def llm_text(llm: Annotated[Tllm, Form()]) -> dict:
    data = JWT.decode(llm.token)
    email, pw = data['email'], data['pw']
    with connect() as conn:
        colors = list(pd.read_sql('''
            SELECT hex_code FROM lipstick WHERE color_id = (
                SELECT T1.color_id FROM "user" AS T0 
                INNER JOIN lipstick AS T1 ON T0.hex_code = T1.hex_code 
                WHERE T0.email = %s and T0.pw=%s
            )''', conn, params=[email, pw])['hex_code'])
        text_llm = TextLLM()
        response = text_llm.invoke(llm.msg, colors, sex=llm.sex, year=llm.year)
        color = re.findall(r"#[A-Fa-f\d]{6}", response)[0]
        with conn.cursor() as cursor:
            cursor.execute('update "user" set hex_code=%s where email=%s and pw=%s', (color, email, pw))
            conn.commit()
        result = pd.read_sql('SELECT hex_code,cname FROM lipstick WHERE hex_code = %s', conn, params=[color]).to_dict(orient="records")[0]
        result['result'] = text_llm.rm_markdown(response.replace(color, result['cname']))
    return result

@app.post('/cvllm')
async def llm_cv(img: Annotated[UploadFile, File()], color_id: Annotated[str, Form()]) -> dict:
    cv_llm = CVLLM()
    response = await cv_llm.invoke(color_id, img)
    return {"result": response}

@app.get('/version/{version}')
async def check_version(version: Annotated[int, Path()]) -> dict:
    with connect() as conn:
        df = pd.read_sql('select * from "version"', conn)
    return to_response(version == df['version'].values[0])

@app.post('/email')
async def get_pw(email: Annotated[Email, Form()]) -> dict:
    new_pw = os.urandom(32).hex()[:6]
    with connect() as conn:
        df = pd.read_sql('select * from "user" where email=%s', conn, params=[email.email])
        if len(df) == 0:
            return to_response("해당 이메일이 존재하지 않습니다")
        with conn.cursor() as cursor:
            cursor.execute('update "user" set pw=%s where email=%s', (hashpw(new_pw), email.email))
            conn.commit()
    SendEmail(email.email, 'Toniverse 비밀번호 초기화 관련', f"당신의 비밀번호는 {new_pw}으로 초기화 했습니다")
    return to_response("메일을 확인해주세요")

@app.post('/getNum')
async def get_num(email: Annotated[str, Form()], num: Annotated[str, Form()]) -> dict:
    SendEmail(email, 'Toniverse 인증번호', f"인증번호 : {num}")
    return to_response("메일을 확인해주세요")

@app.exception_handler(404)
def error_handler(request: Request, exc: HTTPException):
    return JSONResponse(content={"result": "잘못된 응답입니다"}, status_code=404)

app.include_router(chat)
app.include_router(user)

