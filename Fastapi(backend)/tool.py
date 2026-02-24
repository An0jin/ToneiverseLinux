from google.genai import types
from ultralytics import YOLO
import hashlib
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from PIL import Image
import markdown
import numpy as np
from bs4 import BeautifulSoup
import cv2
load_dotenv()
from starlette.concurrency import run_in_threadpool
from abc import ABC, abstractmethod
from jose import JWTError,jwt
from fastapi import UploadFile
from email.mime.text import MIMEText
import smtplib
from google import genai
import datetime
from io import BytesIO
    
def connect():
    """데이터베이스에 접근하는 함수"""
    return psycopg2.connect(host=os.getenv("host"),
                            port=int(os.getenv("port")),
                            user=os.getenv("user"),
                            password=os.getenv("password"),
                            dbname=os.getenv("dbname"))


def to_response(x):
    """응답을 JSON 형식으로 변환하는 함수"""
    if isinstance(x, pd.DataFrame):
        return {"result": x.to_dict(orient="records")}
    elif hasattr(x, 'tolist'):  # NumPy 배열 처리
        return {"result": x.tolist()}
    else:
        return {"result": x}


def hashpw(pw):
    """
    패스워드를 해싱합니다.
    """
    return hashlib.sha256(pw.encode()).hexdigest()

class JWT:
    @staticmethod
    def encode(email):
        return jwt.encode({'email':email}, os.getenv("jwtSecret"), algorithm='HS256')
    @staticmethod
    def decode(token):
        try:
            return jwt.decode(token, os.getenv("jwtSecret"), algorithms=['HS256'])['email']
        except:
            return None
class LLM(ABC):
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("gemini"))
    @abstractmethod
    def invoke(self, *args, **kwargs):pass
    def rm_markdown(self,text):
        result_text=markdown.markdown(text)
        soup=BeautifulSoup(result_text,'html.parser')
        return soup.get_text()

class CVLLM(LLM):
    def __init__(self):
        self.model = YOLO('lipstick.onnx')
        super().__init__()
    def cv_processor(self,img_byte: bytes, color_id: str):
        img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
        results = self.model.predict(img_pil, iou=0.1, agnostic_nms=True, imgsz=640)
        result = results[0]
        result.show()
        num_boxes = len(result.boxes)
        if num_boxes == 0:
            return "립스틱을 찾을 수 없습니다."
        elif num_boxes > 1: 
            return "립스틱 하나만 찍힌 사진을 업로드해주세요."

        tensor = result.boxes[0].xyxy[0]
        x1, y1, x2, y2 = map(int, tensor)
        
        img_np = np.array(img_pil)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        crop = img_bgr[y1:y2, x1:x2]

        is_success, buffer = cv2.imencode(".jpg", crop)
        if is_success:
            final_image = BytesIO(buffer).getvalue()
        else:
            return "이미지 처리 중 오류가 발생했습니다."

        # 5. Gemini 호출
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=final_image,
                    mime_type='image/jpeg',
                ),
                f"Analyze if this lipstick is suitable for someone with a '{color_id}' personal color. Provide a detailed professional opinion in Korean."
            ],
            config={
                "tools": [{"google_search": {}}],
                "system_instruction": """You are an expert beauty analyst specializing in color science and personal color theory. 
    Your task is to analyze the provided product image (lipstick) and determine its suitability for a specific personal color type.

    Guidelines:
    1. Color Analysis: Extract the dominant hue, saturation, and value from the lipstick crop.
    2. Harmony Evaluation: Compare the extracted color profile with the user's provided personal color type.
    3. Logical Reasoning: Explain why the color matches or clashes, considering undertones (warm/cool) and clarity (clear/muted).
    4. Professionalism: Maintain a sophisticated, helpful, and objective tone.
    5. Language: Always provide the final response in Korean as per the user's primary language."""
            }
        )
        result=self.rm_markdown(response.text)
        print(f"result is {result}")
        return result



    async def invoke(self, color_id, images: UploadFile):
        img_byte = await images.read()
        result = await run_in_threadpool(self.cv_processor, img_byte, color_id)
        return result


class TextLLM(LLM):
    def __init__(self):
        super().__init__()

    def invoke(self, text, colors, year, sex):
        age=datetime.datetime.now().year-year+1
        # 영어 시스템 지침 (한국어 답변 강제 포함)
        system_instruction = f"""
        You are a highly professional beauty consultant for the 'Toneiverse' app.
        Your goal is to recommend the best lipstick color from the provided list: {colors}.

        Consider these specific biological and situational factors:
        1. Biological Sex ({sex}): Adjust recommendations based on skin thickness and sebum levels typical of this sex.
        2. Age ({age}): Account for skin moisture retention and texture changes associated with age.
        3. Situation (TPO): Use Google Search to find current beauty trends or lighting conditions for the user's specific situation (e.g., 'interview', 'festival', 'wedding').

        Output Rules:
        - **Language**: You MUST respond in Korean (한국어로 상세히 답변하십시오).
        - **Format**: Start with the HEX color code (e.g., #FF5733) on the first line.
        - **Reasoning**: Provide a logical explanation in Korean focusing on (1) personal color harmony, (2) skin suitability based on {sex} and {age}, and (3) situational appropriateness.
        """

        result = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config={
                "tools": [{"google_search": {}}], # 실시간 검색 도구 활성화
                "system_instruction": system_instruction
            }
        )
        return self.rm_markdown(result.text)

def SendEmail(email,subject,body):
    my_email = "an0jin0106@gmail.com"
    my_password = os.getenv("stmplibpw")
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = my_email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as conn: # 표준 포트 587 사용
            conn.starttls()
            conn.login(user=my_email, password=my_password)
            conn.send_message(msg, from_addr=my_email, to_addrs=[email])
            print("이메일 전송 성공: UTF-8 인코딩 처리 완료")
    except smtplib.SMTPAuthenticationError:
        print("오류: SMTP 인증 실패. G메일 2단계 인증 및 앱 비밀번호 사용 여부를 확인하세요.")
    except Exception as e:
        print(f"오류 발생: {e}")
