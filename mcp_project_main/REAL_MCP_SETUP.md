# 🔗 실제 MCP (Model Context Protocol) 구현 가이드

## 🎯 MCP를 실제로 사용하는 방법들

### 방법 1: 기존 MCP 서버 사용 (권장)
### 방법 2: 자체 MCP 서버 구축
### 방법 3: MCP 호환 도구 연동

---

## 🚀 방법 1: 기존 MCP 서버 사용 (가장 쉬움)

### 1.1 Anthropic Claude Desktop MCP 연동

```bash
# Claude Desktop이 설치되어 있다면
# ~/.config/claude-desktop/mcp-servers.json 설정
{
  "servers": {
    "movie-search": {
      "command": "python",
      "args": ["mcp_movie_server.py"],
      "env": {
        "MOVIE_DB_PATH": "./dataset/imdb_top_1000.csv"
      }
    }
  }
}
```

### 1.2 공개 MCP 서버 활용

```python
# 공개 MCP 서버들 (예시)
MCP_SERVERS = {
    "filesystem": "npx @modelcontextprotocol/server-filesystem",
    "brave-search": "npx @modelcontextprotocol/server-brave-search", 
    "sqlite": "npx @modelcontextprotocol/server-sqlite"
}
```

---

## 🏗️ 방법 2: 자체 MCP 서버 구축

### 2.1 MCP Server SDK 설치

```bash
pip install mcp
# 또는
npm install @modelcontextprotocol/sdk
```

### 2.2 영화 검색용 MCP 서버 구현

```python
# real_mcp_server.py
from mcp import Server, Tool
from mcp.types import TextContent, ImageContent
import pandas as pd
import json

class MovieMCPServer:
    def __init__(self):
        self.server = Server("movie-search-server")
        self.movie_df = pd.read_csv('dataset/imdb_top_1000.csv')
        self._setup_tools()
    
    def _setup_tools(self):
        @self.server.tool()
        async def search_movies(
            keywords: list[str] = None,
            genre: str = None,
            director: str = None,
            min_rating: float = None,
            max_results: int = 5
        ) -> list[dict]:
            """IMDb 데이터에서 영화 검색"""
            
            results = self.movie_df.copy()
            
            # 키워드 검색
            if keywords:
                pattern = '|'.join(keywords)
                mask = (
                    results['Series_Title'].str.contains(pattern, case=False, na=False) |
                    results['Overview'].str.contains(pattern, case=False, na=False) |
                    results['Genre'].str.contains(pattern, case=False, na=False)
                )
                results = results[mask]
            
            # 장르 필터
            if genre:
                results = results[results['Genre'].str.contains(genre, case=False, na=False)]
            
            # 감독 필터
            if director:
                results = results[results['Director'].str.contains(director, case=False, na=False)]
            
            # 평점 필터
            if min_rating:
                results = results[results['IMDB_Rating'] >= min_rating]
            
            # 결과 정렬 및 제한
            results = results.sort_values('IMDB_Rating', ascending=False).head(max_results)
            
            return results.to_dict('records')
        
        @self.server.tool()
        async def get_movie_details(movie_title: str) -> dict:
            """특정 영화의 상세 정보 조회"""
            movie = self.movie_df[
                self.movie_df['Series_Title'].str.contains(movie_title, case=False, na=False)
            ].iloc[0]
            
            return {
                "title": movie['Series_Title'],
                "year": movie['Released_Year'],
                "rating": movie['IMDB_Rating'],
                "genre": movie['Genre'],
                "director": movie['Director'],
                "overview": movie['Overview'],
                "poster": movie.get('Poster_Link', ''),
                "runtime": movie['Runtime'],
                "stars": [movie['Star1'], movie['Star2'], movie['Star3'], movie['Star4']]
            }
    
    async def start(self):
        """MCP 서버 시작"""
        await self.server.start()

# 서버 실행
if __name__ == "__main__":
    import asyncio
    
    server = MovieMCPServer()
    asyncio.run(server.start())
```

### 2.3 실제 MCP 클라이언트 구현

```python
# real_mcp_client.py
import asyncio
import json
from mcp import Client
from mcp.types import Tool

class RealMCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = None
    
    async def connect(self):
        """MCP 서버에 연결"""
        self.client = Client(self.server_url)
        await self.client.connect()
        
        # 서버 정보 및 도구 목록 가져오기
        server_info = await self.client.get_server_info()
        tools = await self.client.list_tools()
        
        print(f"✅ MCP 서버 연결됨: {server_info.name}")
        print(f"사용 가능한 도구: {[tool.name for tool in tools]}")
    
    async def search_movies(self, **kwargs):
        """영화 검색 도구 호출"""
        if not self.client:
            await self.connect()
        
        result = await self.client.call_tool("search_movies", kwargs)
        return result
    
    async def get_movie_details(self, movie_title: str):
        """영화 상세 정보 도구 호출"""
        if not self.client:
            await self.connect()
        
        result = await self.client.call_tool("get_movie_details", {"movie_title": movie_title})
        return result
    
    async def disconnect(self):
        """연결 해제"""
        if self.client:
            await self.client.disconnect()

# 사용 예시
async def test_real_mcp():
    client = RealMCPClient()
    
    try:
        # 영화 검색
        results = await client.search_movies(
            keywords=["prison", "escape"],
            min_rating=8.0,
            max_results=3
        )
        
        print("검색 결과:")
        for movie in results:
            print(f"- {movie['Series_Title']} ({movie['Released_Year']}) ⭐{movie['IMDB_Rating']}")
        
        # 상세 정보 조회
        if results:
            details = await client.get_movie_details(results[0]['Series_Title'])
            print(f"\n상세 정보: {details}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_real_mcp())
```

---

## 🔧 방법 3: MCP 호환 도구 연동

### 3.1 기존 MCP 생태계 활용

```python
# mcp_integration.py
import subprocess
import json
import asyncio

class MCPToolIntegration:
    def __init__(self):
        self.available_servers = {
            "filesystem": {
                "command": ["npx", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
                "description": "파일 시스템 접근"
            },
            "brave-search": {
                "command": ["npx", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": "your-api-key"},
                "description": "Brave 검색 엔진"
            },
            "sqlite": {
                "command": ["npx", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"],
                "description": "SQLite 데이터베이스"
            }
        }
    
    async def call_mcp_server(self, server_name: str, tool_name: str, arguments: dict):
        """MCP 서버 호출"""
        if server_name not in self.available_servers:
            raise ValueError(f"Unknown server: {server_name}")
        
        server_config = self.available_servers[server_name]
        
        # MCP 서버 프로세스 시작
        process = await asyncio.create_subprocess_exec(
            *server_config["command"],
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=server_config.get("env", {})
        )
        
        # JSON-RPC 요청 생성
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # 요청 전송
        stdout, stderr = await process.communicate(
            json.dumps(request).encode() + b'\n'
        )
        
        if process.returncode != 0:
            raise Exception(f"MCP server error: {stderr.decode()}")
        
        # 응답 파싱
        response = json.loads(stdout.decode())
        return response.get("result", {})
```

---

## 🎯 프로젝트에 실제 MCP 적용하기

### 단계 1: MCP 서버 선택
```bash
# 옵션 A: 간단한 파일 기반 MCP 서버
npm install -g @modelcontextprotocol/server-filesystem

# 옵션 B: 우리 영화 데이터용 커스텀 서버 (위의 코드 사용)
python real_mcp_server.py

# 옵션 C: 기존 공개 MCP 서버 활용
```

### 단계 2: AgentSupervisor 수정
```python
# agent_supervisor.py 수정
class AgentSupervisor:
    def __init__(self):
        # ... 기존 코드 ...
        
        # 실제 MCP 클라이언트로 교체
        self.real_mcp_client = RealMCPClient("http://localhost:8000")
        
    async def process_request_async(self, user_input):
        """비동기 버전의 요청 처리"""
        # 실제 MCP 서버 호출
        mcp_results = await self.real_mcp_client.search_movies(
            keywords=self._translate_korean_to_english_keywords(user_input),
            max_results=5
        )
        
        # ... 나머지 로직
```

### 단계 3: Streamlit 비동기 지원
```python
# app.py 수정
import asyncio

def run_async_request(supervisor, user_input):
    """Streamlit에서 비동기 함수 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(supervisor.process_request_async(user_input))
    finally:
        loop.close()

# 사용
if prompt := st.chat_input("..."):
    with st.spinner("영화를 찾고 있습니다..."):
        response, movies = run_async_request(st.session_state.supervisor, prompt)
```

---

## 💡 추천 방법

### 🥇 **단기 (발표용)**: 현재 가짜 MCP 유지
- 이미 완벽하게 작동하고 있음
- MCP 개념과 구조를 잘 보여줌
- 발표에서 혼란 없이 시연 가능

### 🥈 **중기 (학습용)**: 간단한 실제 MCP 서버 구축
```bash
# 1. 위의 real_mcp_server.py 실행
python real_mcp_server.py

# 2. 별도 터미널에서 클라이언트 테스트
python real_mcp_client.py
```

### 🥉 **장기 (실무용)**: MCP 생태계 활용
- Claude Desktop과 연동
- 다양한 공개 MCP 서버 활용
- 표준 MCP 프로토콜 완전 준수

---

## 🤔 어떤 방법을 선택하시겠습니까?

1. **지금 당장 실제 MCP 서버 구축** → 위의 `real_mcp_server.py` 코드 사용
2. **발표 후 천천히 업그레이드** → 현재 시스템 유지
3. **기존 MCP 도구 연동** → Claude Desktop이나 공개 서버 활용

어떤 방향으로 진행하고 싶으신지 알려주시면 더 자세한 구현을 도와드리겠습니다!