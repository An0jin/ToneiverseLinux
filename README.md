# 🎨 Toneiverse (Technical Showcase)

이 리포지토리는 실제 Google Play 스토어에 출시된 AI 퍼스널 컬러 진단 서비스 **Toneiverse**의 핵심 백엔드 및 딥러닝 기술 스택을 집약한 기술 쇼케이스입니다. 본 프로젝트는 상용 서비스를 목적으로 개발되었으며, 실제 운영 환경에서의 성능과 유지보수성을 고려하여 설계되었습니다.

---

## 💎 Technical Highlights

### 1. [Fastapi(backend)](file:///home/an0jin/Documents/GitHub/ToneiverseLinux/Fastapi(backend)) - High Performance API

**Oracle Cloud** 환경에 배포되어 상용 서비스를 지탱하는 고성능 백엔드 아키텍처입니다.

- **Microservice Architecture**: Docker 컨테이너 기반의 독립적이고 확장 가능한 서버 구조.
- **Professional Model Serving**: YOLOv26 모델을 FastAPI와 최적화하여 연동, 실시간에 가까운 추론 속도 확보.
- **LLM Contextual Analysis**: Gemini API를 활용한 자연어 기반 맞춤형 뷰티 컨설팅 로직 구현.
- **Relational Data Modeling**: PostgreSQL을 활용한 체계적인 유저 데이터 및 서비스 기록 관리.

### 2. [Yolo(DL)](file:///home/an0jin/Documents/GitHub/ToneiverseLinux/Yolo(DL)) - Advanced DL Pipeline

서비스의 핵심 지능인 딥러닝 엔진입니다.

- **State-of-the-Art Architecture**: YOLOv12를 넘어선 **YOLOv26의 객체 지향(Object-Oriented) 아키텍처**를 적용하여 정교한 세그먼테이션과 분류 수행.
- **Optimized Data Engineering**: Roboflow 및 OpenCV를 활용한 고효율 학습 데이터 파이프라인 구축.
- **Production-Ready Validation**: Confusion Matrix 분석 등 검증된 성과 지표를 바탕으로 한 상용 수준의 모델링.

### 3. Data Collection - Roboflow Automation

학습 데이터의 다양성과 양을 확보하기 위해 **Roboflow Universe**의 방대한 데이터셋을 활용하였습니다.

- **Automated Pipeline**: Roboflow API를 연동하여 `Personal Color`, `Facekind`, `Lipstick` 등 성격이 다른 다수의 데이터셋을 자동으로 다운로드하고 통합하는 스크립트 구현.
- **Diverse Datasets**: 웜톤/쿨톤 분류 뿐만 아니라 얼굴형, 립스틱 발색 등 서비스에 필요한 다각도의 데이터를 수집.

### 4. Image Data Preprocessing - Dataset Engineering

수집된 이질적인 데이터셋들을 하나의 통일된 YOLO 학습 규격으로 정규화하는 전처리 과정을 거쳤습니다.

- **Unified Integration**: 서로 다른 소스의 데이터를 하나의 `datasets` 폴더로 통합하고, 클래스 인덱스를 재정의하여 레이블 일관성 확보.
- **Structure Optimization**: `images`와 `labels` 폴더 구조를 YOLO 표준에 맞춰 재배치하고, 데이터셋 간 중복 제거 및 클리닝 수행.
- **Data Augmentation**: OpenCV를 활용한 이미지 리사이징 및 정규화를 통해 모델의 범용적 성능 최적화.

---

## 🚀 Key Achievements

- **Innovative Architecture**: 최신 YOLOv26 아키텍처 적용을 통한 기술적 차별화.
- **Hybrid AI System**: 딥러닝(CV)과 LLM(NLP)을 결합한 하이브리드 인공지능 추천 시스템 구축.

---

## 🛠️ Technology Stack

| 카테고리                            | 사용 기술 (Stack)                                                                                                                                                                                                                                                                                            |
| :---------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **os**                        | ![xubuntu](https://img.shields.io/badge/-xubuntu-0044AA?style=flat&logo=xubuntu&logoColor=white)(로컬 백엔드)![Oracle Linux](https://img.shields.io/badge/-Oracle%20Linux-E95420?style=flat&logo=linux&logoColor=white)(클라우드)                                                                                |
| **IDE**                       | ![AntiGravity](https://img.shields.io/badge/-AntiGravity-418AFE?style=flat), ![dbeaver](https://img.shields.io/badge/-dbeaver-382923?style=flat&logo=dbeaver&logoColor=white), ![vim](https://img.shields.io/badge/-vim-019733?style=flat&logo=vim&logoColor=white)                                                |
| **Programming Language**      | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white)                                                                                                                                                                                                                  |
| **Programming Collection**    | ![Roboflow](https://img.shields.io/badge/-roboflow-6706CE?style=flat&logo=roboflow&logoColor=white)                                                                                                                                                                                                            |
| **Programming Preprocessing** | ![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)![markdown](https://img.shields.io/badge/-markdown-000000?style=flat&logo=markdown&logoColor=white)![beautifulsoup](https://img.shields.io/badge/-beautifulsoup-005000?style=flat&logo=beautifulsoup&logoColor=white) |
| **Backend**                   | ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat&logo=docker&logoColor=white)           |
| **AI & Deep Learning**        | ![YOLOv26](https://img.shields.io/badge/-YOLOv26-111F68?style=flat&logo=ultralytics&logoColor=white) ![Gemini](https://img.shields.io/badge/-Gemini%20API-8E75B2?style=flat&logo=googlegemini&logoColor=white)                                                                                                   |
