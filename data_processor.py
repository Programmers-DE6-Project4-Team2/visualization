import streamlit as st
import pandas as pd

from config import project_id, layer, review_table, get_bigquery_client


@st.cache_data
def load_data(limit=10000):
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
