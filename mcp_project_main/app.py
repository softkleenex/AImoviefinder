import streamlit as st
import os
from dotenv import load_dotenv
from agent_supervisor import AgentSupervisor

# Load environment variables
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="영화 추론 에이전트",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목과 설명
st.title("🎬 기억에 의존한 영화 추론 에이전트")
st.markdown("""
**🔗 MCP 기반 에이전트** | **🤖 OpenAI GPT-4o-mini** | **🎬 IMDb Top 1000**

단편적인 정보만으로도 원하는 영화를 찾아드립니다! 
영화 제목이 기억나지 않아도 괜찮습니다. 장르, 감독, 배우, 줄거리 등 기억나는 정보를 자유롭게 말씀해주세요.

🎯 **매 대화마다 Top 5 영화 추천을 받아보세요!**
""")

# 세션 상태 초기화
if 'supervisor' not in st.session_state:
    st.session_state.supervisor = AgentSupervisor()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'suggested_movies' not in st.session_state:
    st.session_state.suggested_movies = []

# 사이드바 - 사용법 안내 및 데이터셋 검색
with st.sidebar:
    st.header("💡 사용법")
    st.markdown("""
    **이런 정보를 알려주세요:**
    - 장르 (액션, 드라마, 코미디 등)
    - 감독 이름
    - 주연 배우
    - 줄거리의 일부
    - 개봉 연도
    - 평점 범위
    
    **예시 질문:**
    - "감옥에서 탈출하는 영화"
    - "크리스토퍼 놀란 감독 영화"
    - "톰 행크스가 나오는 드라마"
    - "평점 9점 이상인 액션 영화"
    """)
    
    st.markdown("---")
    
    # IMDb 데이터셋 직접 검색 기능
    st.header("🔍 IMDb 데이터셋 검색")
    st.markdown("**테스트용: 영화가 데이터베이스에 있는지 미리 확인해보세요**")
    
    # 검색 옵션들
    search_type = st.selectbox(
        "검색 방식",
        ["제목으로 검색", "감독으로 검색", "배우로 검색", "장르로 검색", "키워드로 검색"]
    )
    
    search_term = st.text_input("검색어를 입력하세요", key="dataset_search")
    
    if st.button("🔍 데이터셋 검색"):
        if search_term:
            try:
                # MovieDataManager 인스턴스 생성
                from movie_data_manager import MovieDataManager
                movie_manager = MovieDataManager()
                
                # 검색 실행
                if search_type == "제목으로 검색":
                    results = movie_manager.search_movies(keywords=[search_term])
                elif search_type == "감독으로 검색":
                    results = movie_manager.search_movies(director=search_term)
                elif search_type == "배우로 검색":
                    results = movie_manager.search_movies(actor=search_term)
                elif search_type == "장르로 검색":
                    results = movie_manager.search_movies(genre=search_term)
                else:  # 키워드로 검색
                    results = movie_manager.search_movies(keywords=[search_term])
                
                # 결과 표시
                if not results.empty:
                    st.success(f"✅ {len(results)}개 영화 발견!")
                    
                    for idx, movie in results.head(5).iterrows():
                        st.markdown(f"""
                        **{movie['Series_Title']}** ({movie['Released_Year']})
                        - 평점: ⭐{movie['IMDB_Rating']}
                        - 감독: {movie['Director']}
                        - 장르: {movie['Genre']}
                        """)
                else:
                    st.error("❌ 데이터베이스에서 해당 영화를 찾을 수 없습니다.")
                    st.info("💡 채팅에서 질문하시면 웹 검색으로 찾아드립니다!")
                    
            except Exception as e:
                st.error(f"검색 오류: {str(e)}")
        else:
            st.warning("검색어를 입력해주세요.")
    
    if st.button("🔄 대화 초기화"):
        st.session_state.supervisor = AgentSupervisor()
        st.session_state.messages = []
        st.session_state.suggested_movies = []
        st.success("🔗 MCP 세션이 초기화되었습니다!")
        st.rerun()

# 메인 채팅 인터페이스
st.header("💬 대화")

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("🎬 영화 제목이 기억나지 않아도 괜찮습니다! 장르, 감독, 배우, 줄거리 등 기억나는 정보를 자유롭게 말씀해주세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("영화를 찾고 있습니다..."):
            try:
                # 비동기 호출을 위한 함수
                import asyncio
                
                def run_async_request(supervisor, user_input):
                    """Streamlit에서 비동기 함수 실행"""
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(supervisor.process_request(user_input))
                    finally:
                        loop.close()
                
                response, suggested_movies = run_async_request(st.session_state.supervisor, prompt)
                st.session_state.suggested_movies = suggested_movies
                
                st.markdown(response)
                
                # 추천 영화가 있으면 표시
                if suggested_movies:
                    st.markdown("---")
                    
                    # 탑 5 영화를 시각적으로 먼저 표시
                    st.markdown("### 🏆 추천 영화 Top 5")
                    
                    # 5개 영화를 가로로 배치
                    cols = st.columns(5)
                    for i, movie in enumerate(suggested_movies[:5]):
                        with cols[i]:
                            # 포스터
                            if movie.get('Poster_Link'):
                                st.image(movie['Poster_Link'], width=120)
                            else:
                                st.image("https://via.placeholder.com/120x180?text=No+Image", width=120)
                            
                            # 제목 및 기본 정보
                            title = movie.get('Series_Title', 'Unknown')
                            st.markdown(f"**{title[:15]}{'...' if len(title) > 15 else ''}**")
                            rating = movie.get('IMDB_Rating', 'N/A')
                            st.markdown(f"⭐ {rating}")
                            year = movie.get('Released_Year', 'N/A')
                            st.markdown(f"📅 {year}")
                            
                    # 상세 정보는 확장 가능한 섹션으로
                    st.markdown("### 📝 상세 정보")
                    
                    for i, movie in enumerate(suggested_movies, 1):
                        title = movie.get('Series_Title', 'Unknown')
                        year = movie.get('Released_Year', 'N/A')
                        rating = movie.get('IMDB_Rating', 'N/A')
                        with st.expander(f"🎬 {i}. {title} ({year}) ⭐ {rating}"):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                if movie.get('Poster_Link'):
                                    st.image(movie['Poster_Link'], width=150)
                                else:
                                    st.image("https://via.placeholder.com/150x225?text=No+Image", width=150)
                            
                            with col2:
                                director = movie.get('Director', 'N/A')
                                st.markdown(f"**🎬 감독:** {director}")
                                genre = movie.get('Genre', 'N/A')
                                st.markdown(f"**🎭 장르:** {genre}")
                                star1 = movie.get('Star1', '')
                                star2 = movie.get('Star2', '')
                                stars = ', '.join([s for s in [star1, star2] if s])
                                st.markdown(f"**🎆 주연:** {stars if stars else 'N/A'}")
                                runtime = movie.get('Runtime', 'N/A')
                                st.markdown(f"**⏱️ 러닝타임:** {runtime}")
                                
                                # 메타스코어가 있으면 표시
                                if movie.get('Meta_score') and str(movie.get('Meta_score')) != 'nan':
                                    st.markdown(f"**📊 메타스코어:** {movie['Meta_score']}/100")
                                
                                # 줄거리는 따로 표시
                                st.markdown("**📜 줄거리:**")
                                overview = movie.get('Overview', '줄거리 정보가 없습니다.')
                                st.write(overview)
                else:
                    # 추천 영화가 없어도 기본 Top 5 표시
                    try:
                        # 기본 인기 영화 5개 표시
                        default_movies = st.session_state.supervisor.movie_manager.search_movies(top_n=5)
                        if not default_movies.empty:
                            st.markdown("---")
                            st.markdown("### 🏆 인기 영화 Top 5")
                            
                            cols = st.columns(5)
                            for i, (_, movie) in enumerate(default_movies.iterrows()):
                                if i >= 5:
                                    break
                                with cols[i]:
                                    if movie.get('Poster_Link'):
                                        st.image(movie['Poster_Link'], width=120)
                                    else:
                                        st.image("https://via.placeholder.com/120x180?text=No+Image", width=120)
                                    
                                    title = movie.get('Series_Title', 'Unknown')
                                    st.markdown(f"**{title[:15]}{'...' if len(title) > 15 else ''}**")
                                    rating = movie.get('IMDB_Rating', 'N/A')
                                    st.markdown(f"⭐ {rating}")
                                    year = movie.get('Released_Year', 'N/A')
                                    st.markdown(f"📅 {year}")
                    except Exception as e:
                        st.error(f"기본 영화 로드 오류: {e}")
                
            except Exception as e:
                error_message = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                st.error(error_message)
                response = error_message
    
    # AI 응답을 채팅 기록에 추가
    st.session_state.messages.append({"role": "assistant", "content": response})

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <h4>🎬 AI 영화 추론 에이전트</h4>
    <p><strong>🔗 MCP 기반</strong> | <strong>🤖 OpenAI GPT-4o-mini</strong> | <strong>📊 IMDb Top 1000</strong> | <strong>☁️ Google Cloud Run</strong></p>
    <p><em>Supervisor Architecture & Multi-turn Conversation Powered</em></p>
</div>
""", unsafe_allow_html=True)