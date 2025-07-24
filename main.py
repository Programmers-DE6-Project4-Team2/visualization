from datetime import datetime

import streamlit as st
import pandas as pd


from data_processor import load_reviews, load_products_for_selection, \
    load_product_reviews_with_sentiment, add_sentiment_labels
from keyword_analyzer import extract_keywords_batch, calculate_keyword_sentiment_streaming
from chart_generator import create_bubble_chart, create_top_keywords_chart, \
    create_sentiment_distribution_chart, create_correlation_matrix
from ui_components import create_keyword_filter_section, display_keyword_reviews, \
    render_review_cards, create_keyword_comparison_section, add_search_functionality


# 페이지 설정
st.set_page_config(
    page_title="리뷰 탐색 인터페이스",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 설정
st.sidebar.title("🔍 분석 설정")


def main():
    # ------------------- 페이지·사이드바 설정 -------------------
    st.set_page_config(
        page_title="📊 리뷰 데이터 분석 대시보드",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("📊 키워드별 빈도 + 긍정률 분석 대시보드")
    st.markdown("---")

    # 사이드바에 페이지 선택 추가
    st.sidebar.title("📋 메뉴")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["키워드 분석", "상품별 리뷰 분석"]  # 기존 + 새로운 페이지
    )

    if page == "키워드 분석":
        # ----------------------- 리뷰 데이터 로드 -----------------------
        data_limit = st.sidebar.selectbox("데이터 개수", [1_000, 5_000, 10_000], index=1)
        with st.spinner("데이터를 로드하는 중..."):
            df = load_reviews(limit=data_limit)          # BigQuery → DataFrame
            df = add_sentiment_labels(df)             # 별점 기반 라벨 추가

        st.success(f"총 {len(df):,}개의 리뷰 데이터를 로드했습니다.")

        # --------------- 플랫폼·카테고리 필터 ----------------------
        st.sidebar.subheader("🔧 필터 옵션")
        platforms = st.sidebar.multiselect(
            "플랫폼 선택",
            options=df["platform"].unique(),
            default=df["platform"].unique()
        )
        categories = st.sidebar.multiselect(
            "카테고리 선택",
            options=df["category"].unique(),
            default=df["category"].unique()
        )
        filtered_df = df[(df["platform"].isin(platforms)) & (df["category"].isin(categories))]
        if filtered_df.empty:
            st.warning("선택한 조건에 맞는 데이터가 없습니다.")
            return

        # ------------------ 키워드 분석 파이프라인 ------------------
        with st.spinner("키워드를 분석하는 중..."):
            keywords = extract_keywords_batch(
                filtered_df["content"],
                top_n=50,
                min_length=st.sidebar.slider("최소 키워드 길이", 2, 5, 2)
            )
            keyword_df = calculate_keyword_sentiment_streaming(
                filtered_df,
                keywords,
                chunk_size=1_000
            )
            keyword_df = keyword_df[
                keyword_df["review_count"] >= st.sidebar.slider("최소 리뷰 수", 1, 20, 5)
            ].reset_index(drop=True)

        # ---------------------- 주요 메트릭 ------------------------
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("분석된 키워드 수", len(keyword_df))
        col2.metric("평균 긍정률", f"{keyword_df['positive_rate'].mean():.1f}%")
        col3.metric("총 리뷰 수", f"{filtered_df.shape[0]:,}")
        col4.metric("평균 별점", f"{filtered_df['star'].mean():.2f}")

        st.markdown("---")

        # -------------------- 시각화 섹션 --------------------------
        st.subheader("🎯 키워드별 빈도 vs 긍정률")
        st.plotly_chart(create_bubble_chart(keyword_df), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 상위 키워드 빈도")
            st.plotly_chart(create_top_keywords_chart(keyword_df, top_n=20), use_container_width=True)
        with col2:
            st.subheader("📊 긍정률 분포")
            st.plotly_chart(create_sentiment_distribution_chart(keyword_df), use_container_width=True)

        st.subheader("🔗 지표 간 상관관계")
        st.plotly_chart(create_correlation_matrix(keyword_df), use_container_width=True)

        st.markdown("---")

        # --------------- 키워드→리뷰 리스트 기능 -------------------
        selected_keyword = create_keyword_filter_section(keyword_df, filtered_df)
        if selected_keyword:
            st.markdown("---")
            info = keyword_df[keyword_df["keyword"] == selected_keyword].iloc[0]
            st.markdown(
                f"### 🎯 '{selected_keyword}' 키워드 상세 분석\n"
                f"- 전체 빈도: {info['frequency']:,}회\n"
                f"- 리뷰 수: {info['review_count']:,}개\n"
                f"- 긍정률: {info['positive_rate']:.1f}%\n"
                f"- 평균 별점: {info['avg_rating']:.2f}/5"
            )

            reviews_to_show = display_keyword_reviews(filtered_df, selected_keyword)
            if reviews_to_show is not None and not reviews_to_show.empty:
                render_review_cards(reviews_to_show, selected_keyword)
                st.markdown("### 💾 리뷰 데이터 다운로드")
                st.download_button(
                    label=f"📥 '{selected_keyword}' 리뷰 CSV 다운로드",
                    data=reviews_to_show.to_csv(index=False, encoding="utf-8-sig"),
                    file_name=f"reviews_{selected_keyword}_{pd.Timestamp.now():%Y%m%d_%H%M%S}.csv",
                    mime="text/csv"
                )

        st.markdown("---")
        create_keyword_comparison_section(keyword_df, filtered_df)
        add_search_functionality(filtered_df)

    elif page == "상품별 리뷰 분석":
        product_review_page()


def product_review_page():
    """상품별 리뷰 분석 페이지"""
    st.title("🛍️ 상품별 리뷰 분석")
    st.markdown("상품을 선택하고 긍정/부정 리뷰 샘플을 확인해보세요.")
    st.markdown("---")

    # 상품 데이터 로드
    with st.spinner("상품 데이터 로딩 중..."):
        products_df = load_products_for_selection()

    if products_df.empty:
        st.error("상품 데이터를 불러올 수 없습니다.")
        return

    # 상품 선택 인터페이스
    st.subheader("🎯 상품 선택")

    col1, col2 = st.columns(2)

    with col1:
        # 카테고리 필터
        categories = st.multiselect(
            "카테고리 선택",
            options=products_df['category'].unique(),
            default=products_df['category'].unique()[:3]  # 처음 3개만 기본 선택
        )

    with col2:
        # 플랫폼 필터
        platforms = st.multiselect(
            "플랫폼 선택",
            options=products_df['platform'].unique(),
            default=products_df['platform'].unique()
        )

    # 필터 적용
    filtered_products = products_df[
        (products_df['category'].isin(categories)) &
        (products_df['platform'].isin(platforms))
        ]

    if filtered_products.empty:
        st.warning("선택한 조건에 맞는 상품이 없습니다.")
        return

    # 상품 선택 드롭다운
    product_options = {}
    for _, product in filtered_products.head(30).iterrows():  # 상위 30개만 표시
        display_name = f"{product['name'][:50]}... | {product['brand']} | ⭐{product['rating']:.1f} ({product['review_count']}개)"
        product_options[display_name] = product['product_id']

    selected_display = st.selectbox(
        "분석할 상품을 선택하세요",
        ["선택하세요"] + list(product_options.keys())
    )

    if selected_display == "선택하세요":
        st.info("👆 위에서 상품을 선택해주세요.")
        return

    # 선택된 상품 정보
    selected_product_id = product_options[selected_display]
    selected_product = filtered_products[
        filtered_products['product_id'] == selected_product_id
        ].iloc[0]

    # 상품 정보 카드
    st.markdown("### 📦 선택된 상품 정보")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("평점", f"⭐ {selected_product['rating']:.1f}")
    with col2:
        st.metric("리뷰 수", f"{selected_product['review_count']:,}개")
    with col3:
        st.metric("가격", f"₩{selected_product['price']:,}")
    with col4:
        st.metric("플랫폼", selected_product['platform'])

    st.markdown(f"**상품명**: {selected_product['name']}")
    st.markdown(f"**브랜드**: {selected_product['brand']} | **카테고리**: {selected_product['category']}")

    st.markdown("---")

    # 리뷰 데이터 로드
    with st.spinner("리뷰 데이터 분석 중..."):
        reviews_df = load_product_reviews_with_sentiment(selected_product_id)

    if reviews_df.empty:
        st.warning("이 상품에 대한 리뷰 데이터가 없습니다.")
        return

    # 감성 분석 결과
    sentiment_counts = reviews_df['sentiment'].value_counts()

    st.markdown("### 📊 리뷰 감성 분석")
    col1, col2, col3 = st.columns(3)

    with col1:
        positive_count = sentiment_counts.get('positive', 0)
        positive_rate = (positive_count / len(reviews_df)) * 100
        st.metric("😊 긍정 리뷰", f"{positive_count}개", f"{positive_rate:.1f}%")

    with col2:
        negative_count = sentiment_counts.get('negative', 0)
        negative_rate = (negative_count / len(reviews_df)) * 100
        st.metric("😞 부정 리뷰", f"{negative_count}개", f"{negative_rate:.1f}%")

    with col3:
        neutral_count = sentiment_counts.get('neutral', 0)
        neutral_rate = (neutral_count / len(reviews_df)) * 100
        st.metric("😐 중립 리뷰", f"{neutral_count}개", f"{neutral_rate:.1f}%")

    # 감성별 리뷰 샘플
    st.markdown("### 💬 리뷰 샘플 보기")

    tab1, tab2, tab3 = st.tabs(["😊 긍정 리뷰", "😞 부정 리뷰", "😐 중립 리뷰"])

    with tab1:
        show_sentiment_samples(reviews_df, 'positive', '긍정')

    with tab2:
        show_sentiment_samples(reviews_df, 'negative', '부정')

    with tab3:
        show_sentiment_samples(reviews_df, 'neutral', '중립')


def show_sentiment_samples(reviews_df, sentiment_type, sentiment_name):
    """특정 감성의 리뷰 샘플 표시"""
    sentiment_reviews = reviews_df[reviews_df['sentiment'] == sentiment_type]

    if sentiment_reviews.empty:
        st.info(f"{sentiment_name} 리뷰가 없습니다.")
        return

    total_reviews = len(sentiment_reviews)

    if total_reviews == 1:
        # 리뷰가 1개뿐이면 슬라이더 없이 바로 표시
        st.info(f"{sentiment_name} 리뷰가 1개 있습니다.")
        sample_count = 1
    else:
        # 리뷰가 2개 이상이면 슬라이더 표시
        sample_count = st.slider(
            f"{sentiment_name} 리뷰 샘플 개수",
            min_value=1,
            max_value=min(15, total_reviews),
            value=min(5, total_reviews),
            key=f"{sentiment_type}_count"
        )

    # 정렬 방식
    sort_by = st.selectbox(
        f"{sentiment_name} 리뷰 정렬",
        ["최신순", "오래된순", "별점 높은순", "별점 낮은순"],
        key=f"{sentiment_type}_sort"
    )

    # 정렬 적용
    if sort_by == "최신순":
        sorted_reviews = sentiment_reviews.sort_values('created_at', ascending=False)
    elif sort_by == "오래된순":
        sorted_reviews = sentiment_reviews.sort_values('created_at', ascending=True)
    elif sort_by == "별점 높은순":
        sorted_reviews = sentiment_reviews.sort_values('star', ascending=False)
    else:  # 별점 낮은순
        sorted_reviews = sentiment_reviews.sort_values('star', ascending=True)

    # 샘플 표시
    samples = sorted_reviews.head(sample_count)

    # 감성별 배경색
    bg_colors = {
        'positive': '#d1f2eb',
        'negative': '#fadbd8',
        'neutral': '#fef9e7'
    }

    for idx, review in samples.iterrows():
        # 리뷰 카드
        st.markdown(f"""
        <div style="
            background-color: {bg_colors[sentiment_type]}; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 10px 0;
            border-left: 4px solid {'#27ae60' if sentiment_type == 'positive' else '#e74c3c' if sentiment_type == 'negative' else '#f39c12'};
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <strong>⭐ {review['star']}/5</strong>
                <span style="color: #7f8c8d; font-size: 0.9em;">
                    {review['created_at'].strftime('%Y.%m.%d')}
                </span>
            </div>
            <div style="line-height: 1.5; color: #2c3e50;">
                {review['content'][:500]}{'...' if len(review['content']) > 500 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 다운로드 버튼
    if not samples.empty:
        csv_data = samples[['review_id', 'star', 'content', 'created_at']].to_csv(
            index=False, encoding='utf-8-sig'
        )
        st.download_button(
            f"📥 {sentiment_name} 리뷰 CSV 다운로드",
            data=csv_data,
            file_name=f"{sentiment_name}_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"{sentiment_type}_download"
        )

if __name__ == "__main__":
    main()
