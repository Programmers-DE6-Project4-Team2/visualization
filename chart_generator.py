import plotly.express as px


def create_bubble_chart(keyword_df):
    """키워드별 빈도 + 긍정률 버블 차트"""
    fig = px.scatter(
        keyword_df,
        x='frequency',
        y='positive_rate',
        size='review_count',
        color='avg_rating',
        hover_name='keyword',
        hover_data={
            'frequency': True,
            'positive_rate': ':.1f',
            'review_count': True,
            'avg_rating': ':.2f'
        },
        title="키워드별 빈도 vs 긍정률 (버블 크기: 리뷰 수, 색상: 평균 별점)",
        labels={
            'frequency': '키워드 빈도',
            'positive_rate': '긍정률 (%)',
            'avg_rating': '평균 별점'
        },
        color_continuous_scale='RdYlGn'
    )

    fig.update_layout(
        width=800,
        height=600,
        showlegend=True
    )

    return fig


def create_top_keywords_chart(keyword_df, top_n=20):
    """상위 키워드 빈도 차트"""
    top_keywords = keyword_df.head(top_n)

    fig = px.bar(
        top_keywords,
        x='frequency',
        y='keyword',
        orientation='h',
        color='positive_rate',
        color_continuous_scale='RdYlGn',
        title=f"상위 {top_n}개 키워드 빈도",
        labels={
            'frequency': '빈도',
            'keyword': '키워드',
            'positive_rate': '긍정률 (%)'
        }
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=600
    )

    return fig


def create_sentiment_distribution_chart(keyword_df):
    """긍정률 분포 히스토그램"""
    fig = px.histogram(
        keyword_df,
        x='positive_rate',
        nbins=20,
        title="키워드별 긍정률 분포",
        labels={
            'positive_rate': '긍정률 (%)',
            'count': '키워드 수'
        }
    )

    fig.add_vline(
        x=keyword_df['positive_rate'].mean(),
        line_dash="dash",
        line_color="red",
        annotation_text=f"평균: {keyword_df['positive_rate'].mean():.1f}%"
    )

    return fig


def create_correlation_matrix(keyword_df):
    """상관관계 매트릭스"""
    corr_cols = ['frequency', 'positive_rate', 'avg_rating', 'review_count']
    corr_matrix = keyword_df[corr_cols].corr()

    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="키워드 지표 간 상관관계",
        color_continuous_scale='RdBu'
    )

    return fig