from datetime import datetime

import streamlit as st

from data_processor import load_products_for_selection, \
    load_product_reviews_with_sentiment


def product_review_page():
    """상품별 리뷰 분석 페이지"""
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

    if 'is_correct' in reviews_df.columns:
        accuracy = reviews_df['is_correct'].mean() * 100
        st.metric("🎯 예측 정확도", f"{accuracy:.1f}%")

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
