#!/usr/bin/env python3
"""
Tavily 간단 테스트
"""

import os
from dotenv import load_dotenv
from agent_supervisor import AgentSupervisor

# Load environment variables
load_dotenv()

def test_tavily_simple():
    print("=== Tavily 간단 테스트 ===")
    
    supervisor = AgentSupervisor()
    
    # MCP 데이터베이스에 없을 것 같은 영화 질문
    query = "2024년에 나온 한국 영화 중에서 좀비가 나오는 영화"
    
    print(f"질문: {query}")
    print('='*60)
    
    try:
        response, suggested_movies = supervisor.process_request(query)
        print(response)
        print(f"\n추천 영화 수: {len(suggested_movies)}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tavily_simple()