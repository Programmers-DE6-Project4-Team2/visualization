import streamlit as st
import pandas as pd

from config import project_id, layer, product_table, review_table, \
    predicted_review_table


@st.cache_data
def load_reviews(_client, limit=1000):
    """BigQuery에서 기본 리뷰 데이터 로드"""

    query = f"""
        SELECT 
            review_id,
            product_id,
            content,
            star,
            category,
            platform,
            created_at
        FROM `{project_id}.{layer}.{review_table}`
        WHERE content IS NOT NULL and star > 0 
        LIMIT {limit}
        """
    df = _client.query(query).to_dataframe()
    # 날짜 컬럼을 명시적으로 datetime으로 변환
    df['created_at'] = pd.to_datetime(df['created_at'])

    return df


@st.cache_data
def load_predicted_reviews(_client, limit=1000):
    """BigQuery에서 predicted_reviews 데이터 로드"""
    query = f"""
    SELECT
        review_uid,
        review_id,
        product_id,
        content,
        star,
        true_label,
        pred_label,
        is_correct,
        category,
        platform,
        created_at,
        run_date
    FROM `{project_id}.{layer}.{predicted_review_table}`  # 테이블명 변경
    WHERE content IS NOT NULL and star > 0
    ORDER BY created_at DESC
    LIMIT {limit}
    """
    df = _client.query(query).to_dataframe()
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df


@st.cache_data
def get_available_categories_and_platforms(_client):
    """차원 테이블에서 사용 가능한 카테고리와 플랫폼 목록 조회"""

    # dim_category에서 standard_category 조회
    category_query = f"""
    SELECT DISTINCT standard_category
    FROM `{project_id}.{layer}.dim_category`
    WHERE standard_category IS NOT NULL
    ORDER BY standard_category
    """

    # dim_platform에서 platform 조회
    platform_query = f"""
    SELECT DISTINCT platform
    FROM `{project_id}.{layer}.dim_platform`
    WHERE platform IS NOT NULL
    ORDER BY platform
    """

    try:
        categories_df = _client.query(category_query).to_dataframe()
        platforms_df = _client.query(platform_query).to_dataframe()

        categories = categories_df['standard_category'].tolist()
        platforms = platforms_df['platform'].tolist()

        return categories, platforms
    except Exception as e:
        st.error(f"카테고리/플랫폼 데이터 조회 실패: {str(e)}")
        return [], []


@st.cache_data
def load_products_for_selection(_client, categories=None, platforms=None, limit=100):
    """상품 선택용 데이터 로드 - 차원 테이블 조인 및 필터 적용"""

    # WHERE 절 조건 구성
    where_conditions = ["p.product_id IS NOT NULL"]

    # 선택된 카테고리 필터 (standard_category -> original_category 매핑)
    if categories and len(categories) > 0:
        category_list = "', '".join(categories)
        where_conditions.append(f"dc.standard_category IN ('{category_list}')")

    # 선택된 플랫폼 필터
    if platforms and len(platforms) > 0:
        platform_list = "', '".join(platforms)
        where_conditions.append(f"dp.platform IN ('{platform_list}')")

    where_clause = " AND ".join(where_conditions)

    query = f"""
    WITH top_reviewed_products AS (
        SELECT
            product_id,
            COUNT(*) AS review_count_from_reviews
        FROM `{project_id}.{layer}.{predicted_review_table}`
        WHERE product_id IS NOT NULL
        GROUP BY product_id
        ORDER BY COUNT(*) DESC
    )
    SELECT
        p.product_id,
        p.name,
        p.brand,
        p.price,
        p.rating,
        p.review_count,
        p.category as original_category,  -- product 테이블의 original_category
        dc.standard_category,             -- 표준화된 카테고리
        p.platform,
        dp.description as platform_description,
        trp.review_count_from_reviews
    FROM `{project_id}.{layer}.{product_table}` p
    INNER JOIN top_reviewed_products trp
        ON p.product_id = trp.product_id
    LEFT JOIN `{project_id}.{layer}.dim_category` dc
        ON p.category = dc.original_category  -- original_category로 매핑
        AND p.platform = dc.platform         -- platform도 고려
    LEFT JOIN `{project_id}.{layer}.dim_platform` dp
        ON p.platform = dp.platform
    WHERE {where_clause}
    ORDER BY trp.review_count_from_reviews DESC
    LIMIT {limit}
    """

    try:
        return _client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"상품 데이터 조회 실패: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_product_reviews_with_sentiment(_client, product_id, limit=300):
    """선택된 상품의 predicted_reviews 데이터 로드"""
    query = f"""
    SELECT
        review_id,
        content,
        star,
        pred_label,
        true_label,
        is_correct,
        created_at,
        platform
    FROM `{project_id}.{layer}.{predicted_review_table}`
    WHERE product_id = '{product_id}'
        AND content IS NOT NULL
        AND star > 0
    ORDER BY created_at DESC
    LIMIT {limit}
    """

    df = _client.query(query).to_dataframe()
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        # 기존 sentiment 컬럼을 pred_label로 대체
        df['sentiment'] = df['pred_label']

    return df
