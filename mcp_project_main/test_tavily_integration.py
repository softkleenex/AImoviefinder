#!/usr/bin/env python3
"""
Tavily 통합 테스트
"""

import os
from dotenv import load_dotenv
from agent_supervisor import AgentSupervisor

# Load environment variables
load_dotenv()

def test_tavily_integration():
    print("=== Tavily 통합 테스트 ===")
    
    supervisor = AgentSupervisor()
    
    # MCP 데이터베이스에 없을 것 같은 영화 질문
    test_queries = [
        "2023년에 나온 한국 영화 중에서 좀비가 나오는 영화",
        "넷플릭스 오리지널 시리즈 중에서 로봇이 나오는 작품",
        "최근에 나온 마블 영화 중에서 다중우주를 다루는 영화"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"테스트 {i}: {query}")
        print('='*60)
        
        try:
            response, suggested_movies = supervisor.process_request(query)
            print(response)
            print(f"\n추천 영화 수: {len(suggested_movies)}")
            
        except Exception as e:
            print(f"❌ 테스트 {i} 실패: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
        input("다음 테스트를 위해 Enter를 누르세요...")

if __name__ == "__main__":
    test_tavily_integration()