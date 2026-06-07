from html import escape


def metric_card_html(label: str, value: object) -> str:
    return (
        '<div class="metric-card">'
        f'<div class="metric-card-label">{escape(str(label))}</div>'
        '<div class="metric-card-value" style="white-space:normal;overflow-wrap:anywhere;word-break:break-word">'
        f"{escape(str(value))}</div>"
        "</div>"
    )
