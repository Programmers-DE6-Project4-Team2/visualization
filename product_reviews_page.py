import pandas as pd
import streamlit as st
from data_processor import (
    load_products_for_selection,
    load_product_reviews_with_sentiment,
    get_available_categories_and_platforms
)


def product_review_page(client):
    """상품별 리뷰 분석 페이지"""

    st.title("📊 상품별 리뷰 분석")
    st.markdown("---")

    # 1. 먼저 사용 가능한 카테고리와 플랫폼 목록 로드
    with st.spinner("카테고리 및 플랫폼 정보 로딩 중..."):
        available_categories, available_platforms = get_available_categories_and_platforms(_client=client)

    if not available_categories or not available_platforms:
        st.error("카테고리 또는 플랫폼 정보를 불러올 수 없습니다.")
        st.info("dim_category 및 dim_platform 테이블을 확인해주세요.")
        return

    # 2. 사용자 필터 선택 인터페이스
    st.subheader("🎯 상품 검색 조건")
    st.info("**1단계**: 카테고리 선택 → **2단계**: 플랫폼 선택 → **3단계**: 조건에 맞는 리뷰 수 많은 상품 표시")

    col1, col2 = st.columns(2)

    with col1:
        # 카테고리 필터 (dim_category의 standard_category 사용)
        selected_categories = st.multiselect(
            "카테고리 선택 (표준 카테고리)",
            options=available_categories,
            default=available_categories[:3] if len(available_categories) >= 3 else available_categories,
            help="dim_category 테이블의 standard_category 기준"
        )

    with col2:
        # 플랫폼 필터 (dim_platform의 platform 사용)
        selected_platforms = st.multiselect(
            "플랫폼 선택",
            options=available_platforms,
            default=available_platforms,
            help="dim_platform 테이블의 platform 기준"
        )

    # 3. 선택된 조건이 있을 때만 상품 데이터 로드
    if not selected_categories or not selected_platforms:
        st.warning("⚠️ 카테고리와 플랫폼을 모두 선택해주세요.")
        return

    # 4. 선택된 조건에 따라 상품 데이터 로드
    product_limit = 100
    product_review_limit = 500

    with st.spinner("선택된 조건에 맞는 상품 데이터 로딩 중..."):
        products_df = load_products_for_selection(
            _client=client,
            categories=selected_categories,
            platforms=selected_platforms,
            limit=product_limit
        )

    if products_df.empty:
        st.warning("선택한 조건에 맞는 상품이 없습니다. 다른 조건을 선택해보세요.")
        st.info("카테고리와 플랫폼 조합을 확인하거나 더 넓은 범위로 선택해보시기 바랍니다.")
        return

    # 5. 조건에 맞는 상품 수 표시
    st.success(f"✅ 선택된 조건에 맞는 상품: **{len(products_df)}개** (리뷰 수 많은 순)")

    # 6. 상품 선택 드롭다운
    st.subheader("📦 분석할 상품 선택")

    # 상품 옵션 생성 (상위 30개만 표시)
    product_options = {}
    display_products = products_df.head(30)

    for _, product in display_products.iterrows():
        # 표준 카테고리도 함께 표시
        display_name = (f"{product['name'][:50]}... | "
                        f"{product['brand']} | "
                        f"⭐{product['rating']:.1f} "
                        f"({product['review_count']}개) | "
                        f"{product['standard_category']} | "
                        f"{product['platform']}")
        product_options[display_name] = product['product_id']

    selected_display = st.selectbox(
        "분석할 상품을 선택하세요",
        ["선택하세요"] + list(product_options.keys()),
        help="리뷰 수가 많은 순서로 정렬되어 있습니다."
    )

    if selected_display == "선택하세요":
        st.info("👆 위에서 상품을 선택해주세요.")
        return

    # 7. 선택된 상품 정보 표시
    selected_product_id = product_options[selected_display]
    selected_product = products_df[
        products_df['product_id'] == selected_product_id
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

    # 상품 세부 정보
    st.markdown(f"**상품명**: {selected_product['name']}")
    st.markdown(f"**브랜드**: {selected_product['brand']}")
    st.markdown(f"**표준 카테고리**: {selected_product['standard_category']}")
    st.markdown(f"**원본 카테고리**: {selected_product['original_category']}")

    if 'platform_description' in selected_product and pd.notna(selected_product['platform_description']):
        st.markdown(f"**플랫폼 설명**: {selected_product['platform_description']}")

    st.markdown("---")

    # 8. 리뷰 데이터 로드 및 분석 (기존 코드와 동일)
    with st.spinner("리뷰 데이터 분석 중..."):
        reviews_df = load_product_reviews_with_sentiment(
            _client=client,
            product_id=selected_product_id,
            limit=product_review_limit
        )

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

    # 감성별 리뷰 샘플 (기존 코드와 동일)
    st.markdown("### 💬 리뷰 샘플 보기")
    tab1, tab2, tab3 = st.tabs(["😊 긍정 리뷰", "😞 부정 리뷰", "😐 중립 리뷰"])

    with tab1:
        show_sentiment_samples(reviews_df, 'positive', '긍정')
    with tab2:
        show_sentiment_samples(reviews_df, 'negative', '부정')
    with tab3:
        show_sentiment_samples(reviews_df, 'neutral', '중립')


def show_sentiment_samples(reviews_df, sentiment_type, sentiment_name):
    """특정 감성의 리뷰 샘플 표시 (기존 코드와 동일)"""
    sentiment_reviews = reviews_df[reviews_df['sentiment'] == sentiment_type]

    if sentiment_reviews.empty:
        st.info(f"{sentiment_name} 리뷰가 없습니다.")
        return

    total_reviews = len(sentiment_reviews)
    if total_reviews == 1:
        st.info(f"{sentiment_name} 리뷰가 1개 있습니다.")
        sample_count = 1
    else:
        sample_count = st.slider(
            f"{sentiment_name} 리뷰 샘플 개수",
            min_value=1,
            max_value=min(15, total_reviews),
            value=min(10, total_reviews),
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

    # 감성별 배경색 설정
    bg_colors = {
        'positive': '#d1f2eb',
        'negative': '#fadbd8',
        'neutral': '#fef9e7'
    }

    for idx, review in samples.iterrows():
        # 리뷰 카드 표시
        st.markdown(f"""
        <div style="background-color: {bg_colors[sentiment_type]}; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-weight: bold;">⭐ {review['star']}점</span>
                <span style="color: #666; font-size: 0.9em;">{review['created_at'].strftime('%Y-%m-%d')}</span>
            </div>
            <div style="line-height: 1.6;">
                {review['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
