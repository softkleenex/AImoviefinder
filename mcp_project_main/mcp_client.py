"""
MCP (Model Context Protocol) Client Implementation
영화 추론 에이전트용 MCP 클라이언트
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class MCPClient:
    """MCP 프로토콜을 구현하는 클라이언트"""
    
    def __init__(self):
        self.session_id = self._generate_session_id()
        self.protocol_version = "1.0"
        self.client_info = {
            "name": "movie-inference-agent",
            "version": "1.0.0"
        }
        self.capabilities = {
            "tools": True,
            "prompts": True,
            "resources": True
        }
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return f"mcp_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def initialize_session(self) -> Dict[str, Any]:
        """MCP 세션 초기화"""
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": self.protocol_version,
                "capabilities": self.capabilities,
                "clientInfo": self.client_info
            }
        }
        
        self.logger.info(f"MCP 세션 초기화: {self.session_id}")
        return init_message
    
    def create_tool_request(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구 실행 요청 생성"""
        tool_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        self.logger.info(f"도구 요청 생성: {tool_name}")
        return tool_request
    
    def create_context_message(self, conversation_history: List[Dict], 
                              current_input: str, available_tools: List[Dict]) -> Dict[str, Any]:
        """MCP 컨텍스트 메시지 생성"""
        context_message = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "prompts/get",
            "params": {
                "name": "movie_inference_context",
                "arguments": {
                    "conversation_history": conversation_history,
                    "current_user_input": current_input,
                    "available_tools": available_tools,
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        return context_message
    
    def process_tool_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """도구 응답 처리"""
        if "error" in response:
            self.logger.error(f"도구 실행 오류: {response['error']}")
            return {
                "success": False,
                "error": response["error"],
                "result": None
            }
        
        result = response.get("result", {})
        self.logger.info("도구 실행 성공")
        
        return {
            "success": True,
            "error": None,
            "result": result
        }
    
    def create_resource_request(self, resource_uri: str) -> Dict[str, Any]:
        """리소스 요청 생성"""
        resource_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            }
        }
        
        return resource_request
    
    def _get_next_id(self) -> int:
        """다음 요청 ID 생성"""
        if not hasattr(self, '_current_id'):
            self._current_id = 1
        else:
            self._current_id += 1
        return self._current_id
    
    def log_mcp_interaction(self, request_type: str, request: Dict[str, Any], 
                           response: Optional[Dict[str, Any]] = None):
        """MCP 상호작용 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "request_type": request_type,
            "request": request,
            "response": response
        }
        
        self.logger.info(f"MCP 상호작용: {request_type}")
        # 실제 구현에서는 파일이나 데이터베이스에 저장할 수 있음
        return log_entry


class MCPMovieToolHandler:
    """영화 검색 도구를 위한 MCP 핸들러"""
    
    def __init__(self, movie_manager):
        self.movie_manager = movie_manager
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구들 정의"""
        return [
            {
                "name": "search_movies",
                "description": "IMDb 영화 데이터베이스에서 영화를 검색합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "검색할 키워드 목록"
                        },
                        "genre": {
                            "type": "string", 
                            "description": "영화 장르"
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
                        "top_n": {
                            "type": "integer",
                            "description": "반환할 영화 수",
                            "default": 5
                        }
                    }
                }
            },
            {
                "name": "analyze_movie_context",
                "description": "사용자 입력을 분석하여 영화 검색 파라미터를 추출합니다",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "사용자 입력 텍스트"
                        },
                        "conversation_context": {
                            "type": "array",
                            "description": "이전 대화 컨텍스트"
                        }
                    },
                    "required": ["user_input"]
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구 실행"""
        if tool_name == "search_movies":
            return self._execute_search_movies(arguments)
        elif tool_name == "analyze_movie_context":
            return self._execute_analyze_context(arguments)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "content": []
            }
    
    def _execute_search_movies(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """영화 검색 실행"""
        try:
            # 기본값 설정
            search_params = {
                "top_n": arguments.get("top_n", 5)
            }
            
            # 선택적 파라미터 추가
            for param in ["keywords", "genre", "director", "actor", "min_rating", "max_rating"]:
                if param in arguments and arguments[param]:
                    search_params[param] = arguments[param]
            
            # 영화 검색 실행
            results = self.movie_manager.search_movies(**search_params)
            
            # 결과를 MCP 형식으로 변환
            movies = results.to_dict(orient='records') if not results.empty else []
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"검색 결과: {len(movies)}개 영화 발견"
                    },
                    {
                        "type": "resource",
                        "resource": {
                            "uri": "movie://search_results",
                            "name": "Movie Search Results",
                            "mimeType": "application/json"
                        },
                        "text": json.dumps(movies, ensure_ascii=False, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            return {
                "error": f"영화 검색 중 오류 발생: {str(e)}",
                "content": []
            }
    
    def _execute_analyze_context(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """컨텍스트 분석 실행"""
        user_input = arguments.get("user_input", "")
        
        # 간단한 키워드 추출 로직 (실제로는 더 정교한 NLP 처리)
        analysis = {
            "extracted_keywords": [],
            "detected_genre": None,
            "detected_director": None,
            "detected_actor": None,
            "confidence_score": 0.8
        }
        
        # 키워드 추출
        if "감옥" in user_input or "탈옥" in user_input:
            analysis["extracted_keywords"].extend(["prison", "escape"])
        if "우주" in user_input or "SF" in user_input:
            analysis["detected_genre"] = "Sci-Fi"
        if "크리스토퍼 놀란" in user_input:
            analysis["detected_director"] = "Christopher Nolan"
        
        return {
            "content": [
                {
                    "type": "text", 
                    "text": "사용자 입력 분석 완료"
                },
                {
                    "type": "resource",
                    "resource": {
                        "uri": "analysis://context_analysis",
                        "name": "Context Analysis Result",
                        "mimeType": "application/json"
                    },
                    "text": json.dumps(analysis, ensure_ascii=False, indent=2)
                }
            ]
        }