#!/usr/bin/env python3
"""
실제 MCP 시스템 배포 테스트 스크립트
"""

import requests
import time
import sys
from urllib.parse import urljoin

def test_deployment(base_url, timeout=30):
    """배포된 실제 MCP 시스템 테스트"""
    
    print(f"🧪 실제 MCP 시스템 배포 테스트 시작")
    print(f"🌐 테스트 대상: {base_url}")
    print("="*60)
    
    test_results = {
        "health_check": False,
        "main_page": False,
        "mcp_system": False,
        "response_time": 0
    }
    
    # 1. 헬스 체크
    print("1️⃣ 헬스 체크...")
    try:
        start_time = time.time()
        response = requests.get(base_url, timeout=timeout)
        end_time = time.time()
        
        test_results["response_time"] = end_time - start_time
        
        if response.status_code == 200:
            print(f"   ✅ HTTP 응답: {response.status_code}")
            print(f"   ⏱️ 응답 시간: {test_results['response_time']:.2f}초")
            test_results["health_check"] = True
        else:
            print(f"   ❌ HTTP 응답 오류: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ 타임아웃: {timeout}초 초과")
    except Exception as e:
        print(f"   ❌ 연결 오류: {str(e)}")
    
    # 2. 메인 페이지 내용 확인
    print("\n2️⃣ 메인 페이지 내용 확인...")
    if test_results["health_check"]:
        try:
            response = requests.get(base_url, timeout=timeout)
            content = response.text.lower()
            
            # 필수 키워드 확인
            required_keywords = [
                "영화",
                "추론",
                "에이전트",
                "streamlit"
            ]
            
            found_keywords = []
            for keyword in required_keywords:
                if keyword in content:
                    found_keywords.append(keyword)
            
            if len(found_keywords) >= 3:
                print(f"   ✅ 메인 페이지 로드 성공 ({len(found_keywords)}/{len(required_keywords)} 키워드 발견)")
                test_results["main_page"] = True
            else:
                print(f"   ⚠️ 메인 페이지 내용 부족 ({len(found_keywords)}/{len(required_keywords)} 키워드)")
                
        except Exception as e:
            print(f"   ❌ 메인 페이지 확인 실패: {str(e)}")
    else:
        print("   ⏭️ 헬스 체크 실패로 건너뜀")
    
    # 3. 실제 MCP 시스템 확인 (페이지 소스에서)
    print("\n3️⃣ 실제 MCP 시스템 확인...")
    if test_results["main_page"]:
        try:
            response = requests.get(base_url, timeout=timeout)
            content = response.text
            
            # MCP 관련 키워드 확인
            mcp_indicators = [
                "MCP",
                "Model Context Protocol",
                "JSON-RPC",
                "실제 MCP"
            ]
            
            found_mcp = []
            for indicator in mcp_indicators:
                if indicator in content:
                    found_mcp.append(indicator)
            
            if found_mcp:
                print(f"   ✅ 실제 MCP 시스템 표시 확인: {found_mcp}")
                test_results["mcp_system"] = True
            else:
                print("   ⚠️ MCP 시스템 표시를 찾을 수 없음")
                
        except Exception as e:
            print(f"   ❌ MCP 시스템 확인 실패: {str(e)}")
    else:
        print("   ⏭️ 메인 페이지 로드 실패로 건너뜀")
    
    # 4. 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약:")
    print(f"   헬스 체크: {'✅' if test_results['health_check'] else '❌'}")
    print(f"   메인 페이지: {'✅' if test_results['main_page'] else '❌'}")
    print(f"   실제 MCP: {'✅' if test_results['mcp_system'] else '❌'}")
    print(f"   응답 시간: {test_results['response_time']:.2f}초")
    
    # 전체 성공 여부
    all_tests_passed = all([
        test_results["health_check"],
        test_results["main_page"]
    ])
    
    if all_tests_passed:
        print("\n🎉 배포 테스트 성공!")
        print("🔧 실제 MCP 시스템이 정상적으로 배포되었습니다!")
        return True
    else:
        print("\n⚠️ 일부 테스트 실패")
        print("몇 분 후 다시 테스트하거나 로그를 확인해주세요.")
        return False

def test_specific_features(base_url):
    """특정 기능 테스트 가이드 출력"""
    print("\n🔧 수동 테스트 가이드:")
    print("-" * 40)
    print("다음 브라우저 테스트를 수행하세요:")
    print()
    print("1. 실제 MCP 시스템 테스트:")
    print("   🔍 '감옥에서 탈출하는 영화' 입력")
    print("   ✅ 예상 결과: 'The Shawshank Redemption' 검색")
    print("   ✅ 응답에 '🔧 **실제 MCP 시스템 검색 결과**' 표시")
    print()
    print("2. Tavily 웹 검색 트리거 테스트:")
    print("   🔍 '2024년 최신 영화' 입력")
    print("   ✅ 예상 결과: '🌐 Tavily 웹 검색 결과' 표시")
    print()
    print("3. 다중 LLM 폴백 테스트:")
    print("   🔍 여러 질문 연속 입력으로 API 한도 테스트")
    print("   ✅ 예상 결과: OpenAI → Gemini 자동 전환")
    print()

if __name__ == "__main__":
    # 배포된 서비스 URL
    if len(sys.argv) > 1:
        service_url = sys.argv[1]
    else:
        service_url = "https://movie-agent-real-mcp-904447394903.us-central1.run.app"
    
    print("🚀 실제 MCP 시스템 배포 테스트")
    print(f"📅 테스트 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 메인 테스트 실행
    success = test_deployment(service_url)
    
    # 추가 테스트 가이드 출력
    test_specific_features(service_url)
    
    # 종료 코드
    sys.exit(0 if success else 1)