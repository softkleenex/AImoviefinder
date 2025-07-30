#!/usr/bin/env python3
"""
간단한 실제 MCP 서버 - 영화 검색 전용
MCP (Model Context Protocol) 표준을 준수하는 실제 서버 (간소화 버전)
"""

import asyncio
import json
import logging
import pandas as pd
from typing import Any, Sequence

# MCP SDK 임포트
from mcp import types
from mcp.server import Server, NotificationOptions
from mcp import stdio_server

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple-movie-mcp-server")

class SimpleMovieMCPServer:
    def __init__(self):
        # 영화 데이터 로드
        try:
            self.movie_df = pd.read_csv('dataset/imdb_top_1000.csv')
            logger.info(f"✅ IMDb 데이터 로드 완료: {len(self.movie_df)}개 영화")
        except Exception as e:
            logger.error(f"❌ 데이터 로드 실패: {e}")
            self.movie_df = pd.DataFrame()  # 빈 데이터프레임
    
    async def search_movies(self, keywords=None, genre=None, director=None, 
                           actor=None, min_rating=None, max_rating=None, max_results=5):
        """영화 검색 실행"""
        try:
            if self.movie_df.empty:
                return {
                    "error": "영화 데이터가 로드되지 않았습니다."
                }
            
            results = self.movie_df.copy()
            applied_filters = []
            
            # 키워드 검색
            if keywords and len(keywords) > 0:
                keyword_pattern = '|'.join([str(k) for k in keywords])
                mask = (
                    results['Series_Title'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Overview'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Genre'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Director'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Star1'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Star2'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Star3'].str.contains(keyword_pattern, case=False, na=False) |
                    results['Star4'].str.contains(keyword_pattern, case=False, na=False)
                )
                results = results[mask]
                applied_filters.append(f"키워드: {keywords}")
            
            # 장르 필터
            if genre:
                results = results[results['Genre'].str.contains(genre, case=False, na=False)]
                applied_filters.append(f"장르: {genre}")
            
            # 감독 필터  
            if director:
                results = results[results['Director'].str.contains(director, case=False, na=False)]
                applied_filters.append(f"감독: {director}")
            
            # 배우 필터
            if actor:
                actor_mask = (
                    results['Star1'].str.contains(actor, case=False, na=False) |
                    results['Star2'].str.contains(actor, case=False, na=False) |
                    results['Star3'].str.contains(actor, case=False, na=False) |
                    results['Star4'].str.contains(actor, case=False, na=False)
                )
                results = results[actor_mask]
                applied_filters.append(f"배우: {actor}")
            
            # 평점 필터
            if min_rating is not None:
                results = results[results['IMDB_Rating'] >= min_rating]
                applied_filters.append(f"최소평점: {min_rating}")
            
            if max_rating is not None:
                results = results[results['IMDB_Rating'] <= max_rating]
                applied_filters.append(f"최대평점: {max_rating}")
            
            # 결과 정렬 및 제한
            results = results.sort_values('IMDB_Rating', ascending=False).head(max_results)
            
            # 결과 포맷팅
            if results.empty:
                return {
                    "success": False,
                    "message": f"검색 결과가 없습니다. 적용된 필터: {', '.join(applied_filters) if applied_filters else '없음'}"
                }
            
            # 성공 응답 생성
            movies_data = []
            for _, movie in results.iterrows():
                movies_data.append({
                    "title": movie['Series_Title'],
                    "year": movie['Released_Year'],
                    "rating": movie['IMDB_Rating'],
                    "genre": movie['Genre'],
                    "director": movie['Director'],
                    "stars": [movie['Star1'], movie['Star2'], movie['Star3'], movie['Star4']],
                    "overview": movie['Overview']
                })
            
            return {
                "success": True,
                "count": len(movies_data),
                "filters": applied_filters,
                "movies": movies_data
            }
            
        except Exception as e:
            logger.error(f"❌ 영화 검색 오류: {e}")
            return {
                "error": f"검색 중 오류가 발생했습니다: {str(e)}"
            }

    async def get_movie_details(self, movie_title: str):
        """영화 상세 정보 조회"""
        try:
            if self.movie_df.empty:
                return {"error": "영화 데이터가 로드되지 않았습니다."}
            
            # 영화 찾기
            movie_mask = self.movie_df['Series_Title'].str.contains(movie_title, case=False, na=False)
            matching_movies = self.movie_df[movie_mask]
            
            if matching_movies.empty:
                return {"error": f"'{movie_title}'와 일치하는 영화를 찾을 수 없습니다."}
            
            # 첫 번째 매치 사용
            movie = matching_movies.iloc[0]
            
            return {
                "success": True,
                "movie": {
                    "title": movie['Series_Title'],
                    "year": movie['Released_Year'],
                    "certificate": movie.get('Certificate', 'N/A'),
                    "runtime": movie['Runtime'],
                    "genre": movie['Genre'],
                    "rating": movie['IMDB_Rating'],
                    "votes": movie['No_of_Votes'],
                    "metascore": movie.get('Meta_score', 'N/A'),
                    "director": movie['Director'],
                    "stars": [movie['Star1'], movie['Star2'], movie['Star3'], movie['Star4']],
                    "overview": movie['Overview'],
                    "gross": movie.get('Gross', 'N/A'),
                    "poster": movie.get('Poster_Link', 'N/A')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 영화 상세정보 조회 오류: {e}")
            return {"error": f"상세정보 조회 중 오류가 발생했습니다: {str(e)}"}

# 글로벌 서버 인스턴스
movie_server = SimpleMovieMCPServer()

# MCP 서버 설정
server = Server("simple-movie-search-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        types.Tool(
            name="search_movies",
            description="IMDb Top 1000 데이터에서 영화를 검색합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "검색할 키워드 목록"
                    },
                    "genre": {
                        "type": "string",
                        "description": "영화 장르 (예: Action, Drama, Comedy)"
                    },
                    "director": {
                        "type": "string", 
                        "description": "감독 이름"
                    },
                    "actor": {
                        "type": "string",
                        "description": "배우 이름"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "최소 IMDb 평점"
                    },
                    "max_rating": {
                        "type": "number",
                        "description": "최대 IMDb 평점" 
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "최대 결과 수",
                        "default": 5
                    }
                }
            }
        ),
        types.Tool(
            name="get_movie_details",
            description="특정 영화의 상세 정보를 조회합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "movie_title": {
                        "type": "string",
                        "description": "조회할 영화 제목"
                    }
                },
                "required": ["movie_title"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """도구 호출 처리"""
    logger.info(f"🔧 도구 호출: {name} with {arguments}")
    
    if name == "search_movies":
        result = await movie_server.search_movies(**arguments)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    elif name == "get_movie_details":
        result = await movie_server.get_movie_details(**arguments)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Serve over stdio
    async with stdio_server(server) as (read_stream, write_stream):
        logger.info("🚀 Simple MCP 영화 서버가 stdio에서 실행 중입니다.")
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    logger.info("📡 Simple MCP 서버 시작...")
    asyncio.run(main())