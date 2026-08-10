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
from google import genai

load_dotenv()

def connect():
    """데이터베이스 연결"""
    return psycopg2.connect(
        host=os.getenv("host"),
        port=int(os.getenv("port", 5432)),
        user=os.getenv("user"),
        password=os.getenv("password"),
        dbname=os.getenv("dbname")
    )

def to_response(x):
    """응답을 JSON 규격으로 변환"""
    if isinstance(x, pd.DataFrame):
        return {"result": x.to_dict(orient="records")}
    return {"result": x.tolist() if hasattr(x, 'tolist') else x}

def hashpw(pw: str) -> str:
    """패스워드 해싱"""
    return hashlib.sha256(pw.encode()).hexdigest()

class JWT:
    @staticmethod
    def encode(email: str, pw: str) -> str:
        return jwt.encode({'email': email, 'pw': pw}, os.getenv("jwtSecret"), algorithm='HS256')

    @staticmethod
    def decode(token: str):
        try:
            return jwt.decode(token, os.getenv("jwtSecret"), algorithms=['HS256'])
        except Exception:
            return None

class LLM(ABC):
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("gemini"))

    @abstractmethod
    def invoke(self, *args, **kwargs): pass

    def rm_markdown(self, text: str) -> str:
        return BeautifulSoup(markdown.markdown(text), 'html.parser').get_text()

class CVLLM(LLM):
    def __init__(self):
        super().__init__()
        self.model = YOLO('lipstick.onnx')

    def cv_processor(self, img_byte: bytes, color_id: str) -> str:
        img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
        results = self.model.predict(img_pil, iou=0.1, agnostic_nms=True, imgsz=640)[0]
        if len(results.boxes) == 0:
            return "립스틱을 찾을 수 없습니다."
        if len(results.boxes) > 1:
            return "립스틱 하나만 찍힌 사진을 업로드해주세요."

        x1, y1, x2, y2 = map(int, results.boxes[0].xyxy[0])
        crop = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)[y1:y2, x1:x2]

        is_success, buffer = cv2.imencode(".jpg", crop)
        if not is_success:
            return "이미지 처리 중 오류가 발생했습니다."

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            system_instruction="""You are an expert beauty analyst specializing in color science and personal color theory.
Analyze the provided product image (lipstick) and determine its suitability for a specific personal color type.
Always provide the final response in Korean.""",
            input=[
                {"type": "text", "text": f"Analyze if this lipstick is suitable for someone with a '{color_id}' personal color. Provide a detailed professional opinion in Korean."},
                {"type": "image", "data": BytesIO(buffer).getvalue(), "mime_type": "image/jpeg"}
            ]
        )
        return self.rm_markdown(response.output_text)

    async def invoke(self, color_id: str, images: UploadFile):
        img_byte = await images.read()
        return await run_in_threadpool(self.cv_processor, img_byte, color_id)

class TextLLM(LLM):
    def invoke(self, text: str, colors: list, year: int, sex: str) -> str:
        age = datetime.datetime.now().year - year + 1
        system_instruction = f"""You are a highly professional beauty consultant for the 'Toneiverse' app.
Recommend the best lipstick color from: {colors}.
Biological Sex: {sex}, Age: {age}.
Output Rules: Respond in Korean. First line MUST be HEX code (e.g. #FF5733). Provide logical explanation."""

        result = self.client.interactions.create(
            model="gemini-3.6-flash",
            input=text,
            system_instruction=system_instruction
        )
        return self.rm_markdown(result.output_text)

def SendEmail(email: str, subject: str, body: str):
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

