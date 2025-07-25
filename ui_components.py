import streamlit as st
import pandas as pd
import plotly.express as px


# 2. 키워드 필터 리뷰 리스트
def create_keyword_filter_section(keyword_df, df):
    """키워드 필터 섹션 생성"""
    st.subheader("🔍 키워드별 리뷰 탐색")

    # 상위 20개 키워드 선택 옵션
    top_keywords = keyword_df.head(20)['keyword'].tolist()

    # 키워드 선택 드롭다운
    selected_keyword = st.selectbox(
        "키워드를 선택하세요",
        options=["선택하세요"] + top_keywords,
        key="keyword_selector"
    )

    if selected_keyword != "선택하세요":
        return selected_keyword
    return None


def display_keyword_reviews(df, keyword, max_reviews=50):
    """선택된 키워드가 포함된 리뷰들을 출력"""

    # 키워드가 포함된 리뷰 필터링
    keyword_reviews = df[df['content'].str.contains(keyword, na=False, case=False)]

    if len(keyword_reviews) == 0:
        st.warning(f"'{keyword}' 키워드가 포함된 리뷰가 없습니다.")
        return

    # 키워드 통계 표시
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 리뷰 수", f"{len(keyword_reviews):,}")

    with col2:
        positive_rate = (df['pred_label'] == 'positive').mean() * 100
        st.metric("긍정률", f"{positive_rate:.1f}%")

    with col3:
        avg_rating = keyword_reviews['star'].mean()
        st.metric("평균 별점", f"{avg_rating:.2f}")

    with col4:
        # 플랫폼 분포
        platform_counts = keyword_reviews['platform'].nunique()
        st.metric("플랫폼 수", platform_counts)

    # 필터링 옵션
    st.markdown("### 📋 필터 및 정렬 옵션")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 감성 필터
        sentiment_filter = st.multiselect(
            "감성별 필터",
            options=['positive', 'negative', 'neutral'],
            default=['positive', 'negative', 'neutral'],
            key=f"sentiment_{keyword}"
        )

    with col2:
        # 별점 필터
        rating_range = st.slider(
            "별점 범위",
            min_value=1,
            max_value=5,
            value=(1, 5),
            key=f"rating_{keyword}"
        )

    with col3:
        # 정렬 기준
        sort_option = st.selectbox(
            "정렬 기준",
            ["최신순", "별점 높은순", "별점 낮은순", "긍정 리뷰 우선"],
            key=f"sort_{keyword}"
        )

    # 필터 적용
    filtered_reviews = keyword_reviews[
        (keyword_reviews['pred_label'].isin(sentiment_filter)) &
        (keyword_reviews['star'] >= rating_range[0]) &
        (keyword_reviews['star'] <= rating_range[1])
        ].copy()

    # 정렬 적용
    if sort_option == "최신순":
        filtered_reviews = filtered_reviews.sort_values('created_at', ascending=False)
    elif sort_option == "별점 높은순":
        filtered_reviews = filtered_reviews.sort_values('star', ascending=False)
    elif sort_option == "별점 낮은순":
        filtered_reviews = filtered_reviews.sort_values('star', ascending=True)
    elif sort_option == "긍정 리뷰 우선":
        filtered_reviews = filtered_reviews.sort_values(
            ['pred_label', 'star'],
            ascending=[False, False]
        )

    # 표시할 리뷰 수 제한
    display_reviews = filtered_reviews.head(max_reviews)

    st.markdown(f"### 📝 '{keyword}' 관련 리뷰 ({len(filtered_reviews):,}개 중 {len(display_reviews)}개 표시)")

    return display_reviews


def render_review_cards(reviews_df, keyword):
    """리뷰를 카드 형태로 렌더링"""

    for idx, review in reviews_df.iterrows():
        # 감성에 따른 색상 설정
        sentiment_colors = {
            'positive': '#d4edda',
            'negative': '#f8d7da',
            'neutral': '#fff3cd'
        }

        sentiment_icons = {
            'positive': '😊',
            'negative': '😞',
            'neutral': '😐'
        }

        bg_color = sentiment_colors.get(review['pred_label'], '#f8f9fa')
        icon = sentiment_icons.get(review['pred_label'], '🤔')

        # 키워드 하이라이트
        highlighted_content = review['content'].replace(
            keyword,
            f"**<mark style='background-color: yellow'>{keyword}</mark>**"
        )

        # 리뷰 카드 생성
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: {bg_color}; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                border-left: 4px solid #007bff;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>{icon} {review['pred_label'].title()}</strong>
                        <span style="margin-left: 15px;">⭐ {review['star']}/5</span>
                        <span style="margin-left: 15px;">📱 {review['platform']}</span>
                        <span style="margin-left: 15px;">🏷️ {review['category']}</span>
                    </div>
                    <small style="color: #666;">{review['created_at']}</small>
                </div>
                <div style="line-height: 1.6;">
                    {highlighted_content[:300]}{'...' if len(review['content']) > 300 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)


def create_keyword_comparison_section(keyword_df, df):
    """여러 키워드 비교 기능"""
    st.subheader("🔄 키워드 비교 분석")

    top_keywords = keyword_df.head(20)['keyword'].tolist()

    # 다중 키워드 선택
    selected_keywords = st.multiselect(
        "비교할 키워드들을 선택하세요 (최대 5개)",
        options=top_keywords,
        max_selections=5,
        key="keyword_comparison"
    )

    if len(selected_keywords) >= 2:
        comparison_data = []

        for keyword in selected_keywords:
            keyword_reviews = df[df['content'].str.contains(keyword, na=False)]

            comparison_data.append({
                'keyword': keyword,
                'review_count': len(keyword_reviews),
                'positive_rate': (keyword_reviews['pred_label'] == 'positive').mean() * 100,
                'avg_rating': keyword_reviews['star'].mean(),
                'recent_reviews': len(keyword_reviews[keyword_reviews['created_at'] >= '2024-01-01'])
            })

        comparison_df = pd.DataFrame(comparison_data)

        # 비교 테이블
        st.markdown("#### 📊 키워드 비교표")
        st.dataframe(
            comparison_df.style.format({
                'positive_rate': '{:.1f}%',
                'avg_rating': '{:.2f}',
                'review_count': '{:,}',
                'recent_reviews': '{:,}'
            }).background_gradient(subset=['positive_rate'], cmap='RdYlGn'),
            use_container_width=True
        )

        # 비교 차트
        fig = px.scatter(
            comparison_df,
            x='review_count',
            y='positive_rate',
            size='avg_rating',
            color='keyword',
            title="선택된 키워드들의 리뷰 수 vs 긍정률 비교",
            labels={
                'review_count': '리뷰 수',
                'positive_rate': '긍정률 (%)'
            }
        )

        st.plotly_chart(fig, use_container_width=True)


def add_search_functionality(df):
    """텍스트 검색 기능 추가"""
    st.subheader("🔍 리뷰 텍스트 검색")

    search_term = st.text_input(
        "검색어를 입력하세요",
        placeholder="예: 배송, 품질, 가격 등",
        key="review_search"
    )

    if search_term:
        search_results = df[df['content'].str.contains(search_term, na=False, case=False)]

        if len(search_results) > 0:
            st.success(f"'{search_term}' 검색 결과: {len(search_results):,}개")

            # 검색 결과 요약
            col1, col2, col3 = st.columns(3)

            with col1:
                positive_rate = (search_results['pred_label'] == 'positive').mean() * 100
                st.metric("긍정률", f"{positive_rate:.1f}%")

            with col2:
                avg_rating = search_results['star'].mean()
                st.metric("평균 별점", f"{avg_rating:.2f}")

            with col3:
                platform_dist = search_results['platform'].value_counts()
                top_platform = platform_dist.index[0]
                st.metric("주요 플랫폼", f"{top_platform}")

            # 검색 결과 리뷰 표시 (상위 10개)
            st.markdown("#### 검색 결과 리뷰")
            render_review_cards(search_results.head(10), search_term)

        else:
            st.warning(f"'{search_term}' 검색 결과가 없습니다.")