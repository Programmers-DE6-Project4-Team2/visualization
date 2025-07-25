import streamlit as st
import pandas as pd

from config import project_id, layer, product_table, review_table, \
    get_bigquery_client, predicted_review_table


@st.cache_data
def load_reviews(limit=1000):
    """BigQuery에서 기본 리뷰 데이터 로드"""
    client = get_bigquery_client()

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
    df = client.query(query).to_dataframe()
    # 날짜 컬럼을 명시적으로 datetime으로 변환
    df['created_at'] = pd.to_datetime(df['created_at'])

    return df


@st.cache_data
def load_products_for_selection(limit=100):
    """상품 선택용 데이터 로드"""
    client = get_bigquery_client()
    query = f"""
    SELECT 
        product_id,
        name,
        brand,
        price,
        rating,
        review_count,
        category,
        platform
    FROM `{project_id}.{layer}.{product_table}`
    WHERE rating > 0 AND review_count > 0
    ORDER BY review_count DESC
    LIMIT {limit}
    """
    return client.query(query).to_dataframe()


@st.cache_data
def load_predicted_reviews(limit=1000):
    """BigQuery에서 predicted_reviews 데이터 로드"""
    client = get_bigquery_client()
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
    df = client.query(query).to_dataframe()
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df


@st.cache_data
def load_product_reviews_with_sentiment(product_id, limit=300):
    """선택된 상품의 predicted_reviews 데이터 로드"""
    client = get_bigquery_client()
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
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        # 기존 sentiment 컬럼을 pred_label로 대체
        df['sentiment'] = df['pred_label']
    return df
