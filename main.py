import os

import streamlit as st

from product_reviews_page import product_review_page
from keywords_view_page import keyword_analysis_page


def main():
    # 사이드바에 페이지 선택 추가
    st.sidebar.title("📋 메뉴")
    page = st.sidebar.selectbox(
        "페이지 선택",
        [
            "Superset Charts",
            "키워드 분석",
            "상품별 리뷰 분석"
        ]
    )

    if page == "Superset Charts":
        superset_url = os.getenv("SUPERSET_URL") + "?standalone=true"
        st.components.v1.iframe(superset_url, height=600, scrolling=True)

    elif page == "키워드 분석":
        st.set_page_config(
            page_title="📊 리뷰 데이터 분석 대시보드",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.title("📊 키워드별 빈도 + 긍정률 분석 대시보드")
        st.markdown("---")
        keyword_analysis_page()

    elif page == "상품별 리뷰 분석":
        product_review_page()

if __name__ == "__main__":
    main()
