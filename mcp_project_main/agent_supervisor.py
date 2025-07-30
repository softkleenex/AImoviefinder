import json
import os
import re
from dotenv import load_dotenv
from movie_data_manager import MovieDataManager
from mcp_client import MCPClient, MCPMovieToolHandler
from real_mcp_integration import RealMCPMovieSearch
from tavily_search import TavilyMovieSearcher
from llm_client import get_llm_client

# Load environment variables
load_dotenv()

class AgentSupervisor:
    def __init__(self):
        self.movie_manager = MovieDataManager()
        self.conversation_history = [] # 멀티턴 대화를 위한 대화 기록
        self.last_suggested_movies = [] # 마지막으로 제안된 영화 목록 (top 5)
        self.llm_client = get_llm_client()  # 멀티 LLM 폴백 클라이언트
        
        # 실제 MCP 시스템 초기화 (가짜 MCP 대체)
        self.real_mcp = RealMCPMovieSearch(self.movie_manager)
        print(f"🔗 실제 MCP 시스템 초기화 완료: {self.real_mcp.session_id}")
        
        # 기존 가짜 MCP (호환성 유지용)
        self.mcp_client = MCPClient()
        self.mcp_tool_handler = MCPMovieToolHandler(self.movie_manager)
        self.mcp_session = self.mcp_client.initialize_session()
        
        # Tavily 검색 클라이언트 초기화
        self.tavily_searcher = TavilyMovieSearcher()
        print("🌐 Tavily 웹 검색 클라이언트 초기화 완료")

    def _add_to_history(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def _construct_mcp_request(self, user_input):
        # 실제 MCP 프로토콜을 사용한 컨텍스트 메시지 생성
        available_tools = self.mcp_tool_handler.tools
        mcp_context = self.mcp_client.create_context_message(
            conversation_history=self.conversation_history,
            current_input=user_input,
            available_tools=available_tools
        )
        
        # MCP 상호작용 로깅
        self.mcp_client.log_mcp_interaction("context_request", mcp_context)
        
        # _send_to_llm에서 사용할 수 있는 형태로 변환
        return {
            "current_user_input": user_input,
            "conversation_history": self.conversation_history,
            "mcp_context": mcp_context,
            "available_tools": available_tools
        }

    def _send_to_llm(self, mcp_request):
        """OpenAI API를 사용하여 실제 LLM 응답을 생성합니다."""
        user_input = mcp_request["current_user_input"]
        conversation_history = mcp_request["conversation_history"]
        
        # 시스템 프롬프트 구성
        system_prompt = """
당신은 영화 추론 전문가입니다. 사용자가 단편적인 정보만 제공해도 대화를 통해 원하는 영화를 찾아주는 역할을 합니다.

규칙:
1. 항상 한국어로 응답하세요
2. 사용자에게 추가 질문을 해서 더 많은 정보를 얻으세요
3. 현재 사용자가 생각하고 있을 것 같은 영화 top 5를 JSON 형태로 추천하세요
4. 데이터셋에 없는 영화라면 그 이유를 설명하세요
5. 응답은 반드시 다음 JSON 형식을 따르세요:

{
  "action": "search_movies" 또는 "respond_text",
  "search_params": {
    "keywords": ["키워드1", "키워드2"],
    "genre": "장르",
    "director": "감독명",
    "actor": "배우명",
    "min_rating": 평점,
    "top_n": 5
  },
  "response_text": "사용자에게 보여줄 응답 텍스트",
  "next_question": "다음 질문",
  "reason_no_match": null 또는 "이유"
}

사용 가능한 도구:
- search_movies: IMDb 영화 데이터에서 키워드, 장르, 감독, 배우, 평점으로 검색
"""
        
        # 대화 히스토리를 OpenAI 형식으로 변환
        messages = [{"role": "system", "content": system_prompt}]
        
        for entry in conversation_history:
            if entry["role"] == "user":
                messages.append({"role": "user", "content": entry["content"]})
            elif entry["role"] == "agent":
                messages.append({"role": "assistant", "content": entry["content"]})
        
        # 현재 사용자 입력 추가
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 멀티 LLM API 호출 (폴백 지원)
            llm_text_response = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # JSON 응답 파싱 시도
            try:
                llm_response = json.loads(llm_text_response)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 응답
                llm_response = {
                    "action": "respond_text",
                    "response_text": llm_text_response,
                    "next_question": "더 자세한 정보를 알려주세요.",
                    "reason_no_match": None
                }
            
            return llm_response
            
        except Exception as e:
            print(f"LLM API 오류: {e}")
            # 오류 시 폴백 응답
            return {
                "action": "respond_text",
                "response_text": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "next_question": "어떤 영화를 찾으시나요?",
                "reason_no_match": None
            }


    def _get_gpt_direct_response(self, user_input):
        """GPT가 직접 제공하는 응답"""
        system_prompt = """
당신은 한국인 사용자를 위한 영화 추론 전문가입니다. 
사용자가 단편적인 정보만 제공해도 대화를 통해 영화를 찾도록 도와주세요.

규칙:
1. 항상 한국어로 응답
2. 사용자의 답변 신뢰성을 평가하고 필요시 재질문
3. 데이터셋에 없을 것 같은 영화라면 그 이유 설명
4. 친근하고 대화형으로 응답
5. 추가 정보를 얻기 위한 구체적인 질문 포함
"""
        
        # 대화 히스토리 포함해서 컨텍스트 제공
        messages = [{"role": "system", "content": system_prompt}]
        
        # 최근 3턴의 대화만 포함 (컨텍스트 길이 제한)
        for entry in self.conversation_history[-6:]:  # user-agent 쌍 3개
            if entry["role"] == "user":
                messages.append({"role": "user", "content": entry["content"]})
            elif entry["role"] == "agent":
                messages.append({"role": "assistant", "content": entry["content"]})
        
        # 현재 사용자 입력 추가
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            return response
        except Exception as e:
            return f"LLM 직접 응답 오류: {str(e)}"
    
    def _translate_korean_to_english_keywords(self, user_input):
        """한국어 입력을 영어 키워드로 변환"""
        # 한국어-영어 키워드 매핑 (발표 시연용 확장)
        keyword_mapping = {
            "감옥": ["prison", "jail", "shawshank"],
            "탈출": ["escape", "break", "breakout"],
            "액션": ["action"],
            "드라마": ["drama"],
            "코미디": ["comedy"],
            "로맨스": ["romance", "romantic"],
            "스릴러": ["thriller"],
            "공포": ["horror"],
            "SF": ["sci-fi", "science fiction"],
            "우주": ["space", "galaxy"],
            "전쟁": ["war", "battle"],
            "범죄": ["crime", "criminal"],
            "가족": ["family"],
            "모험": ["adventure"],
            "마피아": ["mafia", "godfather"],
            "좀비": ["zombie"],
            "슈퍼히어로": ["superhero", "batman", "superman"],
            "크리스토퍼 놀란": ["Christopher Nolan", "Nolan"],
            "톰 행크스": ["Tom Hanks", "Hanks"],
            "레오나르도 디카프리오": ["Leonardo DiCaprio", "DiCaprio"],
            "브래드 피트": ["Brad Pitt"],
            "모건 프리먼": ["Morgan Freeman"],
            "알 파치노": ["Al Pacino"],
            "로버트 드니로": ["Robert De Niro"],
            "조커": ["joker"],
            "배트맨": ["batman", "dark knight"],
            "반지의 제왕": ["lord of the rings", "fellowship"],
            "해리포터": ["harry potter", "potter"],
            "타이타닉": ["titanic"],
            "아바타": ["avatar"]
        }
        
        keywords = []
        user_lower = user_input.lower()
        
        for korean, english_list in keyword_mapping.items():
            if korean in user_lower:
                keywords.extend(english_list)
        
        # 매핑되지 않은 경우 기본 키워드 추가
        if not keywords:
            if "영화" in user_lower:
                keywords = ["movie", "film"]
            else:
                # LLM을 사용해서 키워드 추출
                try:
                    response = self.llm_client.chat_completion(
                        messages=[
                            {"role": "system", "content": "다음 한국어 텍스트에서 영화 검색에 사용할 영어 키워드를 추출하세요. 최대 3개, 쉼표로 구분하여 답하세요."},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.3,
                        max_tokens=50
                    )
                    llm_keywords = response.strip().split(',')
                    keywords = [k.strip() for k in llm_keywords if k.strip()]
                except:
                    keywords = []
        
        return keywords if keywords else [user_input]  # 최소한 원본이라도 반환

    def _evaluate_mcp_quality(self, user_input, mcp_results):
        """MCP 결과의 품질을 평가하여 Tavily 검색 필요성 판단"""
        if not mcp_results:
            return True  # 결과가 없으면 웹 검색
        
        # 특정 키워드가 있으면 웹 검색이 필요할 가능성이 높음
        modern_indicators = [
            "2020", "2021", "2022", "2023", "2024", "2025",
            "최근", "넷플릭스", "디즈니", "마블", "DC", "아마존",
            "좀비", "바이러스", "팬데믹", "코로나", "메타버스",
            "AI", "인공지능", "NFT", "가상현실", "VR"
        ]
        
        user_lower = user_input.lower()
        for indicator in modern_indicators:
            if indicator in user_lower:
                print(f"🔍 '{indicator}' 키워드 감지 - 웹 검색 필요")
                return True
        
        # MCP 결과의 연도 확인
        try:
            latest_year = max([int(movie.get('Released_Year', 0)) for movie in mcp_results])
            if "2024" in user_input and latest_year < 2020:
                print(f"🔍 최신 영화 요청이지만 MCP 최신 결과가 {latest_year}년 - 웹 검색 필요")
                return True
        except:
            pass
        
        return False  # 일반적인 경우는 MCP 결과 사용

    def _get_gpt_feedback_on_mcp(self, user_input, mcp_results):
        """GPT가 MCP 결과에 대해 제공하는 피드백"""
        if not mcp_results:
            return "MCP 검색 결과가 없어서 피드백을 제공할 수 없습니다."
        
        # MCP 결과를 요약
        mcp_summary = []
        for movie in mcp_results[:3]:  # 처음 3개만
            mcp_summary.append(f"- {movie['Series_Title']} ({movie['Released_Year']}, 평점: {movie['IMDB_Rating']})")
        mcp_text = "\n".join(mcp_summary)
        
        system_prompt = f"""
당신은 영화 전문가입니다. 사용자가 "{user_input}"라고 질문했고, 
MCP 시스템이 다음 영화들을 추천했습니다:

{mcp_text}

이 MCP 추천 결과에 대해 평가하고 피드백을 제공하세요. 
추천이 적절한지, 다른 관점에서 볼 때는 어떤지, 추가로 고려할 점은 무엇인지 등을 알려주세요.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"MCP 추천 결과에 대한 피드백을 주세요."}
        ]
        
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            return response
        except Exception as e:
            return f"LLM 피드백 오류: {str(e)}"

    async def process_request(self, user_input):
        self._add_to_history("user", user_input)
        
        # 1. GPT 직접 응답
        gpt_direct_response = self._get_gpt_direct_response(user_input)
        
        # 2. MCP 도구 기반 검색
        mcp_request = self._construct_mcp_request(user_input)
        llm_response = self._send_to_llm(mcp_request)
        
        mcp_movies = []
        mcp_response = ""
        
        # 실제 MCP를 통한 영화 검색 실행
        # 한국어 키워드를 영어로 변환
        english_keywords = self._translate_korean_to_english_keywords(user_input)
        search_params = {
            "keywords": english_keywords,
            "max_results": 5
        }
        
        # 실제 MCP 도구 호출
        mcp_result = await self.real_mcp.call_tool("search_movies", search_params)
        self.real_mcp.log_mcp_interaction("tool_call", {
            "tool": "search_movies", 
            "params": search_params,
            "result_success": "result" in mcp_result
        })
        
        # 실제 MCP 결과에서 영화 데이터 추출
        if "result" in mcp_result and "content" in mcp_result["result"]:
            try:
                content_text = mcp_result["result"]["content"][0]["text"]
                mcp_data = json.loads(content_text)
                
                if mcp_data.get("success"):
                    mcp_movies = mcp_data["movies"]
                    self.last_suggested_movies = mcp_movies
                    
                    if mcp_movies:
                        mcp_response = "🔧 **실제 MCP 시스템 검색 결과:**\n"
                        mcp_response += f"📊 검색된 영화: {mcp_data['count']}개\n"
                        for i, movie in enumerate(mcp_movies[:3], 1):
                            mcp_response += f"{i}. {movie['Series_Title']} ({movie['Released_Year']}) ⭐{movie['IMDB_Rating']}\n"
                    else:
                        mcp_response = "🔧 **실제 MCP 시스템:** 검색 조건에 맞는 영화를 찾지 못했습니다."
                else:
                    mcp_response = f"🔧 **실제 MCP 시스템:** {mcp_data.get('message', '검색 실패')}"
                    
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                mcp_response = f"🔧 **실제 MCP 시스템 오류:** 응답 파싱 실패 ({str(e)})"
        elif "error" in mcp_result:
            mcp_response = f"🔧 **실제 MCP 시스템 오류:** {mcp_result['error']['message']}"
        else:
            mcp_response = "🔧 **실제 MCP 시스템 오류:** 예상치 못한 응답 형식"
        
        # 3. MCP 결과 품질 확인 후 Tavily 웹 검색 수행
        tavily_response = ""
        
        # MCP 결과 품질 평가 (관련성 확인)
        should_use_tavily = self._evaluate_mcp_quality(user_input, mcp_movies)
        
        if len(mcp_movies) < 3 or should_use_tavily:  # MCP 결과가 부족하거나 품질이 낮으면 웹 검색
            print("🌐 MCP 결과가 부족하여 Tavily 웹 검색을 수행합니다...")
            tavily_result = self.tavily_searcher.search_movie_by_description(
                self.conversation_history, user_input
            )
            
            if tavily_result["success"]:
                tavily_response = "## 🌐 Tavily 웹 검색 결과:\n"
                tavily_response += f"**검색 쿼리:** {tavily_result['search_query']}\n\n"
                
                for i, movie in enumerate(tavily_result["results"][:3], 1):
                    tavily_response += f"{i}. **{movie['cleaned_title']}** ({movie['source']})\n"
                    tavily_response += f"   📝 {movie['content']}\n"
                    tavily_response += f"   🔗 [더 보기]({movie['url']})\n\n"
            else:
                tavily_response = f"## 🌐 Tavily 웹 검색 결과:\n❌ {tavily_result['error']}\n"
        
        # 4. GPT가 MCP 결과에 대한 피드백
        gpt_feedback = self._get_gpt_feedback_on_mcp(user_input, mcp_movies)
        
        # 5. 통합 응답 생성 (wish.txt 요구사항에 따라 개선)
        combined_response = f"""🎬 **영화 추론 결과:**

{gpt_direct_response}

---

{mcp_response}

---

💡 **추가 분석:**
{gpt_feedback}

🤔 **다음 질문:** 혹시 기억나는 다른 단서가 있으신가요? (출연 배우, 줄거리, 인상 깊었던 장면 등)"""

        # Tavily 결과가 있으면 추가
        if tavily_response:
            combined_response += f"""

---

{tavily_response}"""

        self._add_to_history("agent", combined_response)
        return combined_response, mcp_movies

async def main():
    supervisor = AgentSupervisor()
    print("영화 추론 에이전트입니다. 찾으시는 영화에 대해 단편적인 정보를 말씀해주세요. (종료하려면 'exit' 입력)")

    while True:
        user_input = input("사용자: ")
        if user_input.lower() == 'exit':
            print("에이전트를 종료합니다.")
            break
        
        response, movies = await supervisor.process_request(user_input)
        print(f"에이전트: {response}")
        print("-" * 30)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
