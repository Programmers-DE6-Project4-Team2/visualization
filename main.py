import streamlit as st
import pandas as pd


from data_processor import load_data, add_sentiment_labels
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
        page_title="📊 키워드별 빈도 + 긍정률 분석",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("📊 키워드별 빈도 + 긍정률 분석 대시보드")
    st.markdown("---")

    # ----------------------- 데이터 로드 -----------------------
    data_limit = st.sidebar.selectbox("데이터 개수", [1_000, 5_000, 10_000], index=1)
    with st.spinner("데이터를 로드하는 중..."):
        df = load_data(limit=data_limit)          # BigQuery → DataFrame
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


if __name__ == "__main__":
    main()
