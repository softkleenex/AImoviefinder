# 🎬 기억에 의존한 영화 추론 에이전트

사용자가 영화 제목을 기억하지 못하고 단편적인 정보만 말해도, 대화를 통해 그 영화를 찾아주는 **실제 MCP 기반** 멀티턴 LLM 추론 시스템입니다.

## 🔥 핵심 기능

### 1. Agent Supervisor 아키텍처
- 중앙 집중식 에이전트 관리 (`AgentSupervisor`)
- 멀티턴 대화 상태 유지 (`conversation_history`)
- 다양한 도구와 서비스 조율

### 2. 멀티턴 대화 시스템
- 대화 히스토리 추적 및 상황 인식
- 사용자 답변 신뢰성 평가 및 재질문
- 자연스러운 한국어 대화 흐름

### 3. **실제 MCP (Model Context Protocol) 구현** ⭐
- **JSON-RPC 2.0 프로토콜** 완전 구현
- **실제 MCP 표준** 준수 (`real_mcp_integration.py`)
- **표준 도구 스키마** 및 응답 형식
- **세션 관리** 및 **요청 ID 추적**

### 4. 다중 검색 시스템
- **로컬 IMDb 데이터**: Top 1000 영화 즉시 검색
- **웹 검색**: Tavily API를 통한 최신 정보
- **지능형 폴백**: MCP 검색 품질 평가 후 자동 웹 검색

### 5. 한국어 완전 지원
- 확장된 한국어-영어 키워드 매핑 (발표용 최적화)
- 한국인 사용자 친화적 인터페이스
- 데이터셋 부재 영화에 대한 이유 설명

## 🛠 기술 스택

- **Frontend**: Streamlit (포트 8080)
- **Backend**: Python 3.11
- **LLM**: OpenAI GPT-4o-mini, Google Gemini (폴백)
- **Database**: IMDb Top 1000 CSV
- **Search**: Tavily API (웹 검색)
- **Deployment**: Google Cloud Run
- **Protocol**: **실제 MCP (JSON-RPC 2.0)** 🎯

## 🔗 실제 MCP 구현 상세

### MCP 시스템 구조
```
RealMCPMovieSearch (real_mcp_integration.py)
├── JSON-RPC 2.0 요청/응답
├── 표준 도구 스키마 정의
├── 세션 및 요청 ID 관리
└── 에러 처리 및 로깅
```

### MCP 도구 정의
```python
{
    "search_movies": {
        "name": "search_movies",
        "description": "Search movies in IMDb Top 1000 dataset",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "genre": {"type": "string"},
                "director": {"type": "string"},
                "actor": {"type": "string"},
                "max_results": {"type": "integer", "default": 5}
            }
        }
    }
}
```

## 🚀 배포

### 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Google Cloud 배포
```bash
chmod +x deploy.sh
./deploy.sh
```

**🌐 라이브 URL**: https://movie-agent-real-mcp-904447394903.us-central1.run.app

## 📊 시스템 아키텍처

```
사용자 입력 → AgentSupervisor → RealMCPMovieSearch (JSON-RPC 2.0)
                     ↓                      ↓
              한국어-영어 변환 → MCP 도구 호출 → IMDb 검색
                     ↓                      ↓
              품질 평가 → Tavily 웹 검색 (필요시)
                     ↓
              LLM 통합 응답 → Streamlit UI → Top 5 추천
                     ↓
              멀티턴 대화 히스토리 유지
```

## 🎯 발표용 시연 예시

- **"감옥에서 탈출하는 영화"** → The Shawshank Redemption
- **"마피아 영화"** → The Godfather 시리즈
- **"크리스토퍼 놀란 감독 영화"** → The Dark Knight, Inception
- **"조커가 나오는 영화"** → The Dark Knight

## 🔧 주요 컴포넌트

### 실제 MCP 시스템
- `real_mcp_integration.py`: **실제 MCP JSON-RPC 2.0 구현** ⭐
- `agent_supervisor.py`: MCP 통합 메인 에이전트 로직

### 기존 호환성 유지
- `mcp_client.py`: 기존 시스템과의 호환성
- `movie_data_manager.py`: 영화 데이터 관리
- `tavily_search.py`: 웹 검색 통합
- `llm_client.py`: 멀티 LLM 폴백 시스템

## 📋 Wish.txt 요구사항 달성

✅ **1. 에이전트 supervisor 아키텍쳐 사용** - `AgentSupervisor` 클래스  
✅ **2. 멀티턴 대화가 가능** - `conversation_history` 상태 관리  
✅ **3. MCP 사용 (Model Context Protocol)** - **실제 JSON-RPC 2.0 구현**  
✅ **4. IMDb movies dataset** - Top 1000 영화 데이터  
✅ **5. 발표 및 시연 준비** - Google Cloud Run 배포 완료  

**🎬 시연시간: 16:50 | 팀당 10분 | 모든 준비 완료! 🚀**

## 💬 사용 예시

**사용자**: "감옥에서 탈출하는 영화"
**AI**: 🎬 **영화 추론 결과:**
다음과 같은 영화들을 추천드립니다:

🔧 **실제 MCP 시스템 검색 결과:**  
📊 검색된 영화: 3개  
1. The Shawshank Redemption (1994) ⭐9.3  
2. Escape from Alcatraz (1979) ⭐7.6  
3. The Great Escape (1963) ⭐8.2  

**사용자**: "그 중에서 모건 프리먼이 나오는 영화"
**AI**: The Shawshank Redemption이 정확히 맞는 것 같습니다! 모건 프리먼과 팀 로빈스가 주연으로 출연한 감동적인 드라마입니다...

## 📊 프로젝트 구조

```
mcp_project/
├── real_mcp_integration.py  # 실제 MCP JSON-RPC 2.0 구현 ⭐
├── agent_supervisor.py      # 메인 에이전트 (Supervisor)
├── movie_data_manager.py    # 영화 데이터 관리 (Worker)
├── tavily_search.py         # 웹 검색 통합
├── llm_client.py           # 멀티 LLM 폴백 시스템
├── app.py                 # Streamlit 웹 앱
├── dataset/
│   └── imdb_top_1000.csv # IMDb 영화 데이터
├── requirements.txt      # Python 의존성
├── Dockerfile           # Docker 설정
├── deploy.sh           # 배포 스크립트
└── README.md          # 프로젝트 문서
```

## 🔧 주요 설정

### MCP 설정
- 프로토콜: JSON-RPC 2.0
- 세션 관리: 시간 기반 세션 ID
- 요청 추적: 순차적 요청 ID

### LLM 설정
- 메인: OpenAI GPT-4o-mini
- 폴백: Google Gemini
- Temperature: 0.7
- Max Tokens: 1000

### Streamlit 설정
- Port: 8080
- 메모리 제한: 최적화됨
- 업로드 제한: 50MB

## 📝 개발 로그

### 완료된 기능
- ✅ **실제 MCP JSON-RPC 2.0 프로토콜 구현**
- ✅ Agent Supervisor 아키텍처
- ✅ 멀티턴 대화 시스템
- ✅ 한국어 최적화 키워드 매핑
- ✅ 사용자 답변 신뢰성 평가
- ✅ Google Cloud Run 배포
- ✅ Runtime 오류 완전 수정
- ✅ 발표용 시연 최적화

### 실제 MCP vs 기존 시스템
| 구분 | 기존 시스템 | 실제 MCP |
|------|-------------|----------|
| 프로토콜 | 임시 구현 | JSON-RPC 2.0 표준 |
| 도구 스키마 | 단순 딕셔너리 | 표준 JSON Schema |
| 세션 관리 | 없음 | 실제 세션 ID |
| 에러 처리 | 기본 | 표준 MCP 에러 코드 |
| 로깅 | 간단 | 구조화된 MCP 로그 |

## 📄 라이센스

이 프로젝트는 교육 목적으로 개발되었습니다.