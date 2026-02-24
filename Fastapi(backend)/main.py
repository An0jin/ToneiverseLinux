from fastapi import FastAPI, UploadFile, HTTPException, Request,Form,File
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
from fastapi.middleware.cors import CORSMiddleware
from router import *
import json
import re
from tool import JWT,connect,to_response,hashpw, SendEmail,TextLLM,CVLLM
import os
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool
load_dotenv()


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    docs_url=None,  # 주석 해제 시 Swagger 문서 비활성화
    redoc_url=None
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# ====================[ 테스트용 ]====================

# @app.get('/')
# async def test():
#     return FileResponse("index.html")

# ====================[ 로그인 기능 ]====================

# 로그인 시스템
@app.post('/login')
async def login(login:Login=Form(...)):
    try:
        with connect() as conn:
            login.email=login.email.lower()
            df=pd.read_sql('select email,name,hex_code,color_id,cname,year,sex from  v_user_lipstick where email=%s and pw=%s',conn,params=[login.email,hashpw(login.pw)])
            result=df.to_dict(orient="records")[0] if len(df)==1 else dict(zip(df.columns,[None]*len(df.columns)))
            result['msg']="성공"if  len(df)==1 else '이메일과 암호를 확인해주세요'
            result['token']=JWT.encode(login.email)if  len(df)==1 else None
            return result
    except Exception as e:  
        return to_response(str(e))


# ====================[ 예측 기능 ]====================
def sync_processor(img_byte: bytes, token: str):
    """
    CPU-bound(predict)와 I/O-bound(DB access)를 모두 처리하는 동기 함수.
    이 함수는 전체가 스레드 풀에서 실행되므로 메인 이벤트 루프를 차단하지 않습니다.
    """
    
    model=YOLO('pcolor.onnx')   
    # 1. 모델 추론 (CPU-bound)
    img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
    print("이미지 불러오기 완료") 
    results = model.predict(img_pil, iou=0.1, agnostic_nms=True,imgsz=640)
    result_cls = results[0].boxes.cls
    # results[0].show()
    print(f"결과 : {result_cls}")
    # 2. 예측 결과 로직 (동일)
    if len(result_cls) > 1:
        return {"color_id": "한사람만 테스트할수 있습니다", "hex_code": "", "cname": ""}
    elif len(result_cls) == 0:
        return {"color_id": "얼굴을 찾을 수 없습니다", "hex_code": "", "cname": ""}
    
    color_id=model.names[result_cls[0].item()]
    
    with connect() as conn:
        df = pd.read_sql(
            'SELECT color_id, hex_code, cname FROM lipstick where color_id=%s', 
            conn, 
            params=(color_id,)
        )

        # DataFrame을 JSON 문자열로 변환 후 파싱
        df_json = df.to_json(orient="records")
        response = json.loads(df_json)[0]

        try:
            email = JWT.decode(token)
            if not email:
                print("WARN: JWT 디코딩 성공, 그러나 이메일 정보 없음")
            else:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE "user" SET hex_code=%s WHERE email=%s', 
                    (response['hex_code'], email)
                )
                conn.commit()
        except jwt.InvalidTokenError:
            print("WARN: 유효하지 않은 토큰입니다. DB 업데이트 생략.")
        except Exception as e:
            print(f"ERROR: DB 업데이트 중 예외 발생: {e}")

    return response


@app.post('/predict')
async def predict_image(img: UploadFile=File(...), token: str = Form(None)):
    
    print("예측중")
    
    # 1. 비동기로 파일 읽기 (유일한 async I/O)
    try:
        img_byte = await img.read()
    except Exception:
        raise HTTPException(status_code=400, detail="이미지 파일을 읽을 수 없습니다.")

    # 2. CPU-bound 및 동기 I/O (Pandas/DB) 작업을 스레드 풀에서 실행
    # blocking 코드를 run_in_threadpool로 감싸 이벤트 루프 차단을 방지함
    try:
        result = await run_in_threadpool(sync_processor, img_byte, token)
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))
    except NotImplementedError:
        raise HTTPException(status_code=500, detail="서버 설정 오류: DB 연결 함수가 정의되지 않았습니다.")
    except Exception as e:
         # 다른 모든 예외를 500 에러로 처리
         print(f"Critical Error in sync_processor: {e}")
         raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")
    
    # 3. 최종 응답
    return result

# ====================[ 립스틱 반환 기능 ]====================

# 퍼스널컬러->어울리는 립스틱 해시코드 반환
@app.get('/lipstick/{color}')
async def lipstick(color:str):
    with connect() as conn:
        df=pd.read_sql('select hex_code,cname from lipstick where color_id=%s',conn,params=[color,])
    return to_response(df.to_dict(orient='records'))

# ====================[ AI 챗봇 기능 ]====================
@app.post('/llm')
async def llm_text(llm:Tllm=Form(None)):
    with connect() as conn:
        load_dotenv()
        email=JWT.decode(llm.token)
        colors=list(map(lambda x:x[0],pd.read_sql('''
        SELECT hex_code FROM lipstick 
WHERE color_id = (
    SELECT T1.color_id 
    FROM "user" AS T0 
    INNER JOIN lipstick AS T1 ON T0.hex_code = T1.hex_code 
    WHERE T0.email = %s
)''',conn,params=[email,]).values))
        lllm=TextLLM()
        
        response = lllm.invoke(llm.msg,colors,sex=llm.sex,year=llm.year)
        patten=r"#[A-Fa-f\d]{6}"
        color=re.findall(patten,response)[0]
        cursor=conn.cursor()
        cursor.execute('update "user" set hex_code=%s where email=%s',(color,email))
        conn.commit()     
        result=pd.read_sql('SELECT hex_code,cname FROM lipstick WHERE hex_code = %s',conn,params=[color,])
        result=result.to_dict(orient="records")[0]
        result['result']=lllm.rm_markdown(response.replace(color,result['cname']))
    return result
@app.post('/cvllm')
async def llm_cv(img:UploadFile=File(...),color_id:str=Form(...)):
    with connect() as conn:
        load_dotenv()
        lllm=CVLLM()
        response =await lllm.invoke(color_id,img)
        print(f"response is {response}")
        result={"result":response}
    return result

# ====================[ 버전 체크 기능]====================
@app.get('/version/{version}')
async def version(version:int):
    with connect() as conn:
        df=pd.read_sql('select * from "version"',conn)
    return to_response(version==df['version'].values[0])

# ====================[  비밀번호 초기화 기능]====================
@app.post('/email')
async def get_Pw(email:Email=Form(...)):
    print(f"email : {email.email}")
    new_pw=os.urandom(32).hex()[:6]
    with connect() as conn:
        df=pd.read_sql('select * from "user" where email=%s',conn,params=[email.email])
        if len(df)==0:
            return to_response("해당 이메일이 존재하지 않습니다")
        cursor=conn.cursor()
        cursor.execute('update "user" set pw=%s where email=%s',(hashpw(new_pw),email.email))
        conn.commit()
    SendEmail(email.email,'Toniverse 비밀번호 초기화 관련',f"당신의 비밀번호는 {new_pw}으로 초기화 했습니다")
    return to_response("메일을 확인해주세요")

@app.post('/getNum')
async def getNum(email:str=Form(...),num:str=Form(...)):
    SendEmail(email,'Toniverse 인증번호',f"인증번호 : {num}")
    return to_response("메일을 확인해주세요")

# ====================[ 예측 기능 ]====================
def lipstick_processor(img_byte: bytes, color_id: str):
    """
    CPU-bound(predict)와 I/O-bound(DB access)를 모두 처리하는 동기 함수.
    이 함수는 전체가 스레드 풀에서 실행되므로 메인 이벤트 루프를 차단하지 않습니다.
    """
    
    # 1. 모델 추론 (CPU-bound)
    img_pil = Image.open(BytesIO(img_byte)).convert('RGB') 
    results = model.predict(img_pil, iou=0.1, agnostic_nms=True,imgsz=512)
    result = results[0]
    print(f"결과 : {result}")
    # 2. 예측 결과 로직 (동일)
    if len(result.boxes) > 1:
        return to_response("립스틱 한개만 진단합니다")
    elif len(result.boxes) == 0:
        return to_response("립스틱을 찾을 수 없습니다")
    
    color_id=result.names[result.boxes.cls[0].item()]
    
    with connect() as conn:
        df = pd.read_sql(
            'SELECT color_id, hex_code, cname FROM lipstick where color_id=%s', 
            conn, 
            params=(color_id,)
        )

        # DataFrame을 JSON 문자열로 변환 후 파싱
        df_json = df.to_json(orient="records")
        response = json.loads(df_json)[0]

        try:
            email = JWT.decode(token)
            if not email:
                print("WARN: JWT 디코딩 성공, 그러나 이메일 정보 없음")
            else:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE "user" SET hex_code=%s WHERE email=%s', 
                    (response['hex_code'], email)
                )
                conn.commit()
        except jwt.InvalidTokenError:
            print("WARN: 유효하지 않은 토큰입니다. DB 업데이트 생략.")
        except Exception as e:
            print(f"ERROR: DB 업데이트 중 예외 발생: {e}")

    return response


@app.post('/predict')
async def lipstick_predict(img: UploadFile=File(...), color_id: str = Form(None)):
    
    print("예측중")
    
    # 1. 비동기로 파일 읽기 (유일한 async I/O)
    try:
        img_byte = await img.read()
    except Exception:
        raise HTTPException(status_code=400, detail="이미지 파일을 읽을 수 없습니다.")

    # 2. CPU-bound 및 동기 I/O (Pandas/DB) 작업을 스레드 풀에서 실행
    # blocking 코드를 run_in_threadpool로 감싸 이벤트 루프 차단을 방지함
    try:
        result = await run_in_threadpool(lipstick_processor, img_byte, color_id)
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))
    except NotImplementedError:
        raise HTTPException(status_code=500, detail="서버 설정 오류: DB 연결 함수가 정의되지 않았습니다.")
    except Exception as e:
         # 다른 모든 예외를 500 에러로 처리
         print(f"Critical Error in sync_processor: {e}")
         raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")
    
    # 3. 최종 응답
    return result


# ====================[ 예외 처리 ]====================

# 404 에러 응답 커스터마이징
@app.exception_handler(404)
def error(request: Request, exc: HTTPException):
    return JSONResponse(content={"result":"잘못된 응답입니다"},status_code=404)

# 라우터 등록
app.include_router(chat)
app.include_router(user)
