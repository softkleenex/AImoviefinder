"""
Tavily 웹 검색을 통한 영화 정보 검색 모듈
"""

import os
from typing import List, Dict, Any
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class TavilyMovieSearcher:
    def __init__(self):
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            print("⚠️ TAVILY_API_KEY가 설정되지 않았습니다.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=api_key)
    
    def search_movie_by_description(self, conversation_history: List[Dict], current_query: str) -> Dict[str, Any]:
        """대화 기록을 바탕으로 영화 검색 쿼리를 생성하고 웹 검색"""
        if not self.client:
            return {
                "success": False,
                "error": "Tavily API 키가 설정되지 않았습니다.",
                "results": []
            }
        
        try:
            # 대화 기록을 바탕으로 검색 쿼리 생성
            search_query = self._generate_search_query(conversation_history, current_query)
            
            print(f"🔍 Tavily 검색 쿼리: {search_query}")
            
            # Tavily로 웹 검색 실행
            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5,
                include_domains=["imdb.com", "themoviedb.org", "rottentomatoes.com", "wikipedia.org"]
            )
            
            # 검색 결과 처리
            movie_info = self._parse_search_results(response)
            
            return {
                "success": True,
                "search_query": search_query,
                "results": movie_info,
                "raw_response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Tavily 검색 오류: {str(e)}",
                "results": []
            }
    
    def _generate_search_query(self, conversation_history: List[Dict], current_query: str) -> str:
        """대화 기록을 바탕으로 검색 쿼리 생성"""
        # 대화 기록에서 중요한 키워드 추출
        all_context = []
        
        for entry in conversation_history[-3:]:  # 최근 3개 대화만 사용
            if entry.get("role") == "user":
                all_context.append(entry.get("content", ""))
        
        all_context.append(current_query)
        context_text = " ".join(all_context)
        
        # 영화 검색에 최적화된 쿼리 생성
        search_query = f"movie film {current_query}"
        
        # 특정 키워드가 포함된 경우 추가
        if "감옥" in context_text or "탈출" in context_text:
            search_query += " prison escape"
        if "액션" in context_text:
            search_query += " action"
        if "드라마" in context_text:
            search_query += " drama"
        if "코미디" in context_text:
            search_query += " comedy"
        
        return search_query
    
    def _parse_search_results(self, response: Dict) -> List[Dict[str, str]]:
        """Tavily 검색 결과를 파싱하여 영화 정보 추출"""
        movies = []
        
        if "results" not in response:
            return movies
        
        for result in response["results"][:5]:  # 상위 5개 결과만
            movie_info = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")[:300] + "...",  # 300자로 제한
                "source": self._extract_source_name(result.get("url", ""))
            }
            
            # 영화 제목 추출 시도
            if "title" in result:
                title = result["title"]
                # IMDb나 다른 사이트의 제목 형식 정리
                if " - IMDb" in title:
                    movie_info["cleaned_title"] = title.replace(" - IMDb", "")
                elif " (" in title and ")" in title:
                    # (년도) 형식 처리
                    movie_info["cleaned_title"] = title
                else:
                    movie_info["cleaned_title"] = title
            
            movies.append(movie_info)
        
        return movies
    
    def _extract_source_name(self, url: str) -> str:
        """URL에서 소스 이름 추출"""
        if "imdb.com" in url:
            return "IMDb"
        elif "themoviedb.org" in url:
            return "TMDb"
        elif "rottentomatoes.com" in url:
            return "Rotten Tomatoes"
        elif "wikipedia.org" in url:
            return "Wikipedia"
        else:
            return "Web"

# 테스트용 함수
def test_tavily_search():
    searcher = TavilyMovieSearcher()
    
    # 테스트 대화 기록
    conversation = [
        {"role": "user", "content": "감옥에서 탈출하는 영화 찾고 있어"},
        {"role": "user", "content": "주인공이 무죄인데 억울하게 갇힌 영화야"}
    ]
    
    current_query = "20년 넘게 감옥에 있다가 탈출하는 영화"
    
    result = searcher.search_movie_by_description(conversation, current_query)
    
    print("=== Tavily 검색 결과 ===")
    print(f"성공: {result['success']}")
    if result['success']:
        print(f"검색 쿼리: {result['search_query']}")
        print("\n검색된 영화들:")
        for i, movie in enumerate(result['results'], 1):
            print(f"{i}. {movie['cleaned_title']} ({movie['source']})")
            print(f"   내용: {movie['content']}")
            print(f"   URL: {movie['url']}\n")
    else:
        print(f"오류: {result['error']}")

if __name__ == "__main__":
    test_tavily_search()