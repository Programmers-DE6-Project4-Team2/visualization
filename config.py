import os
import streamlit as st
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

credential = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
project_id = os.getenv('GCP_PROJECT_ID')
layer = os.getenv('LAYER')
product_table = os.getenv('PRODUCT_TABLE')
review_table = os.getenv('REVIEW_TABLE')
predicted_review_table = os.getenv('PREDICTED_REVIEW_TABLE')


@st.cache_resource
def get_bigquery_client():
    """BigQuery 클라이언트 초기화 with 인증"""
    try:
        if credential and os.path.exists(credential):
            client = bigquery.Client.from_service_account_json(
                credential,
                project=project_id
            )
        else:
            # 방법 2: 기본 인증 (gcloud auth application-default login 사용)
            client = bigquery.Client(project=project_id)

        # 연결 테스트
        client.query("SELECT 1").result()
        st.success("✅ BigQuery 연결 성공!")
        return client

    except Exception as e:
        st.error(f"❌ BigQuery 연결 실패: {str(e)}")
        st.info("""
        **GCP 인증 설정 방법:**
        1. Service Account Key 파일 다운로드
        2. .env 파일에 경로 설정
        3. 또는 `gcloud auth application-default login` 실행
        """)
        return None
