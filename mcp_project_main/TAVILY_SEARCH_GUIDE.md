# 🌐 Tavily 웹 검색 트리거 기준 및 동작 원리

## 🔍 **Tavily 웹 검색이 언제 실행되는가?**

### 1. **MCP 결과 부족 조건**
```python
if len(mcp_movies) < 3 or should_use_tavily:
```
- MCP 검색 결과가 3개 미만일 때
- `_evaluate_mcp_quality()` 함수가 True를 반환할 때

### 2. **특정 키워드 자동 감지**

#### 🗓️ **최신 연도 키워드**
```python
"2020", "2021", "2022", "2023", "2024", "2025"
```
- **이유**: IMDb Top 1000 데이터셋이 주로 2020년 이전 영화 포함
- **동작**: 최신 영화 요청 시 웹 검색으로 보완

#### 📺 **플랫폼/프랜차이즈 키워드**  
```python
"최근", "넷플릭스", "디즈니", "마블", "DC", "아마존"
```
- **이유**: 스트리밍 플랫폼 전용 콘텐츠는 데이터셋에 없을 가능성 높음
- **동작**: 웹에서 최신 플랫폼 정보 검색

#### 🦠 **최신 트렌드 키워드**
```python
"좀비", "바이러스", "팬데믹", "코로나", "메타버스"
```
- **이유**: 팬데믹 이후 트렌드 영화들 검색
- **동작**: 최신 트렌드 영화 웹 검색

#### 🤖 **기술 키워드**
```python
"AI", "인공지능", "NFT", "가상현실", "VR"
```
- **이유**: 최신 기술 테마 영화들은 데이터셋에 부족
- **동작**: 기술 관련 최신 영화 검색

### 3. **연도 불일치 검사**
```python
if "2024" in user_input and latest_year < 2020:
    print(f"🔍 최신 영화 요청이지만 MCP 최신 결과가 {latest_year}년 - 웹 검색 필요")
    return True
```

## 🔧 **Tavily 검색 동작 과정**

### 1. **검색 쿼리 생성**
```python
# tavily_search.py의 _build_search_query() 함수
def _build_search_query(self, conversation_history, current_input):
    # 한국어 키워드를 영어로 변환
    # 영화 관련 키워드 추가: "movie", "film", "action"
    # 최종 검색 쿼리 반환
```

### 2. **웹 검색 실행**
```python
# Tavily API 호출
search_results = self.tavily_client.search(
    query=search_query,
    search_depth="advanced",
    max_results=5
)
```

### 3. **결과 후처리**
- 영화 제목 추출 및 정리
- 중복 제거
- IMDb, Rotten Tomatoes 등 신뢰할 수 있는 소스 우선

## 📊 **실제 동작 예시**

### 예시 1: 최신 영화 요청
```
사용자: "2024년에 나온 좋은 영화 추천해주세요"
시스템: 🔍 '2024' 키워드 감지 - 웹 검색 필요
결과: MCP 검색 + Tavily 웹 검색 병행
```

### 예시 2: 넷플릭스 콘텐츠
```
사용자: "넷플릭스에서 볼 만한 영화"  
시스템: 🔍 '넷플릭스' 키워드 감지 - 웹 검색 필요
결과: 넷플릭스 전용 콘텐츠 웹 검색
```

### 예시 3: MCP 결과 부족
```
사용자: "한국 좀비 영화"
MCP 결과: 1개 영화만 발견
시스템: 🌐 MCP 결과가 부족하여 Tavily 웹 검색을 수행합니다...
결과: 추가 한국 좀비 영화 웹에서 검색
```

## ⚙️ **Tavily 검색 최적화 설정**

### 1. **검색 깊이**
```python
search_depth="advanced"  # 더 정확한 결과
```

### 2. **결과 개수**
```python
max_results=5  # 상위 5개 결과만
```

### 3. **검색 도메인 필터링**
```python
# 영화 관련 신뢰할 수 있는 소스 우선
preferred_domains = [
    "imdb.com", 
    "rottentomatoes.com",
    "themoviedb.org",
    "metacritic.com"
]
```

## 🎯 **Tavily vs MCP 결과 통합**

### 통합 응답 구조:
```markdown
## 🤖 GPT 직접 응답:
[GPT의 일반적인 영화 조언]

## 🔧 실제 MCP 시스템 검색 결과:
[IMDb Top 1000 데이터셋 검색 결과]

## 🌐 Tavily 웹 검색 결과:
[최신 웹 정보 검색 결과]

## 🎯 GPT의 MCP 결과 분석:
[GPT가 MCP 결과에 대한 피드백]
```

이렇게 MCP 로컬 데이터와 Tavily 웹 검색을 지능적으로 조합하여 **포괄적이고 최신의 영화 정보**를 제공합니다!
