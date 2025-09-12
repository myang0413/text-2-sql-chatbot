"""
통합 앱: FastAPI + Streamlit을 하나의 프로세스에서 실행
Supabase PostgreSQL 연결 지원
"""
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time
import os
import sqlite3
import psycopg2
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# FastAPI 앱 설정
api_app = FastAPI(title="Text-to-SQL API", version="1.0.0")

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini 클라이언트 초기화
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_db_connection():
    """Get database connection - PostgreSQL for production, SQLite for fallback"""
    database_url = os.getenv("DATABASE_URL")
    
    # Check if running in deployment environment
    is_deployed = (
        os.getenv("STREAMLIT_SHARING") == "true" or 
        os.getenv("RAILWAY_ENVIRONMENT") or 
        os.getenv("HEROKU") or
        os.getenv("RENDER") or
        "streamlit" in os.getcwd().lower()
    )
    
    if database_url and database_url.startswith("postgresql://"):
        try:
            clean_url = database_url.strip()
            conn = psycopg2.connect(
                clean_url,
                sslmode='require',
                connect_timeout=10
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return conn, 'postgresql'
        except Exception as e:
            print(f"PostgreSQL connection failed: {str(e)}")
            if is_deployed:
                return sqlite3.connect(':memory:'), 'sqlite_memory'
    
    if is_deployed:
        return sqlite3.connect(':memory:'), 'sqlite_memory'
    else:
        sqlite_path = os.path.join(os.path.dirname(__file__), 'spider_demo.db')
        return sqlite3.connect(sqlite_path), 'sqlite'

# FastAPI 모델 정의
class QueryRequest(BaseModel):
    question: str
    language: str = "en"
    
class QueryResponse(BaseModel):
    sql_query: str
    result: list
    explanation: str

def init_database():
    """Initialize database with sample data"""
    from init_db import init_database as init_db_func
    try:
        init_db_func()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def get_database_schema():
    """Get database schema information for context"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'sqlite' or db_type == 'sqlite_memory':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        elif db_type == 'postgresql':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        
        tables = cursor.fetchall()
        schema_info = {}
        
        for (table_name,) in tables:
            if db_type == 'sqlite' or db_type == 'sqlite_memory':
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema_info[table_name] = []
                for col in columns:
                    schema_info[table_name].append({
                        'column': col[1],
                        'type': col[2],
                        'nullable': 'YES' if col[3] == 0 else 'NO'
                    })
            elif db_type == 'postgresql':
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name='{table_name}';
                """)
                columns = cursor.fetchall()
                schema_info[table_name] = []
                for col in columns:
                    schema_info[table_name].append({
                        'column': col[0],
                        'type': col[1],
                        'nullable': col[2]
                    })
        
        cursor.close()
        conn.close()
        return schema_info
    except Exception as e:
        print(f"Error getting schema: {e}")
        return {}

def generate_sql_with_gemini(question: str, schema: dict, language: str = "en") -> str:
    """Generate SQL query using Gemini API"""
    schema_text = ""
    for table_name, columns in schema.items():
        schema_text += f"\nTable: {table_name}\n"
        for col in columns:
            schema_text += f"  - {col['column']} ({col['type']})\n"
    
    if language == "ko":
        prompt = f"""
당신은 SQL 전문가입니다. 다음 데이터베이스 스키마와 자연어 질문을 보고 유효한 SQL 쿼리를 생성하세요.

데이터베이스 스키마:
{schema_text}

질문: {question}

규칙:
1. SQL 쿼리만 생성하고 설명은 하지 마세요
2. 적절한 SQL 문법을 사용하세요
3. 테이블과 컬럼 이름을 정확히 사용하세요
4. 필요시 적절한 JOIN을 사용하세요
5. 마크다운 포맷 없이 SQL 쿼리만 반환하세요

SQL 쿼리:
"""
    else:
        prompt = f"""
You are a SQL expert. Given the following database schema and a natural language question, 
generate a valid SQL query.

Database Schema:
{schema_text}

Question: {question}

Rules:
1. Generate only the SQL query, no explanations
2. Use proper SQL syntax
3. Be precise with table and column names
4. Use appropriate JOINs when needed
5. Return only the SQL query without any markdown formatting

SQL Query:
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
                top_p=0.8
            )
        )
        
        sql_query = response.text.strip()
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        return sql_query
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

def execute_sql_query(sql_query: str):
    """Execute SQL query and return results"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        if db_type == 'sqlite' or db_type == 'sqlite_memory':
            column_names = [description[0] for description in cursor.description]
        elif db_type == 'postgresql':
            column_names = [description.name for description in cursor.description]
        
        result_list = []
        for row in results:
            result_dict = {}
            for i, value in enumerate(row):
                result_dict[column_names[i]] = value
            result_list.append(result_dict)
        
        cursor.close()
        conn.close()
        return result_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution error: {str(e)}")

def generate_explanation(question: str, sql_query: str, results: list, language: str = "en") -> str:
    """Generate explanation using Gemini"""
    if language == "ko":
        prompt = f"""
다음 SQL 쿼리를 간단한 용어로 설명해주세요:

질문: {question}
SQL 쿼리: {sql_query}
결과 개수: {len(results)}

쿼리가 무엇을 하는지, 결과가 무엇을 보여주는지 간단하고 명확하게 설명해주세요.
마크다운 형식 없이 일반 텍스트로만 답변해주세요.
"""
    else:
        prompt = f"""
Explain this SQL query in simple terms:

Question: {question}
SQL Query: {sql_query}
Number of results: {len(results)}

Provide a brief, clear explanation of what the query does and what the results show.
Answer in plain text without any markdown formatting.
"""

    try:
        print(f"Generating explanation for query: {sql_query[:50]}...")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=300,
                top_p=0.8
            )
        )
        
        if response and response.text:
            explanation = response.text.strip()
            print(f"Generated explanation: {explanation[:100]}...")
            return explanation
        else:
            print("Empty response from Gemini API")
            return "설명을 생성할 수 없습니다." if language == "ko" else "Unable to generate explanation."
            
    except Exception as e:
        print(f"Error generating explanation: {str(e)}")
        # 간단한 설명을 직접 생성
        if language == "ko":
            return f"이 쿼리는 '{question}' 질문에 대한 답을 찾기 위해 데이터베이스를 검색합니다. 총 {len(results)}개의 결과를 반환했습니다."
        else:
            return f"This query searches the database to answer '{question}'. It returned {len(results)} results."

# FastAPI 엔드포인트
@api_app.get("/")
async def root():
    return {"message": "Text-to-SQL API is running"}

@api_app.get("/health")
async def health_check():
    try:
        conn, db_type = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected", "db_type": db_type}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@api_app.get("/schema")
async def get_schema():
    schema = get_database_schema()
    return {"schema": schema}

@api_app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    schema = get_database_schema()
    if not schema:
        raise HTTPException(status_code=500, detail="Unable to retrieve database schema")
    
    sql_query = generate_sql_with_gemini(request.question, schema, request.language)
    results = execute_sql_query(sql_query)
    explanation = generate_explanation(request.question, sql_query, results, request.language)
    
    return QueryResponse(
        sql_query=sql_query,
        result=results,
        explanation=explanation
    )

# FastAPI 서버를 별도 스레드에서 실행
def run_fastapi():
    uvicorn.run(api_app, host="0.0.0.0", port=8000, log_level="info")

# Streamlit 앱 시작 시 FastAPI 서버도 시작
if 'fastapi_started' not in st.session_state:
    st.session_state.fastapi_started = True
    init_database()
    
    # 배포 환경이 아닌 경우에만 FastAPI 서버 시작
    if not (os.getenv("STREAMLIT_SHARING") == "true" or 
            os.getenv("RAILWAY_ENVIRONMENT") or 
            os.getenv("HEROKU") or
            os.getenv("RENDER")):
        threading.Thread(target=run_fastapi, daemon=True).start()
        time.sleep(2)  # FastAPI 서버 시작 대기

# 다국어 지원
LANGUAGES = {
    "한국어": {
        "title": "🤖 Text-to-SQL 챗봇 데모",
        "subtitle": "자연어로 질문하면 SQL 쿼리를 생성하고 결과를 보여드립니다.",
        "system_status": "📊 시스템 상태",
        "api_connected": "✅ API 서버 연결됨",
        "api_disconnected": "❌ API 서버 연결 실패",
        "db_schema": "📋 데이터베이스 스키마",
        "schema_error": "스키마 정보를 가져올 수 없습니다.",
        "ask_question": "💬 질문하기",
        "sample_questions": "📝 예시 질문들",
        "input_placeholder": "예: 모든 직원의 이름과 급여를 보여주세요",
        "ask_button": "🚀 질문하기",
        "thinking": "🤔 SQL 쿼리를 생성하고 실행 중...",
        "chat_history": "💭 대화 기록",
        "question": "질문",
        "generated_sql": "생성된 SQL 쿼리",
        "explanation": "설명",
        "result": "결과",
        "error": "❌ 오류",
        "no_results": "결과가 없습니다.",
        "download_csv": "📥 CSV로 다운로드",
        "clear_history": "🗑️ 대화 기록 지우기",
        "powered_by": "🚀 Powered by Gemini 2.5 Flash | 🐘 Supabase PostgreSQL | ⚡ FastAPI + Streamlit | 🕸️ Spider 데이터셋"
    },
    "English": {
        "title": "🤖 Text-to-SQL Chatbot Demo",
        "subtitle": "Ask questions in natural language and get SQL queries with results.",
        "system_status": "📊 System Status",
        "api_connected": "✅ API Server Connected",
        "api_disconnected": "❌ API Server Connection Failed",
        "db_schema": "📋 Database Schema",
        "schema_error": "Unable to retrieve schema information.",
        "ask_question": "💬 Ask a Question",
        "sample_questions": "📝 Sample Questions",
        "input_placeholder": "e.g., Show me all employee names and salaries",
        "ask_button": "🚀 Ask Question",
        "thinking": "🤔 Generating SQL query and executing...",
        "chat_history": "💭 Chat History",
        "question": "Question",
        "generated_sql": "Generated SQL Query",
        "explanation": "Explanation",
        "result": "Result",
        "error": "❌ Error",
        "no_results": "No results found.",
        "download_csv": "📥 Download CSV",
        "clear_history": "🗑️ Clear Chat History",
        "powered_by": "🚀 Powered by Gemini 2.5 Flash | 🐘 Supabase PostgreSQL | ⚡ FastAPI + Streamlit | 🕸️ Spider Dataset"
    }
}

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Text-to-SQL Chatbot",
    page_icon="🤖",
    layout="wide"
)

# 언어 선택
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    selected_lang = st.selectbox("🌐 Language", ["한국어", "English"], key="language")

lang = LANGUAGES[selected_lang]

# API 엔드포인트
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_database_schema_api():
    """Get database schema from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/schema", timeout=10)
        if response.status_code == 200:
            return response.json()["schema"]
        return None
    except:
        # 배포 환경에서는 직접 스키마 가져오기
        return get_database_schema()

def query_api(question, language="en"):
    """Send query to API and get response"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"question": question, "language": language},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout. Please try again." if language == "en" else "요청 시간이 초과되었습니다. 다시 시도해주세요."}
    except Exception as e:
        # 배포 환경에서는 직접 처리
        try:
            schema = get_database_schema()
            if not schema:
                return {"error": "Unable to retrieve database schema"}
            
            sql_query = generate_sql_with_gemini(question, schema, language)
            results = execute_sql_query(sql_query)
            explanation = generate_explanation(question, sql_query, results, language)
            
            return {
                "sql_query": sql_query,
                "result": results,
                "explanation": explanation
            }
        except Exception as direct_e:
            return {"error": f"Connection error: {str(direct_e)}" if language == "en" else f"연결 오류: {str(direct_e)}"}

# 메인 UI
st.title(lang["title"])
st.markdown(lang["subtitle"])

# 사이드바
with st.sidebar:
    st.header(lang["system_status"])
    
    # API 상태 확인
    if check_api_health():
        st.success(lang["api_connected"])
    else:
        st.warning("Direct mode (배포 환경)")
    
    st.header(lang["db_schema"])
    
    # 데이터베이스 스키마 표시
    schema = get_database_schema_api()
    if schema:
        for table_name, columns in schema.items():
            with st.expander(f"📁 {table_name}"):
                for col in columns:
                    st.text(f"• {col['column']} ({col['type']})")
    else:
        st.warning(lang["schema_error"])

# 메인 콘텐츠 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.header(lang["ask_question"])
    
    # 예시 질문들
    st.subheader(lang["sample_questions"])
    
    if selected_lang == "한국어":
        sample_questions = [
            "모든 직원의 이름과 급여를 보여주세요",
            "컴퓨터 과학과에 속한 직원들은 누구인가요?",
            "가장 높은 급여를 받는 직원은 누구인가요?",
            "각 부서별 평균 급여는 얼마인가요?",
            "현재 진행 중인 프로젝트들을 보여주세요",
            "학생들의 평균 GPA는 얼마인가요?",
            "수학과 학생들의 정보를 보여주세요"
        ]
    else:
        sample_questions = [
            "Show me all employee names and salaries",
            "Who are the employees in Computer Science department?",
            "Who is the highest paid employee?",
            "What is the average salary by department?",
            "Show me current ongoing projects",
            "What is the average GPA of students?",
            "Show me information about Mathematics students"
        ]
    
    for i, question in enumerate(sample_questions):
        if st.button(f"💡 {question}", key=f"sample_{i}"):
            st.session_state.user_question = question

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_question' not in st.session_state:
    st.session_state.user_question = ""

# 사용자 입력
user_input = st.text_input(
    f"{lang['question']}:",
    value=st.session_state.user_question,
    placeholder=lang["input_placeholder"],
    key="question_input"
)

if st.button(lang["ask_button"], type="primary") or st.session_state.user_question:
    if user_input or st.session_state.user_question:
        question = user_input or st.session_state.user_question
        st.session_state.user_question = ""
        
        with st.spinner(lang["thinking"]):
            language_code = "ko" if selected_lang == "한국어" else "en"
            result = query_api(question, language_code)
        
        # 대화 기록에 추가
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.chat_history.append({
            "timestamp": timestamp,
            "question": question,
            "result": result
        })

# 대화 기록 표시
st.header(lang["chat_history"])

for i, chat in enumerate(reversed(st.session_state.chat_history)):
    with st.expander(f"🕐 {chat['timestamp']} - {chat['question'][:50]}...", expanded=(i==0)):
        st.markdown(f"**{lang['question']}:** {chat['question']}")
        
        if "error" in chat["result"]:
            st.error(f"{lang['error']}: {chat['result']['error']}")
        else:
            # SQL 쿼리 표시
            st.markdown(f"**{lang['generated_sql']}:**")
            st.code(chat["result"]["sql_query"], language="sql")
            
            # 설명 표시
            if "explanation" in chat["result"]:
                st.markdown(f"**{lang['explanation']}:**")
                st.info(chat["result"]["explanation"])
            
            # 결과 표시
            st.markdown(f"**{lang['result']}:**")
            if chat["result"]["result"]:
                df = pd.DataFrame(chat["result"]["result"])
                st.dataframe(df, use_container_width=True)
                
                # 다운로드 버튼
                csv = df.to_csv(index=False)
                st.download_button(
                    label=lang["download_csv"],
                    data=csv,
                    file_name=f"query_result_{chat['timestamp'].replace(':', '')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(lang["no_results"])

# 대화 기록 지우기 버튼
if st.session_state.chat_history:
    if st.button(lang["clear_history"]):
        st.session_state.chat_history = []
        st.rerun()

# 푸터
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center'>
        <p>{lang["powered_by"]}</p>
    </div>
    """, 
    unsafe_allow_html=True
)
