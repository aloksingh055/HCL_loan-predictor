import plotly.graph_objects as go


def risk_gauge(probability: float, is_high_risk: bool):
    """Default probability ko 0-100% gauge mein dikhata hai."""
    color = "#d62728" if is_high_risk else "#2ca02c"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": "%"},
            title={"text": "Default Probability"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
    return fig