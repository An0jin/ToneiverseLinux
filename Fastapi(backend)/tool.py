import hashlib, os, smtplib, datetime
from io import BytesIO
from abc import ABC, abstractmethod
import pandas as pd, numpy as np, cv2, markdown, psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from jose import jwt
from ultralytics import YOLO
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool
from email.mime.text import MIMEText
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import base64

# .env 환경 변수 로드
load_dotenv()

def connect():
    """PostgreSQL 데이터베이스 연결 객체 생성"""
    return psycopg2.connect(
        host=os.getenv("host"),
        port=int(os.getenv("port", 5432)),
        user=os.getenv("user"),
        password=os.getenv("password"),
        dbname=os.getenv("dbname")
    )

def to_response(x):
    """결과 데이터를 API 공통 JSON 규격({'result': ...})으로 변환"""
    if isinstance(x, pd.DataFrame):
        return {"result": x.to_dict(orient="records")}
    return {"result": x.tolist() if hasattr(x, 'tolist') else x}

def hashpw(pw: str) -> str:
    """비밀번호를 SHA256으로 해싱하여 16진수 문자열로 반환"""
    return hashlib.sha256(pw.encode()).hexdigest()

class JWT:
    """JWT 토큰 생성 및 검증 유틸리티 클래스"""
    @staticmethod
    def encode(email: str, pw: str) -> str:
        """이메일과 해시된 비밀번호를 페이로드로 담아 JWT 토큰 생성"""
        return jwt.encode({'email': email, 'pw': pw}, os.getenv("jwtSecret"), algorithm='HS256')

    @staticmethod
    def decode(token: str):
        """JWT 토큰을 디코딩하여 페이로드 반환 (유효하지 않을 경우 None)"""
        try:
            return jwt.decode(token, os.getenv("jwtSecret"), algorithms=['HS256'])
        except Exception:
            return None

class LLM(ABC):
    """Google Gemini 기반 LLM 추상 기본 클래스 (웹 검색 도구 포함)"""
    def __init__(self):
        api_key = os.getenv("gemini")
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key)
        self.search = DuckDuckGoSearchRun()
        self.content: AIMessage

    @abstractmethod
    def invoke(self, *args, **kwargs):
        """하위 클래스에서 구현해야 할 LLM 호출 인터페이스"""
        pass

    def rm_markdown(self, text: str) -> str:
        """마크다운 태그를 제거하고 순수 텍스트만 추출"""
        return BeautifulSoup(markdown.markdown(text), 'html.parser').get_text()

    @property
    def text(self) -> str:
        """추출된 텍스트 프로퍼티"""
        return self.content[0]['text']

class TextLLM(LLM):
    """사용자 상황 및 퍼스널컬러 후보군에 따른 맞춤형 립스틱 추천 텍스트 LLM 클래스"""
    def invoke(self, text: str, colors: list, year: int, sex: str) -> str:
        """나이, 성별, 상황, 립스틱 컬러 목록 및 웹 검색 트렌드를 종합하여 최적의 컬러 추천"""
        age = datetime.datetime.now().year - year + 1
        system_instruction = f"""You are a highly professional beauty consultant for the 'Toneiverse' app.
Recommend the best lipstick color from: {colors}.
Biological Sex: {sex}, Age: {age}.
Output Rules: Respond in Korean. First line MUST be HEX code (e.g. #FF5733). Provide logical explanation."""
        
        # 최신 트렌드 웹 검색 (검색 실패 시 빈 문자열 처리)
        try:
            search_result = self.search.run(f"best lipstick trend for {text}")
        except Exception:
            search_result = ""

        # 사용자 요청 및 검색 참고 정보 구성
        user_content = f"User Request: {text}\nReference Info:\n{search_result}" if search_result else text

        # LLM 호출
        self.content = self.llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_content)
        ]).content
        
        return self.rm_markdown(self.text)

class CVLLM(LLM):
    """립스틱 이미지 검출(YOLO) 및 퍼스널컬러 적합도 분석 비전 LLM 클래스"""
    def __init__(self):
        super().__init__()
        self.model = YOLO('lipstick.onnx')

    def cv_processor(self, img_byte: bytes, color_id: str) -> str:
        """이미지에서 립스틱 영역을 탐지/크롭 후 Gemini Vision에 질의하여 한글 분석 결과 반환"""
        img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
        results = self.model.predict(img_pil, iou=0.1, agnostic_nms=True, imgsz=640)[0]
        
        # 립스틱 객체 검출 수 검증
        if len(results.boxes) == 0:
            return "립스틱을 찾을 수 없습니다."
        if len(results.boxes) > 1:
            return "립스틱 하나만 찍힌 사진을 업로드해주세요."

        # 검출된 립스틱 바운딩 박스 크롭 및 JPEG 인코딩
        x1, y1, x2, y2 = map(int, results.boxes[0].xyxy[0])
        crop = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)[y1:y2, x1:x2]

        is_success, buffer = cv2.imencode(".jpg", crop)
        if not is_success:
            return "이미지 처리 중 오류가 발생했습니다."

        # Base64 이미지와 함께 멀티모달 LLM 호출
        self.content = self.llm.invoke(
            [
                SystemMessage(content="""You are an expert beauty analyst specializing in color science and personal color theory.
Analyze the provided product image (lipstick) and determine its suitability for a specific personal color type.
Always provide the final response in Korean."""),
                HumanMessage(
                    content=[
                        {"type": "text", "text": f"Analyze if this lipstick is suitable for someone with a '{color_id}' personal color. Provide a detailed professional opinion in Korean."},
                        {"type": "image", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"}}
                    ]
                )
            ]
        ).content
        return self.rm_markdown(self.text)

    async def invoke(self, color_id: str, images: UploadFile):
        """업로드된 이미지 파일을 읽고 비동기 스레드풀에서 cv_processor 실행"""
        img_byte = await images.read()
        return await run_in_threadpool(self.cv_processor, img_byte, color_id)

def SendEmail(email: str, subject: str, body: str):
    """Gmail SMTP를 통해 사용자에게 안내 이메일 발송"""
    my_email, my_pw = "an0jin0106@gmail.com", os.getenv("stmplibpw")
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'], msg['From'] = subject, my_email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as conn:
            conn.starttls()
            conn.login(my_email, my_pw)
            conn.send_message(msg, from_addr=my_email, to_addrs=[email])
    except Exception as e:
        print(f"이메일 전송 오류: {e}")