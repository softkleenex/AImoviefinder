#!/usr/bin/env python3
"""
실제 MCP 클라이언트 - MCP 서버와 통신하는 클라이언트
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Dict, List, Any, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("real-mcp-client")

class RealMCPClient:
    """실제 MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, server_command: List[str] = None):
        self.server_command = server_command or ["python", "real_mcp_server_simple.py"]
        self.server_process = None
        self.request_id = 0
        
    async def start_server(self):
        """MCP 서버 프로세스 시작"""
        try:
            self.server_process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/Volumes/samsd/mcp_project"
            )
            logger.info("✅ MCP 서버 프로세스 시작됨")
            
            # 초기화
            await self.initialize()
            
        except Exception as e:
            logger.error(f"❌ MCP 서버 시작 실패: {e}")
            raise
    
    async def stop_server(self):
        """MCP 서버 프로세스 종료"""
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
            logger.info("🛑 MCP 서버 프로세스 종료됨")
    
    def _get_next_id(self) -> int:
        """다음 요청 ID 생성"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, method: str, params: Dict = None) -> Dict:
        """MCP 서버에 JSON-RPC 요청 전송"""
        if not self.server_process:
            raise RuntimeError("MCP 서버가 시작되지 않았습니다")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }
        
        # 요청 전송
        request_json = json.dumps(request) + "\n"
        self.server_process.stdin.write(request_json.encode())
        await self.server_process.stdin.drain()
        
        logger.debug(f"📤 요청 전송: {method}")
        
        # 응답 수신
        response_line = await self.server_process.stdout.readline()
        if not response_line:
            raise RuntimeError("서버로부터 응답을 받지 못했습니다")
        
        response = json.loads(response_line.decode().strip())
        logger.debug(f"📥 응답 수신: {response.get('id')}")
        
        if "error" in response:
            raise Exception(f"MCP 서버 오류: {response['error']}")
        
        return response.get("result", {})
    
    async def initialize(self):
        """MCP 서버 초기화"""
        try:
            result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "real-mcp-client",
                    "version": "1.0.0"
                }
            })
            logger.info("✅ MCP 서버 초기화 완료")
            return result
        except Exception as e:
            logger.error(f"❌ MCP 서버 초기화 실패: {e}")
            raise
    
    async def list_tools(self) -> List[Dict]:
        """사용 가능한 도구 목록 조회"""
        try:
            result = await self._send_request("tools/list")
            tools = result.get("tools", [])
            logger.info(f"📋 사용 가능한 도구: {[tool['name'] for tool in tools]}")
            return tools
        except Exception as e:
            logger.error(f"❌ 도구 목록 조회 실패: {e}")
            return []
    
    async def call_tool(self, name: str, arguments: Dict = None) -> Dict:
        """도구 호출"""
        try:
            result = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments or {}
            })
            logger.info(f"🔧 도구 '{name}' 호출 성공")
            return result
        except Exception as e:
            logger.error(f"❌ 도구 '{name}' 호출 실패: {e}")
            return {"error": str(e)}
    
    async def search_movies(self, **kwargs) -> Dict:
        """영화 검색 도구 호출"""
        return await self.call_tool("search_movies", kwargs)
    
    async def get_movie_details(self, movie_title: str) -> Dict:
        """영화 상세 정보 도구 호출"""
        return await self.call_tool("get_movie_details", {"movie_title": movie_title})

# 테스트 함수
async def test_real_mcp():
    """실제 MCP 클라이언트-서버 통신 테스트"""
    print("🧪 실제 MCP 시스템 테스트 시작...")
    
    client = RealMCPClient()
    
    try:
        # 서버 시작
        await client.start_server()
        
        # 도구 목록 조회
        tools = await client.list_tools()
        print(f"✅ 도구 목록: {[tool['name'] for tool in tools]}")
        
        # 영화 검색 테스트
        print("\n🔍 영화 검색 테스트...")
        search_result = await client.search_movies(
            keywords=["prison", "escape"],
            min_rating=8.0,
            max_results=3
        )
        
        if "content" in search_result:
            for content in search_result["content"]:
                if content.get("type") == "text":
                    result_data = json.loads(content["text"])
                    if result_data.get("success"):
                        print(f"✅ {result_data['count']}개 영화 발견:")
                        for i, movie in enumerate(result_data["movies"][:3], 1):
                            print(f"  {i}. {movie['title']} ({movie['year']}) ⭐{movie['rating']}")
                    else:
                        print(f"❌ 검색 실패: {result_data.get('message', result_data.get('error'))}")
                    break
        
        # 영화 상세 정보 테스트
        print("\n📽️ 영화 상세 정보 테스트...")
        details_result = await client.get_movie_details("The Shawshank Redemption")
        
        if "content" in details_result:
            for content in details_result["content"]:
                if content.get("type") == "text":
                    detail_data = json.loads(content["text"])
                    if detail_data.get("success"):
                        movie = detail_data["movie"]
                        print(f"✅ 영화 상세 정보:")
                        print(f"  제목: {movie['title']}")
                        print(f"  연도: {movie['year']}")
                        print(f"  평점: {movie['rating']}")
                        print(f"  장르: {movie['genre']}")
                        print(f"  감독: {movie['director']}")
                    else:
                        print(f"❌ 상세 정보 조회 실패: {detail_data.get('error')}")
                    break
        
        print("\n🎉 실제 MCP 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 서버 종료
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(test_real_mcp())