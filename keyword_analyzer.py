"""
한국어 텍스트 처리 관련 로직
1) 키워드 추출 함수  ─ extract_keywords_batch
2) 키워드별 감성·통계 집계 ─ calculate_keyword_sentiment_streaming
"""
import re
import streamlit as st
import pandas as pd

from konlpy.tag import Okt
from collections import Counter


@st.cache_data(show_spinner=False)
def extract_keywords_batch(
    text_series: pd.Series,
    *,
    top_n: int = 50,
    min_length: int = 2,
    batch_size: int = 1_000
) -> list[tuple[str, int]]:
    """
    대용량 한국어 리뷰에서 상위 N개 키워드(명사)와 빈도를 추출한다.

    Parameters
    ----------
    text_series : 리뷰 텍스트 Series
    top_n       : 반환할 키워드 개수
    min_length  : 키워드 최소 글자 수
    batch_size  : 형태소 분석 배치 크기

    Returns
    -------
    List[Tuple[keyword, frequency]]
    """
    okt = Okt()
    total_counter = Counter()

    for start in range(0, len(text_series), batch_size):
        batch_text = " ".join(text_series.iloc[start:start + batch_size].astype(str))
        batch_text = re.sub(r"[^\w\s]", " ", batch_text)          # 특수문자 제거
        nouns = okt.nouns(batch_text)                             # 명사 추출
        nouns = [n for n in nouns if len(n) >= min_length]        # 길이 필터
        total_counter.update(nouns)

    return total_counter.most_common(top_n)


@st.cache_data(show_spinner=False)
def calculate_keyword_sentiment_streaming(
    df: pd.DataFrame,
    keywords: list[tuple[str, int]],
    *,
    chunk_size: int = 1_000
) -> pd.DataFrame:
    """
    키워드별 리뷰 수·긍정률·평균 별점을 스트리밍(청크) 방식으로 계산한다.

    Parameters
    ----------
    df        : 리뷰 원본 DataFrame (content, star, pred_label 컬럼 포함)
    keywords  : extract_keywords_batch 결과 리스트
    chunk_size: 한 번에 처리할 리뷰 행 수

    Returns
    -------
    pd.DataFrame[
        keyword, frequency, review_count, positive_rate, avg_rating
    ]
    """
    # 결과 누적용 dict
    stats = {
        k: {
            "keyword": k,
            "frequency": f,
            "review_count": 0,
            "positive_cnt": 0,
            "rating_sum": 0.0
        }
        for k, f in keywords
    }

    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start + chunk_size]

        for kw in stats.keys():
            mask = chunk["content"].str.contains(kw, na=False)
            sub = chunk[mask]
            cnt = len(sub)
            if cnt == 0:
                continue

            stats[kw]["review_count"] += cnt
            stats[kw]["positive_cnt"] += (sub["pred_label"] == "positive").sum()
            stats[kw]["rating_sum"]   += sub["star"].sum()

    # 최종 DataFrame 변환
    rows = []
    for v in stats.values():
        if v["review_count"] == 0:      # 리뷰가 실제로 없으면 제외
            continue
        rows.append({
            "keyword":       v["keyword"],
            "frequency":     v["frequency"],
            "review_count":  v["review_count"],
            "positive_rate": v["positive_cnt"] / v["review_count"] * 100,
            "avg_rating":    v["rating_sum"] / v["review_count"]
        })

    return pd.DataFrame(rows)
