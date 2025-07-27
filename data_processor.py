import streamlit as st
import pandas as pd

from config import project_id, layer, product_table, review_table, \
    get_bigquery_client, predicted_review_table


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
def load_products_for_selection(_client, limit=100):
    """상품 선택용 데이터 로드"""
    query = f"""
    WITH top_reviewed_products AS (
        SELECT 
            product_id,
            COUNT(*) AS review_count_from_reviews
        FROM `{project_id}.{layer}.{predicted_review_table}`
        WHERE product_id IS NOT NULL
        GROUP BY product_id
        ORDER BY COUNT(*) DESC
        LIMIT {limit}
    )
    SELECT
        p.product_id,
        p.name,
        p.brand,
        p.price,
        p.rating,
        p.review_count,
        p.category,
        p.platform,
        trp.review_count_from_reviews  -- 실제 리뷰 개수도 함께 조회
    FROM `{project_id}.{layer}.{product_table}` p
    INNER JOIN top_reviewed_products trp
    ON p.product_id = trp.product_id
    ORDER BY trp.review_count_from_reviews DESC
    """
    return _client.query(query).to_dataframe()


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
    FROM `{project_id}.{layer}.{predicted_review_table}`  # 테이블명 변경
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
