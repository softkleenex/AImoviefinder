"""
멀티 LLM 클라이언트 - OpenAI와 Gemini API 폴백 시스템
"""

import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

# API 클라이언트들
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()

class MultiLLMClient:
    """
    여러 LLM API를 순차적으로 시도하는 폴백 시스템
    1. OpenAI GPT-4o-mini (Primary)
    2. OpenAI GPT-4o-mini (Backup Key)
    3. Google Gemini Pro (Final Fallback)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_provider = None
        
        # API 키 설정
        self.openai_keys = [
            os.getenv('OPENAI_API_KEY'),
            os.getenv('OPENAI_API_KEY_BACKUP')
        ]
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # 클라이언트 초기화
        self.openai_clients = []
        for key in self.openai_keys:
            if key and OPENAI_AVAILABLE:
                try:
                    client = OpenAI(api_key=key)
                    self.openai_clients.append(client)
                except Exception as e:
                    self.logger.warning(f"OpenAI 클라이언트 초기화 실패: {e}")
        
        # Gemini 클라이언트 초기화
        if self.google_api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.google_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                self.logger.info("✅ Gemini 클라이언트 초기화 성공")
            except Exception as e:
                self.logger.warning(f"Gemini 클라이언트 초기화 실패: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None
        
        self.logger.info(f"사용 가능한 OpenAI 클라이언트: {len(self.openai_clients)}개")
        self.logger.info(f"Gemini 사용 가능: {'✅' if self.gemini_client else '❌'}")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        여러 LLM을 순차적으로 시도하여 응답 생성
        """
        
        # 1. OpenAI 클라이언트들 순차 시도
        for i, client in enumerate(self.openai_clients):
            try:
                self.logger.info(f"🤖 OpenAI 클라이언트 #{i+1} 시도 중...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                result = response.choices[0].message.content
                self.current_provider = f"OpenAI-{i+1}"
                self.logger.info(f"✅ OpenAI 클라이언트 #{i+1} 성공")
                return result
                
            except Exception as e:
                self.logger.warning(f"❌ OpenAI 클라이언트 #{i+1} 실패: {str(e)}")
                # Rate limit이나 quota 초과 시 잠시 대기
                if "rate_limit" in str(e).lower() or "quota" in str(e).lower():
                    self.logger.info("Rate limit 감지, 2초 대기 후 다음 시도...")
                    time.sleep(2)
                continue
        
        # 2. Gemini 폴백 시도
        if self.gemini_client:
            try:
                self.logger.info("🔷 Gemini 클라이언트 시도 중...")
                
                # OpenAI 메시지 형식을 Gemini 형식으로 변환
                gemini_prompt = self._convert_messages_to_gemini_format(messages)
                
                response = self.gemini_client.generate_content(
                    gemini_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                result = response.text
                self.current_provider = "Gemini"
                self.logger.info("✅ Gemini 클라이언트 성공")
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Gemini 클라이언트 실패: {str(e)}")
        
        # 3. 모든 API 실패 시 기본 응답
        self.current_provider = "Fallback"
        self.logger.error("🚨 모든 LLM API 실패, 기본 응답 반환")
        return "죄송합니다. 현재 AI 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> str:
        """
        OpenAI 메시지 형식을 Gemini용 단일 프롬프트로 변환
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def get_current_provider(self) -> str:
        """현재 사용 중인 LLM 제공자 반환"""
        return self.current_provider or "Unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 정보 반환"""
        return {
            "openai_clients_available": len(self.openai_clients),
            "gemini_available": self.gemini_client is not None,
            "current_provider": self.current_provider,
            "openai_installed": OPENAI_AVAILABLE,
            "gemini_installed": GEMINI_AVAILABLE
        }

# 전역 클라이언트 인스턴스
_global_llm_client = None

def get_llm_client() -> MultiLLMClient:
    """전역 LLM 클라이언트 인스턴스 반환"""
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = MultiLLMClient()
    return _global_llm_client

# 테스트 함수
def test_llm_fallback():
    """LLM 폴백 시스템 테스트"""
    print("=== LLM 폴백 시스템 테스트 ===")
    
    client = get_llm_client()
    print(f"상태: {client.get_status()}")
    
    # 테스트 메시지
    test_messages = [
        {"role": "system", "content": "당신은 영화 전문가입니다."},
        {"role": "user", "content": "액션 영화 추천해주세요."}
    ]
    
    try:
        response = client.chat_completion(test_messages)
        print(f"\n✅ 응답 성공 (제공자: {client.get_current_provider()})")
        print(f"응답: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_llm_fallback()