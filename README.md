# 🤖 Text-to-SQL Chatbot with Spider Dataset

[한국어](#한국어) | [English](#english)

## 데모 비디오 링크/Demo Video Link: https://www.youtube.com/watch?v=ic68Z8Q7xU4

---

## 한국어

### 📋 프로젝트 개요

Spider 데이터셋을 활용한 자연어-SQL 변환 챗봇 시스템입니다. Google Gemini 2.5 Flash API를 사용하여 자연어 질문을 SQL 쿼리로 변환하고, Supabase PostgreSQL 데이터베이스에서 실행합니다.

### 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │───▶│  FastAPI Server │───▶│ Supabase PostgreSQL │
│  (Frontend)     │    │  (Backend)      │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Gemini API    │
                       │  (2.5 Flash)    │
                       └─────────────────┘
```

### 🚀 빠른 시작

#### 1. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt


#### 2. 데이터베이스 초기화
```bash
python init_db.py
```

#### 3. 앱 실행
```bash
streamlit run app_integrated.py
```

### 🎯 주요 기능

- **🌍 다국어 지원**: 한국어/영어 인터페이스
- **🕷️ Spider 데이터셋**: 10개의 다양한 도메인 데이터베이스
- **🤖 AI 기반 SQL 생성**: Gemini 2.5 Flash로 자연어를 SQL로 변환
- **📊 실시간 결과**: 쿼리 실행 및 결과 시각화
- **💬 대화형 인터페이스**: 채팅 기록 및 설명 제공
- **☁️ 클라우드 배포**: Streamlit Cloud + Supabase 지원

### 📊 포함된 데이터베이스

| 데이터베이스 | 도메인 | 테이블 수 | 설명 |
|-------------|--------|----------|------|
| `academic` | 학술 | 15 | 저자, 논문, 학회 정보 |
| `college_2` | 교육 | 11 | 강의실, 학과, 수강 정보 |
| `flight_company` | 교통 | 3 | 공항, 항공사, 항공편 |
| `department_store` | 소매 | 14 | 매장, 고객, 주문 정보 |
| `storm_record` | 기상 | 3 | 폭풍, 지역, 피해 정보 |
| `race_track` | 스포츠 | 2 | 경주, 트랙 정보 |
| `pilot_record` | 항공 | 3 | 조종사, 항공기, 기록 |
| `body_builder` | 피트니스 | 2 | 보디빌더, 인물 정보 |
| `perpetrator` | 범죄 | 2 | 가해자, 인물 정보 |
| `icfp_1` | 학술 | 4 | 기관, 저자, 논문 정보 |

### 💡 예시 질문

**한국어:**
- "academic 데이터베이스의 모든 저자를 보여주세요"
- "college_2에서 컴퓨터 과학과 학생들은 누구인가요?"
- "flight_company의 모든 공항 정보를 알려주세요"
- "department_store에서 가장 많이 주문한 고객은 누구인가요?"

**English:**
- "Show me all authors in the academic database"
- "Who are the computer science students in college_2?"
- "List all airports in flight_company"
- "Which customer has the most orders in department_store?"

### 🗂️ 프로젝트 구조

```
chatbot_demo_text_2_sql/
├── app_integrated.py      # 통합 앱 (FastAPI + Streamlit)
├── init_db.py            # 데이터베이스 초기화
├── requirements.txt      # Python 의존성
├── packages.txt         # 시스템 패키지
├── .env                 # 환경 변수
├── .streamlit/
│   └── config.toml      # Streamlit 설정
├── spider/
│   └── evaluation_examples/
│       └── examples/
│           └── tables.json  # Spider 스키마
└── README.md           # 이 파일
```

### 🔧 API 엔드포인트

- `GET /`: 서버 상태 확인
- `GET /health`: 헬스 체크 (DB 연결 포함)
- `GET /schema`: 데이터베이스 스키마 조회
- `POST /query`: 자연어 질의 처리

### 🌐 배포

#### Streamlit Cloud 배포
1. GitHub 리포지토리에 코드 업로드
2. [share.streamlit.io](https://share.streamlit.io)에서 새 앱 생성
3. 환경 변수 설정:
   - `DATABASE_URL`: Supabase PostgreSQL URL
   - `GEMINI_API_KEY`: Google Gemini API 키

### 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: Supabase PostgreSQL
- **AI Model**: Google Gemini 2.5 Flash
- **Dataset**: Spider (Text-to-SQL)
- **Deployment**: Streamlit Cloud

### 📝 License

This project is licensed under the MIT License.

### 📊 Dataset Citation

This project uses the **Spider** dataset for Text-to-SQL tasks:

**Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Tasks**

- **Authors**: Tao Yu, Rui Zhang, Kai Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James Ma, Irene Li, Qingning Yao, Shanelle Roman, Ziyu Zhang, Dragomir Radev
- **Institution**: Yale University & Salesforce Research  
- **Year**: 2018
- **Website**: [https://yale-lily.github.io/spider](https://yale-lily.github.io/spider)
- **Paper**: [https://arxiv.org/abs/1809.08887](https://arxiv.org/abs/1809.08887)

**BibTeX Citation:**
```bibtex
@inproceedings{yu2018spider,
  title={Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-sql tasks},
  author={Yu, Tao and Zhang, Rui and Yang, Kai and Yasunaga, Michihiro and Wang, Dongxu and Li, Zifan and Ma, James and Li, Irene and Yao, Qingning and Roman, Shanelle and others},
  booktitle={Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
  pages={3911--3921},
  year={2018}
}
```

---

## English

### 📋 Project Overview

A natural language to SQL chatbot system using the Spider dataset. It converts natural language questions to SQL queries using Google Gemini 2.5 Flash API and executes them on Supabase PostgreSQL database.

### 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │───▶│  FastAPI Server │───▶│ Supabase PostgreSQL │
│  (Frontend)     │    │  (Backend)      │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Gemini API    │
                       │  (2.5 Flash)    │
                       └─────────────────┘
```

### 🚀 Quick Start

#### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt


#### 2. Initialize Database
```bash
python init_db.py
```

#### 3. Run Application
```bash
streamlit run app_integrated.py
```

### 🎯 Key Features

- **🌍 Multi-language Support**: Korean/English interface
- **🕷️ Spider Dataset**: 10 diverse domain databases
- **🤖 AI-powered SQL Generation**: Natural language to SQL with Gemini 2.5 Flash
- **📊 Real-time Results**: Query execution and result visualization
- **💬 Interactive Interface**: Chat history and explanations
- **☁️ Cloud Deployment**: Streamlit Cloud + Supabase support

### 📊 Included Databases

| Database | Domain | Tables | Description |
|----------|--------|--------|-------------|
| `academic` | Academic | 15 | Authors, papers, conferences |
| `college_2` | Education | 11 | Classrooms, departments, courses |
| `flight_company` | Transportation | 3 | Airports, airlines, flights |
| `department_store` | Retail | 14 | Stores, customers, orders |
| `storm_record` | Weather | 3 | Storms, regions, damages |
| `race_track` | Sports | 2 | Races, tracks |
| `pilot_record` | Aviation | 3 | Pilots, aircraft, records |
| `body_builder` | Fitness | 2 | Bodybuilders, people |
| `perpetrator` | Crime | 2 | Perpetrators, people |
| `icfp_1` | Academic | 4 | Institutions, authors, papers |

### 💡 Example Questions

**Korean:**
- "academic 데이터베이스의 모든 저자를 보여주세요"
- "college_2에서 컴퓨터 과학과 학생들은 누구인가요?"
- "flight_company의 모든 공항 정보를 알려주세요"
- "department_store에서 가장 많이 주문한 고객은 누구인가요?"

**English:**
- "Show me all authors in the academic database"
- "Who are the computer science students in college_2?"
- "List all airports in flight_company"
- "Which customer has the most orders in department_store?"

### 🗂️ Project Structure

```
chatbot_demo_text_2_sql/
├── app_integrated.py      # Integrated app (FastAPI + Streamlit)
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
├── packages.txt         # System packages
├── .env                 # Environment variables
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── spider/
│   └── evaluation_examples/
│       └── examples/
│           └── tables.json  # Spider schema
└── README.md           # This file
```

### 🔧 API Endpoints

- `GET /`: Server status check
- `GET /health`: Health check (including DB connection)
- `GET /schema`: Database schema retrieval
- `POST /query`: Natural language query processing

### 🌐 Deployment

#### Streamlit Cloud Deployment
1. Upload code to GitHub repository
2. Create new app on [share.streamlit.io](https://share.streamlit.io)
3. Set environment variables:
   - `DATABASE_URL`: Supabase PostgreSQL URL
   - `GEMINI_API_KEY`: Google Gemini API key

### 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: Supabase PostgreSQL
- **AI Model**: Google Gemini 2.5 Flash
- **Dataset**: Spider (Text-to-SQL)
- **Deployment**: Streamlit Cloud

### 📝 License

This project is licensed under the MIT License.

### 📊 Dataset Citation

This project uses the **Spider** dataset for Text-to-SQL tasks:

**Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Tasks**

- **Authors**: Tao Yu, Rui Zhang, Kai Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James Ma, Irene Li, Qingning Yao, Shanelle Roman, Ziyu Zhang, Dragomir Radev
- **Institution**: Yale University & Salesforce Research  
- **Year**: 2018
- **Website**: [https://yale-lily.github.io/spider](https://yale-lily.github.io/spider)
- **Paper**: [https://arxiv.org/abs/1809.08887](https://arxiv.org/abs/1809.08887)

**BibTeX Citation:**
```bibtex
@inproceedings{yu2018spider,
  title={Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-sql tasks},
  author={Yu, Tao and Zhang, Rui and Yang, Kai and Yasunaga, Michihiro and Wang, Dongxu and Li, Zifan and Ma, James and Li, Irene and Yao, Qingning and Roman, Shanelle and others},
  booktitle={Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
  pages={3911--3921},
  year={2018}
}
```

---

## 🚀 Powered by

- **Google Gemini 2.5 Flash** - AI Language Model
- **Supabase** - PostgreSQL Database
- **Streamlit** - Web Framework
- **FastAPI** - Backend API
- **Spider Dataset** - Text-to-SQL Benchmark
