#!/usr/bin/env python3
"""
GPT-MCP 병행 응답 상세 테스트
"""

import os
from dotenv import load_dotenv
from agent_supervisor import AgentSupervisor

# Load environment variables
load_dotenv()

def test_detailed_response():
    print("=== GPT-MCP 병행 응답 상세 테스트 ===")
    
    supervisor = AgentSupervisor()
    
    # 테스트 쿼리
    query = "감옥에서 탈출하는 영화"
    print(f"\n질문: {query}")
    print("=" * 50)
    
    try:
        response, suggested_movies = supervisor.process_request(query)
        print(response)
        print("\n" + "=" * 50)
        print(f"추천 영화 수: {len(suggested_movies)}")
        
        if suggested_movies:
            print("\n추천 영화 상세:")
            for i, movie in enumerate(suggested_movies, 1):
                print(f"{i}. {movie.get('Series_Title', 'N/A')}")
                print(f"   연도: {movie.get('Released_Year', 'N/A')}")
                print(f"   평점: {movie.get('IMDB_Rating', 'N/A')}")
                print(f"   장르: {movie.get('Genre', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_response()