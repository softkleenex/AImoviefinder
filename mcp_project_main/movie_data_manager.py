import pandas as pd

class MovieDataManager:
    def __init__(self, csv_path='dataset/imdb_top_1000.csv'):
        self.df = pd.read_csv(csv_path)
        # 'Genre' 컬럼을 쉼표로 분리하여 리스트로 저장
        self.df['Genre_List'] = self.df['Genre'].apply(lambda x: [g.strip() for g in x.split(',')])

    def search_movies(self, keywords=None, genre=None, director=None, actor=None, min_rating=None, max_rating=None, top_n=10):
        results = self.df.copy()

        # 키워드 검색: 제목, 줄거리, 장르, 감독, 배우 필드에서 검색
        if keywords:
            keyword_pattern = '|'.join(keywords) # 여러 키워드를 OR 조건으로 검색
            results = results[
                results['Series_Title'].str.contains(keyword_pattern, case=False, na=False) |
                results['Overview'].str.contains(keyword_pattern, case=False, na=False) |
                results['Genre'].str.contains(keyword_pattern, case=False, na=False) |
                results['Director'].str.contains(keyword_pattern, case=False, na=False) |
                results['Star1'].str.contains(keyword_pattern, case=False, na=False) |
                results['Star2'].str.contains(keyword_pattern, case=False, na=False) |
                results['Star3'].str.contains(keyword_pattern, case=False, na=False) |
                results['Star4'].str.contains(keyword_pattern, case=False, na=False)
            ]

        if genre:
            results = results[results['Genre_List'].apply(lambda x: genre.lower() in [g.lower() for g in x])]
        if director:
            results = results[results['Director'].str.lower().str.contains(director.lower(), na=False)]
        if actor:
            actor_lower = actor.lower()
            results = results[
                results['Star1'].str.lower().str.contains(actor_lower, na=False) |
                results['Star2'].str.lower().str.contains(actor_lower, na=False) |
                results['Star3'].str.lower().str.contains(actor_lower, na=False) |
                results['Star4'].str.lower().str.contains(actor_lower, na=False)
            ]
        if min_rating:
            results = results[results['IMDB_Rating'] >= min_rating]
        if max_rating:
            results = results[results['IMDB_Rating'] <= max_rating]

        # 평점 기준으로 내림차순 정렬
        if not results.empty:
            results = results.sort_values(by='IMDB_Rating', ascending=False)
        else:
            return results # 결과가 없으면 빈 데이터프레임 반환

        return results.head(top_n)

if __name__ == '__main__':
    manager = MovieDataManager()

    print("--- 키워드 '탈옥'으로 영화 검색 (제목, 줄거리 포함) ---")
    prison_break_movies = manager.search_movies(keywords=['탈옥', '감옥'])
    print(prison_break_movies[['Series_Title', 'Overview', 'IMDB_Rating']])

    print("\n--- 감독 'Christopher Nolan'의 영화 검색 ---")
    nolan_movies = manager.search_movies(director='Christopher Nolan')
    print(nolan_movies[['Series_Title', 'Director', 'IMDB_Rating']])

    print("\n--- 배우 'Tom Hanks' 출연 영화 검색 ---")
    hanks_movies = manager.search_movies(actor='Tom Hanks')
    print(hanks_movies[['Series_Title', 'Star1', 'IMDB_Rating']])

    print("\n--- 장르 'Drama' 이면서 평점 9.0 이상인 영화 검색 ---")
    drama_high_rating_movies = manager.search_movies(genre='Drama', min_rating=9.0)
    print(drama_high_rating_movies[['Series_Title', 'Genre', 'IMDB_Rating']])
