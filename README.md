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

---

## 🚀 Key Achievements

- **Innovative Architecture**: 최신 YOLOv26 아키텍처 적용을 통한 기술적 차별화.
- **Hybrid AI System**: 딥러닝(CV)과 LLM(NLP)을 결합한 하이브리드 인공지능 추천 시스템 구축.

---

## 🛠️ Technology Stack

| 카테고리                       | 사용 기술 (Stack)                                                                                                                                                                                                                                                                                                    |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Infrastructure**       | ![Xubuntu](https://img.shields.io/badge/-Xubuntu-2D2D2D?style=flat&logo=xubuntu&logoColor=white) ![Oracle Cloud](https://img.shields.io/badge/-Oracle%20Cloud-F80000?style=flat&logo=oracle&logoColor=white) ![Google](https://img.shields.io/badge/-Deployed%20on%20Google-4285F4?style=flat&logo=google&logoColor=white) |
| **Programming Language** | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white)                                                                                                                                                                                                                          |
| **Backend**              | ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat&logo=docker&logoColor=white)                   |
| **AI & Deep Learning**   | ![YOLOv26](https://img.shields.io/badge/YOLOv26-OO--Architecture-blue) ![Gemini](https://img.shields.io/badge/-Gemini%20API-8E75B2?style=flat&logo=googlegemini&logoColor=white) ![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)                                             |
