#!/usr/bin/env python3
"""
MCP 기능 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from agent_supervisor import AgentSupervisor

# Load environment variables
load_dotenv()

def test_mcp_functionality():
    print("=== MCP 기능 테스트 시작 ===")
    
    try:
        # AgentSupervisor 초기화
        supervisor = AgentSupervisor()
        print("✅ AgentSupervisor 초기화 성공")
        
        # 테스트 쿼리
        test_queries = [
            "감옥에서 탈출하는 영화",
            "크리스토퍼 놀란 감독 영화",
            "액션 영화 추천해줘"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 테스트 {i}: {query} ---")
            try:
                response, suggested_movies = supervisor.process_request(query)
                print(f"✅ 응답: {response[:100]}...")
                print(f"✅ 추천 영화 수: {len(suggested_movies)}")
                
                if suggested_movies:
                    print("추천 영화:")
                    for j, movie in enumerate(suggested_movies[:3], 1):  # 처음 3개만 출력
                        print(f"  {j}. {movie.get('Series_Title', 'N/A')} ({movie.get('Released_Year', 'N/A')})")
                
            except Exception as e:
                print(f"❌ 테스트 {i} 실패: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n=== MCP 기능 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_functionality()