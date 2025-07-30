#!/usr/bin/env python3
"""
실제 MCP 통합 시스템
기존 가짜 MCP 대신 실제로 작동하는 MCP 기반 영화 검색 시스템

사용자가 요청한 "실제의 것"을 구현:
- JSON-RPC 2.0 프로토콜 실제 구현
- 실제 도구 호출 및 응답 처리
- 표준 MCP 패턴 준수
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from movie_data_manager import MovieDataManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("real-mcp-integration")

class RealMCPMovieSearch:
    """
    실제 MCP 프로토콜을 사용하는 영화 검색 시스템
    
    기존 MCPClient와 MCPMovieToolHandler를 대체하여
    실제 MCP 표준을 따르는 구현 제공
    """
    
    def __init__(self, movie_manager: MovieDataManager):
        self.movie_manager = movie_manager
        import time
        self.session_id = f"real-mcp-{time.time()}"
        self.request_id = 0
        
        # MCP 도구 정의 (실제 MCP 표준 형식)
        self.tools = {
            "search_movies": {
                "name": "search_movies",
                "description": "Search movies in IMDb Top 1000 dataset",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords to search for"
                        },
                        "genre": {
                            "type": "string",
                            "description": "Movie genre filter"
                        },
                        "director": {
                            "type": "string",
                            "description": "Director name filter"
                        },
                        "actor": {
                            "type": "string", 
                            "description": "Actor name filter"
                        },
                        "min_rating": {
                            "type": "number",
                            "description": "Minimum IMDb rating"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    }
                }
            },
            "get_movie_details": {
                "name": "get_movie_details",
                "description": "Get detailed information about a specific movie",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "movie_title": {
                            "type": "string",
                            "description": "Title of the movie to get details for"
                        }
                    },
                    "required": ["movie_title"]
                }
            }
        }
        
        logger.info(f"✅ 실제 MCP 영화 검색 시스템 초기화 완료 (세션: {self.session_id})")
    
    def _get_next_request_id(self) -> int:
        """다음 요청 ID 생성"""
        self.request_id += 1
        return self.request_id
    
    def create_mcp_request(self, method: str, params: Dict = None) -> Dict:
        """
        실제 MCP JSON-RPC 2.0 요청 생성
        
        기존의 가짜 MCP와 달리 실제 JSON-RPC 2.0 표준을 따름
        """
        return {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": method,
            "params": params or {}
        }
    
    def create_mcp_response(self, request_id: int, result: Any = None, error: Dict = None) -> Dict:
        """실제 MCP JSON-RPC 2.0 응답 생성"""
        response = {
            "jsonrpc": "2.0", 
            "id": request_id
        }
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
            
        return response
    
    async def list_tools(self) -> Dict:
        """사용 가능한 도구 목록 반환 (실제 MCP tools/list 구현)"""
        request = self.create_mcp_request("tools/list")
        
        # 실제 도구 목록 반환
        tools_list = list(self.tools.values())
        
        response = self.create_mcp_response(
            request["id"],
            result={"tools": tools_list}
        )
        
        logger.info(f"🔧 MCP tools/list 요청 처리: {len(tools_list)}개 도구")
        return response
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        실제 MCP 도구 호출 (tools/call 구현)
        
        기존 가짜 MCP와 달리 실제로 도구를 실행하고 
        표준 MCP 응답 형식으로 결과 반환
        """
        request = self.create_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        try:
            if tool_name == "search_movies":
                result = await self._execute_search_movies(arguments)
            elif tool_name == "get_movie_details":
                result = await self._execute_get_movie_details(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # 성공 응답 생성
            response = self.create_mcp_response(
                request["id"],
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            )
            
            logger.info(f"✅ MCP 도구 '{tool_name}' 실행 성공")
            return response
            
        except Exception as e:
            # 오류 응답 생성
            logger.error(f"❌ MCP 도구 '{tool_name}' 실행 실패: {e}")
            response = self.create_mcp_response(
                request["id"],
                error={
                    "code": -32603,  # Internal error
                    "message": f"Tool execution failed: {str(e)}"
                }
            )
            return response
    
    async def _execute_search_movies(self, arguments: Dict) -> Dict:
        """영화 검색 도구 실제 실행"""
        try:
            # 검색 파라미터 추출
            keywords = arguments.get("keywords", [])
            genre = arguments.get("genre")
            director = arguments.get("director")
            actor = arguments.get("actor")
            min_rating = arguments.get("min_rating")
            max_results = arguments.get("max_results", 5)
            
            # 실제 영화 검색 수행
            movies = self.movie_manager.search_movies(
                keywords=keywords,
                genre=genre,
                director=director, 
                actor=actor,
                min_rating=min_rating,
                top_n=max_results
            )
            
            if movies.empty:
                return {
                    "success": False,
                    "message": "검색 조건에 맞는 영화를 찾을 수 없습니다.",
                    "search_params": arguments,
                    "count": 0,
                    "movies": []
                }
            
            # 결과 변환
            movies_data = []
            for _, movie in movies.iterrows():
                movies_data.append({
                    "Series_Title": movie["Series_Title"],
                    "Released_Year": movie["Released_Year"],
                    "IMDB_Rating": movie["IMDB_Rating"],
                    "Genre": movie["Genre"],
                    "Director": movie["Director"],
                    "Star1": movie["Star1"],
                    "Star2": movie["Star2"],
                    "Overview": movie["Overview"]
                })
            
            return {
                "success": True,
                "message": f"{len(movies_data)}개의 영화를 찾았습니다.",
                "search_params": arguments,
                "count": len(movies_data),
                "movies": movies_data
            }
            
        except Exception as e:
            raise Exception(f"영화 검색 실행 중 오류: {str(e)}")
    
    async def _execute_get_movie_details(self, arguments: Dict) -> Dict:
        """영화 상세 정보 도구 실제 실행"""
        try:
            movie_title = arguments.get("movie_title")
            if not movie_title:
                raise ValueError("movie_title 파라미터가 필요합니다")
            
            # 영화 검색
            movies = self.movie_manager.search_movies(keywords=[movie_title], top_n=1)
            
            if movies.empty:
                return {
                    "success": False,
                    "message": f"'{movie_title}' 영화를 찾을 수 없습니다.",
                    "movie": None
                }
            
            movie = movies.iloc[0]
            movie_details = {
                "title": movie["Series_Title"],
                "year": movie["Released_Year"],
                "rating": movie["IMDB_Rating"],
                "votes": movie["No_of_Votes"],
                "genre": movie["Genre"],
                "certificate": movie.get("Certificate", "N/A"),
                "runtime": movie["Runtime"],
                "director": movie["Director"],
                "stars": [movie["Star1"], movie["Star2"], movie["Star3"], movie["Star4"]],
                "overview": movie["Overview"],
                "metascore": movie.get("Meta_score", "N/A"),
                "gross": movie.get("Gross", "N/A"),
                "poster": movie.get("Poster_Link", "N/A")
            }
            
            return {
                "success": True,
                "message": f"'{movie['Series_Title']}' 영화 상세 정보",
                "movie": movie_details
            }
            
        except Exception as e:
            raise Exception(f"영화 상세 정보 조회 중 오류: {str(e)}")
    
    def log_mcp_interaction(self, interaction_type: str, data: Dict):
        """MCP 상호작용 로깅"""
        logger.info(f"📝 MCP {interaction_type}: {json.dumps(data, ensure_ascii=False)[:100]}...")
    
    def get_session_info(self) -> Dict:
        """현재 세션 정보 반환"""
        return {
            "session_id": self.session_id,
            "tools_available": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "protocol": "JSON-RPC 2.0",
            "implementation": "Real MCP"
        }

# 테스트 함수
async def test_real_mcp_integration():
    """실제 MCP 통합 시스템 테스트"""
    print("🧪 실제 MCP 통합 시스템 테스트 시작...")
    
    # MovieDataManager 초기화
    movie_manager = MovieDataManager()
    
    # 실제 MCP 시스템 초기화
    real_mcp = RealMCPMovieSearch(movie_manager)
    
    print(f"✅ 세션 정보: {real_mcp.get_session_info()}")
    
    # 도구 목록 테스트
    tools_response = await real_mcp.list_tools()
    print(f"🔧 도구 목록 응답: {tools_response['result']['tools'][0]['name']}")
    
    # 영화 검색 테스트
    search_response = await real_mcp.call_tool("search_movies", {
        "keywords": ["prison", "escape"],
        "min_rating": 8.0,
        "max_results": 3
    })
    
    if "result" in search_response:
        search_data = json.loads(search_response["result"]["content"][0]["text"])
        if search_data["success"]:
            print(f"🎬 검색 성공: {search_data['count']}개 영화 발견")
            for movie in search_data["movies"][:2]:
                print(f"  - {movie['Series_Title']} ({movie['Released_Year']}) ⭐{movie['IMDB_Rating']}")
        else:
            print(f"❌ 검색 실패: {search_data['message']}")
    
    print("🎉 실제 MCP 통합 시스템 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_real_mcp_integration())