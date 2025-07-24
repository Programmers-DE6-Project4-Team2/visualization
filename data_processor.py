import streamlit as st
import pandas as pd

from config import project_id, layer, product_table, review_table, get_bigquery_client


@st.cache_data
def load_reviews(limit=10000):
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
def load_products_for_selection(limit=500):
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
def load_product_reviews_with_sentiment(product_id, limit=300):
    """선택된 상품의 리뷰 데이터 로드 및 감성 분류"""
    client = get_bigquery_client()
    query = f"""
    SELECT 
        review_id,
        content,
        star,
        created_at,
        platform
    FROM `{project_id}.{layer}.{review_table}`
    WHERE product_id = '{product_id}' 
    AND content IS NOT NULL 
    AND star > 0
    ORDER BY created_at DESC
    LIMIT {limit}
    """
    df = client.query(query).to_dataframe()

    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        # 간단한 감성 분류 (별점 기준)
        df['sentiment'] = df['star'].apply(
            lambda x: 'positive' if x >= 4 else 'negative' if x <= 2 else 'neutral'
        )
    return df


def add_sentiment_labels(df):
    """별점 기반으로 감성 라벨 생성"""

    def classify_sentiment(star):
        if star >= 4:
            return 'positive'
        elif star <= 2:
            return 'negative'
        else:
            return 'neutral'

    df['pred_label'] = df['star'].apply(classify_sentiment)
    df['true_label'] = df['pred_label']  # 별점 기반이므로 동일
    df['is_correct'] = True  # 별점 기반 분류이므로 항상 True

    return df
