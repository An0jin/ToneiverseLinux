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
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.capabilities import WebSearch
from pydantic_ai.run import AgentRunResult

# .env 환경 변수 로드
load_dotenv()


def connect():
    """
    PostgreSQL 데이터베이스 연결 객체를 생성하여 반환합니다.
    
    환경변수:
        host: DB 호스트 주소
        port: DB 포트 (기본값: 5432)
        user: DB 사용자명
        password: DB 패스워드
        dbname: 데이터베이스명
    """
    return psycopg2.connect(
        host=os.getenv("host"),
        port=int(os.getenv("port", 5432)),
        user=os.getenv("user"),
        password=os.getenv("password"),
        dbname=os.getenv("dbname")
    )


def to_response(x):
    """
    결과 데이터를 API 공통 JSON 규격({'result': ...}) 형태로 변환합니다.
    
    Args:
        x: 변환할 원본 데이터 (DataFrame, ndarray, 단일 값 등)
    Returns:
        dict: 표준화된 결과 딕셔너리
    """
    if isinstance(x, pd.DataFrame):
        return {"result": x.to_dict(orient="records")}
    return {"result": x.tolist() if hasattr(x, 'tolist') else x}


def hashpw(pw: str) -> str:
    """
    비밀번호 문자열을 SHA-256 해시 함수로 암호화하여 16진수 문자열로 반환합니다.
    
    Args:
        pw (str): 평문 비밀번호
    Returns:
        str: 64자리 16진수 해시 문자열
    """
    return hashlib.sha256(pw.encode()).hexdigest()


class JWT:
    """JWT(JSON Web Token) 생성 및 검증을 담당하는 유틸리티 클래스"""
    
    @staticmethod
    def encode(email: str, pw: str) -> str:
        """
        사용자 이메일과 해시된 비밀번호를 페이로드에 담아 HS256 알고리즘 기반의 JWT 토큰을 발행합니다.
        
        Args:
            email (str): 사용자 이메일
            pw (str): 암호화된 비밀번호
        Returns:
            str: 인코딩된 JWT 토큰 문자열
        """
        return jwt.encode({'email': email, 'pw': pw}, os.getenv("jwtSecret"), algorithm='HS256')

    @staticmethod
    def decode(token: str):
        """
        JWT 토큰을 검증 및 디코딩하여 페이로드 딕셔너리를 반환합니다.
        
        Args:
            token (str): 검증할 JWT 토큰
        Returns:
            dict | None: 디코딩 성공 시 페이로드 dict, 서명 위조나 만료 등 오류 시 None 반환
        """
        try:
            return jwt.decode(token, os.getenv("jwtSecret"), algorithms=['HS256'])
        except Exception:
            return None


class LLM(ABC):
    """Google Gemini 기반 LLM 추상 기본 클래스 (웹 검색 에이전트 및 텍스트 후처리 지원)"""

    def __init__(self):
        """Gemini API 프로바이더 및 모델 인스턴스 초기화"""
        api_key = os.getenv("gemini")
        self._provider = GoogleProvider(api_key=api_key)
        # Google Gemini 2.0 Flash 모델 설정 (멀티모달 및 고속 응답 최적화)
        self._model = GoogleModel(model_name='gemini-3.1-flash-lite', provider=self._provider)
        self._agent: Agent = None
        self._content: AgentRunResult = None

    @abstractmethod
    def invoke(self, *args, **kwargs):
        """하위 클래스에서 각 비즈니스 로직에 맞게 구현해야 할 실행 추상 인터페이스"""
        pass

    @property
    def agent(self) -> Agent:
        """현재 설정된 Pydantic AI Agent 객체 반환"""
        return self._agent

    @agent.setter
    async def agent(self, instructions: str):
        """
        지정된 시스템 지침(instructions)과 DuckDuckGo 웹 검색 역량을 가진 Agent를 구성합니다.
        
        Args:
            instructions (str): 에이전트에 부여할 페르소나 및 응답 규칙
        """
        self._agent = Agent(
            self._model,
            capabilities=[WebSearch(native=False, local='duckduckgo')],
            instructions=instructions
        )

    def rm_markdown(self, text: str) -> str:
        """
        마크다운 형식의 텍스트를 HTML로 파싱한 뒤 순수 텍스트(PlainText)만 추출하여 반환합니다.
        
        Args:
            text (str): 마크다운이 포함된 원본 텍스트
        Returns:
            str: 포맷팅 태그가 제거된 순수 텍스트
        """
        return BeautifulSoup(markdown.markdown(text), 'html.parser').get_text()

    @property
    def text(self) -> str:
        """Agent 실행 결과(AgentRunResult)에서 최종 출력 텍스트를 안전하게 반환"""
        return self._content.output if self._content else ""


class TextLLM(LLM):
    """사용자의 퍼스널컬러 후보군 및 상황에 맞춘 립스틱 색상 추천 텍스트 LLM 클래스"""

    def __init__(self):
        super().__init__()

    async def invoke(self, text: str, colors: list, year: int, sex: str) -> str:
        """
        사용자의 나이, 성별, 요청 상황 및 추천 대상 립스틱 컬러 목록을 종합 분석하여
        최적의 립스틱 HEX 코드 및 추천 사유를 반환합니다.
        
        주의: main.py 라우터에서 동기(sync) 방식으로 호출되므로 run_sync를 사용하여 동기 실행합니다.
        
        Args:
            text (str): 사용자 질의 또는 상황 설명
            colors (list): 추천 후보군 립스틱 HEX 코드 리스트
            year (int): 사용자 출생 연도
            sex (str): 사용자 성별
        Returns:
            str: 첫 줄에 HEX 코드, 이어서 추천 근거가 포함된 한글 텍스트
        """
        # 현재 연도 기준 한국식 나이 계산
        age = datetime.datetime.now().year - year + 1

        # Toneiverse 뷰티 컨설턴트 페르소나 및 출력 규칙 설정
        self.agent = f"""You are a highly professional beauty consultant for the 'Toneiverse' app.
Recommend the best lipstick color from: {colors}.
Biological Sex: {sex}, Age: {age}.
Output Rules: Respond in Korean. First line MUST be HEX code (e.g. #FF5733). Provide logical explanation."""

        # LLM 에이전트 동기 호출 (필요시 내장된 DuckDuckGo 웹 검색 수행)
        self._content = await self.agent.run([f"User Request: {text}"])
        
        return self.rm_markdown(self.text)


class CVLLM(LLM):
    """YOLO 기반 립스틱 영역 탐지 및 Gemini Vision 기반 퍼스널컬러 적합도 분석 클래스"""

    def __init__(self):
        super().__init__()
        # 립스틱 객체 검출을 위한 YOLO ONNX 모델 로드 (self._model과의 이름 충돌 방지를 위해 yolo_model 사용)
        self.yolo_model = YOLO('lipstick.onnx')
        # 비전 분석 전용 시스템 프롬프트 설정
        self.agent = """You are an expert beauty analyst specializing in color science and personal color theory.
Analyze the provided product image (lipstick) and determine its suitability for a specific personal color type.
Always provide the final response in Korean."""

    async def cv_processor(self, img_byte: bytes, color_id: str) -> str:
        """
        [동기 작업 함수] 이미지 바이트에서 립스틱을 검출 및 크롭하고, 
        멀티모달 Gemini 모델에 전달하여 퍼스널컬러와의 어울림을 분석합니다.
        
        Args:
            img_byte (bytes): 업로드된 원본 이미지 파일 바이트 데이터
            color_id (str): 대상 퍼스널컬러 식별자 (예: '봄 웜톤', '여름 쿨톤' 등)
        Returns:
            str: 립스틱 검출 여부 안내 또는 LLM의 전문 분석 의견
        """
        # 이미지 바이트를 PIL RGB 이미지로 변환
        img_pil = Image.open(BytesIO(img_byte)).convert('RGB')
        
        # YOLOv8 ONNX 모델로 립스틱 바운딩 박스 추론
        results = self.yolo_model.predict(img_pil, iou=0.1, agnostic_nms=True, imgsz=640)[0]
        
        # 검출된 립스틱 수 유효성 검증
        if len(results.boxes) == 0:
            return "립스틱을 찾을 수 없습니다."
        if len(results.boxes) > 1:
            return "립스틱 하나만 찍힌 사진을 업로드해주세요."

        # 검출된 첫 번째 립스틱 영역 좌표 크롭 (OpenCV BGR 포맷 변환)
        x1, y1, x2, y2 = map(int, results.boxes[0].xyxy[0])
        crop = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)[y1:y2, x1:x2]

        # 크롭된 영역을 JPEG 바이너리로 인코딩
        is_success, buffer = cv2.imencode(".jpg", crop)
        if not is_success:
            return "이미지 처리 중 오류가 발생했습니다."

        # 멀티모달 Gemini 호출: run_sync를 사용하여 동기식으로 응답 수신 (buffer.tobytes() 바이트열 변환)
        self._content = await self.agent.run(
            [
                f"Analyze if this lipstick is suitable for someone with a '{color_id}' personal color. Provide a detailed professional opinion in Korean.",
                BinaryContent(data=buffer.tobytes(), media_type='image/jpeg')
            ]
        )
        return self.rm_markdown(self.text)

    async def invoke(self, color_id: str, images: UploadFile):
        """
        FastAPI의 UploadFile에서 비동기로 바이트를 읽어온 뒤,
        CPU 집약적인 cv_processor를 별도 스레드풀에서 안전하게 실행합니다.
        
        Args:
            color_id (str): 퍼스널컬러 ID
            images (UploadFile): 업로드된 립스틱 이미지 파일 객체
        Returns:
            str: 분석 결과 한글 텍스트
        """
        img_byte = await images.read()
        return await run_in_threadpool(self.cv_processor, img_byte, color_id)


def SendEmail(email: str, subject: str, body: str):
    """
    Gmail SMTP 서버(포트 587, TLS)를 통해 지정된 수신자에게 안내 이메일을 발송합니다.
    
    Args:
        email (str): 수신자 이메일 주소
        subject (str): 메일 제목
        body (str): 메일 본문 내용 (UTF-8 Plain Text)
    """
    my_email = "an0jin0106@gmail.com"
    # stmplibpw 또는 smtplibpw 환경변수에서 앱 비밀번호 로드
    my_pw = os.getenv("smtplibpw") or os.getenv("stmplibpw")
    
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'], msg['From'] = subject, my_email
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as conn:
            conn.starttls()
            conn.login(my_email, my_pw)
            conn.send_message(msg, from_addr=my_email, to_addrs=[email])
    except Exception as e:
        print(f"이메일 전송 오류: {e}")