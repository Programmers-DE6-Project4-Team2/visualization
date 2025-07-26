import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account


credential = st.secrets['GOOGLE_APPLICATION_CREDENTIALS']
project_id = st.secrets['GCP_PROJECT_ID']
layer = st.secrets['LAYER']
product_table = st.secrets['PRODUCT_TABLE']
review_table = st.secrets['REVIEW_TABLE']
predicted_review_table = st.secrets['PREDICTED_REVIEW_TABLE']


@st.cache_resource
def get_bigquery_client():
    """BigQuery 클라이언트 초기화 with secrets.toml"""
    try:
        # secrets.toml에서 GCP credentials 가져오기
        credentials_dict = dict(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])

        # Service Account credentials 생성
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )

        # BigQuery 클라이언트 생성
        client = bigquery.Client(
            credentials=credentials,
            project=credentials_dict["project_id"]
        )

        # 연결 테스트
        client.query("SELECT 1").result()
        st.success("✅ BigQuery 연결 성공!")
        return client

    except FileNotFoundError:
        st.error("❌ secrets.toml 파일을 찾을 수 없습니다.")
        st.info("""
        **secrets.toml 설정 방법:**
        1. `.streamlit/secrets.toml` 파일 생성
        2. GCP Service Account JSON을 TOML 형식으로 변환
        3. Streamlit Community Cloud에서는 앱 설정의 Secrets 섹션에 추가
        """)
        return None

    except KeyError as e:
        st.error(f"❌ secrets.toml에서 키를 찾을 수 없습니다: {str(e)}")
        st.info("""
        **필요한 secrets.toml 구조:**
        ```
        [connections.gcs]
        type = "service_account"
        project_id = "your-project-id"
        private_key_id = "your-private-key-id"
        ...
        ```
        """)
        return None

    except Exception as e:
        st.error(f"❌ BigQuery 연결 실패: {str(e)}")
        st.info("""
        **문제 해결 방법:**
        1. secrets.toml 파일이 올바른 위치(.streamlit/)에 있는지 확인
        2. TOML 형식이 올바른지 확인 (따옴표, 등호 사용)
        3. private_key에서 \\n이 올바르게 이스케이프되었는지 확인
        4. project_id가 정확한지 확인
        """)
        return None
