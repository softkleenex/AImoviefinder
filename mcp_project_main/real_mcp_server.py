#!/usr/bin/env python3
"""
실제 MCP 서버 - 영화 검색 전용
MCP (Model Context Protocol) 표준을 준수하는 실제 서버
"""

import asyncio
import json
import logging
from typing import Any, Sequence
import pandas as pd

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("movie-mcp-server")

class MovieMCPServer:
    def __init__(self):
        # MCP 서버 초기화
        self.server = Server("movie-search-server")
        
        # 영화 데이터 로드
        try:
            self.movie_df = pd.read_csv('dataset/imdb_top_1000.csv')
            logger.info(f"✅ IMDb 데이터 로드 완료: {len(self.movie_df)}개 영화")
        except Exception as e:
            logger.error(f"❌ 데이터 로드 실패: {e}")
            self.movie_df = pd.DataFrame()  # 빈 데이터프레임
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """MCP 핸들러들 설정"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """사용 가능한 도구 목록 반환"""
            return [
                Tool(
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
                Tool(
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
                ),
                Tool(
                    name="get_top_movies_by_genre",
                    description="장르별 최고 평점 영화들을 조회합니다",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "genre": {
                                "type": "string",
                                "description": "장르명 (예: Action, Drama, Comedy)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "결과 수 제한",
                                "default": 10
                            }
                        },
                        "required": ["genre"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """도구 호출 처리"""
            logger.info(f"🔧 도구 호출: {name} with {arguments}")
            
            if name == "search_movies":
                return await self._search_movies(**arguments)
            elif name == "get_movie_details":
                return await self._get_movie_details(**arguments)
            elif name == "get_top_movies_by_genre":
                return await self._get_top_movies_by_genre(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _search_movies(self, keywords=None, genre=None, director=None, 
                           actor=None, min_rating=None, max_rating=None, max_results=5):
        """영화 검색 실행"""
        try:
            if self.movie_df.empty:
                return [TextContent(
                    type="text",
                    text="❌ 영화 데이터가 로드되지 않았습니다."
                )]
            
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
                return [TextContent(
                    type="text",
                    text=f"🔍 검색 결과가 없습니다.\n적용된 필터: {', '.join(applied_filters) if applied_filters else '없음'}"
                )]
            
            # 성공 응답 생성
            response_text = f"🎬 **영화 검색 결과** ({len(results)}개 발견)\n"
            response_text += f"📋 적용된 필터: {', '.join(applied_filters) if applied_filters else '없음'}\n\n"
            
            for i, (_, movie) in enumerate(results.iterrows(), 1):
                response_text += f"{i}. **{movie['Series_Title']}** ({movie['Released_Year']})\n"
                response_text += f"   ⭐ 평점: {movie['IMDB_Rating']}/10\n"  
                response_text += f"   🎭 장르: {movie['Genre']}\n"
                response_text += f"   🎬 감독: {movie['Director']}\n"
                response_text += f"   🌟 주연: {movie['Star1']}, {movie['Star2']}\n"
                response_text += f"   📝 줄거리: {movie['Overview'][:100]}...\n\n"
            
            # JSON 데이터도 함께 반환
            movies_json = results.to_dict('records')
            
            return [
                TextContent(
                    type="text",
                    text=response_text
                ),
                TextContent(
                    type="text", 
                    text=f"```json\n{json.dumps(movies_json, ensure_ascii=False, indent=2)}\n```"
                )
            ]
            
        except Exception as e:
            logger.error(f"❌ 영화 검색 오류: {e}")
            return [TextContent(
                type="text",
                text=f"❌ 검색 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def _get_movie_details(self, movie_title: str):
        """영화 상세 정보 조회"""
        try:
            if self.movie_df.empty:
                return [TextContent(type="text", text="❌ 영화 데이터가 로드되지 않았습니다.")]
            
            # 영화 찾기
            movie_mask = self.movie_df['Series_Title'].str.contains(movie_title, case=False, na=False)
            matching_movies = self.movie_df[movie_mask]
            
            if matching_movies.empty:
                return [TextContent(
                    type="text",
                    text=f"❌ '{movie_title}'와 일치하는 영화를 찾을 수 없습니다."
                )]
            
            # 첫 번째 매치 사용
            movie = matching_movies.iloc[0]
            
            details_text = f"""
🎬 **영화 상세 정보**

**제목**: {movie['Series_Title']}
**개봉연도**: {movie['Released_Year']}
**관람등급**: {movie.get('Certificate', 'N/A')}
**러닝타임**: {movie['Runtime']}
**장르**: {movie['Genre']}

**평점 정보**
- IMDb 평점: {movie['IMDB_Rating']}/10 ({movie['No_of_Votes']:,}표)
- 메타스코어: {movie.get('Meta_score', 'N/A')}/100

**제작진**
- 감독: {movie['Director']}
- 주연배우: {movie['Star1']}, {movie['Star2']}, {movie['Star3']}, {movie['Star4']}

**줄거리**
{movie['Overview']}

**박스오피스**
- 총 수익: ${movie.get('Gross', 'N/A')}

**포스터**: {movie.get('Poster_Link', 'N/A')}
"""
            
            return [TextContent(type="text", text=details_text)]
            
        except Exception as e:
            logger.error(f"❌ 영화 상세정보 조회 오류: {e}")
            return [TextContent(
                type="text",
                text=f"❌ 상세정보 조회 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def _get_top_movies_by_genre(self, genre: str, limit: int = 10):
        """장르별 최고 평점 영화 조회"""
        try:
            if self.movie_df.empty:
                return [TextContent(type="text", text="❌ 영화 데이터가 로드되지 않았습니다.")]
            
            # 장르 필터링
            genre_movies = self.movie_df[
                self.movie_df['Genre'].str.contains(genre, case=False, na=False)
            ]
            
            if genre_movies.empty:
                return [TextContent(
                    type="text",
                    text=f"❌ '{genre}' 장르의 영화를 찾을 수 없습니다."
                )]
            
            # 평점순 정렬
            top_movies = genre_movies.sort_values('IMDB_Rating', ascending=False).head(limit)
            
            response_text = f"🏆 **{genre} 장르 최고 평점 영화 Top {len(top_movies)}**\n\n"
            
            for i, (_, movie) in enumerate(top_movies.iterrows(), 1):
                response_text += f"{i}. **{movie['Series_Title']}** ({movie['Released_Year']})\n"
                response_text += f"   ⭐ {movie['IMDB_Rating']}/10\n"
                response_text += f"   🎬 {movie['Director']}\n\n"
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"❌ 장르별 영화 조회 오류: {e}")
            return [TextContent(
                type="text",
                text=f"❌ 장르별 영화 조회 중 오류가 발생했습니다: {str(e)}"
            )]

async def main():
    """MCP 서버 실행"""
    logger.info("🚀 실제 MCP 영화 서버 시작...")
    
    # 서버 인스턴스 생성
    movie_server = MovieMCPServer()
    
    # stdio를 통한 서버 실행
    import sys
    logger.info("✅ MCP 서버가 stdio 모드로 실행 중입니다.")
    logger.info("📡 클라이언트 연결을 기다리는 중...")
    
    await movie_server.server.run(
        read_stream=sys.stdin, 
        write_stream=sys.stdout,
        initialization_options=InitializationOptions(
            server_name="movie-search-server",
            server_version="1.0.0",
            capabilities=movie_server.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 서버 종료됨")
    except Exception as e:
        logger.error(f"❌ 서버 오류: {e}")
        raise