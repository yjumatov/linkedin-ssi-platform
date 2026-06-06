"""Email reporting service: daily and weekly SSI summary reports."""
from __future__ import annotations

import textwrap
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from jinja2 import Environment, DictLoader

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.analytics import AnalyticsResponse

logger = get_logger(__name__)


_DAILY_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 20px; }
  .card { background: white; border-radius: 12px; padding: 24px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  .score-big { font-size: 64px; font-weight: 700; color: #0077b5; text-align: center; margin: 8px 0; }
  .score-label { font-size: 14px; color: #64748b; text-align: center; margin-bottom: 24px; }
  .components { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .comp { background: #f1f5f9; border-radius: 8px; padding: 12px; }
  .comp-score { font-size: 28px; font-weight: 700; color: #1e293b; }
  .comp-name { font-size: 12px; color: #64748b; margin-top: 4px; }
  .delta-up { color: #16a34a; font-weight: 600; }
  .delta-down { color: #dc2626; font-weight: 600; }
  .delta-neutral { color: #64748b; }
  .rec { border-left: 4px solid; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0; }
  .rec-high { border-color: #dc2626; background: #fef2f2; }
  .rec-medium { border-color: #f59e0b; background: #fffbeb; }
  .rec-low { border-color: #16a34a; background: #f0fdf4; }
  h1 { color: #0f172a; } h2 { color: #1e293b; font-size: 18px; }
  .footer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px; }
</style>
</head>
<body>
<div style="max-width:600px;margin:0 auto">
  <h1>📊 LinkedIn SSI Daily Report — {{ report_date }}</h1>

  <div class="card">
    <div class="score-big">{{ "%.0f"|format(analytics.total.current) }}</div>
    <div class="score-label">Total SSI Score (out of 100)</div>
    <div class="components">
      {% for name, label, comp in components %}
      <div class="comp">
        <div class="comp-score">{{ "%.0f"|format(comp.current) }}<span style="font-size:14px;color:#94a3b8">/25</span></div>
        <div class="comp-name">{{ label }}</div>
        {% if comp.delta_1d is not none %}
          <div class="{% if comp.delta_1d > 0 %}delta-up{% elif comp.delta_1d < 0 %}delta-down{% else %}delta-neutral{% endif %}">
            {% if comp.delta_1d > 0 %}+{% endif %}{{ "%.1f"|format(comp.delta_1d) }} today
          </div>
        {% endif %}
      </div>
      {% endfor %}
    </div>
  </div>

  {% if analytics.total.delta_7d is not none %}
  <div class="card">
    <h2>📈 Weekly Change</h2>
    <p>
      Your SSI changed
      <strong class="{% if analytics.total.delta_7d >= 0 %}delta-up{% else %}delta-down{% endif %}">
        {% if analytics.total.delta_7d >= 0 %}+{% endif %}{{ "%.1f"|format(analytics.total.delta_7d) }} points
      </strong>
      over the past 7 days.
      Current trend: <strong>{{ analytics.total.trend }}</strong>
      {% if analytics.total.velocity %}({{ "%.1f"|format(analytics.total.velocity) }} pts/week){% endif %}.
    </p>
    {% for insight in analytics.insights %}
    <p style="color:#475569;font-size:14px">• {{ insight }}</p>
    {% endfor %}
  </div>
  {% endif %}

  {% if recommendations %}
  <div class="card">
    <h2>💡 Top Recommendations</h2>
    {% for rec in recommendations[:3] %}
    <div class="rec rec-{{ rec.priority }}">
      <strong>{{ rec.title }}</strong>
      <p style="margin:8px 0;font-size:14px;color:#475569">{{ rec.recommendation[:200] }}...</p>
      <small style="color:#64748b">Priority: {{ rec.priority.upper() }} | {{ rec.category.replace("_"," ").title() }}</small>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="footer">
    LinkedIn SSI Intelligence Platform • Generated {{ report_date }}<br>
    <a href="{{ dashboard_url }}" style="color:#0077b5">View Full Dashboard →</a>
  </div>
</div>
</body>
</html>
"""

_TEMPLATES = {"daily": _DAILY_HTML}
_jinja_env = Environment(loader=DictLoader(_TEMPLATES))


def _render_daily_email(
    analytics: AnalyticsResponse,
    recommendations: list[dict],
    report_date: date,
) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    comp_names = [
        ("professional_brand", "Professional Brand", analytics.professional_brand),
        ("find_right_people", "Find the Right People", analytics.find_right_people),
        ("engage_with_insights", "Engage with Insights", analytics.engage_with_insights),
        ("build_relationships", "Build Relationships", analytics.build_relationships),
    ]

    delta_symbol = ""
    if analytics.total.delta_1d is not None:
        delta_symbol = f" (+{analytics.total.delta_1d:.1f})" if analytics.total.delta_1d > 0 else f" ({analytics.total.delta_1d:.1f})"

    subject = (
        f"SSI Daily Report {report_date} — Score: {analytics.total.current:.0f}/100{delta_symbol}"
    )

    tmpl = _jinja_env.get_template("daily")
    html = tmpl.render(
        analytics=analytics,
        components=comp_names,
        recommendations=recommendations,
        report_date=report_date.strftime("%B %d, %Y"),
        dashboard_url=f"http://localhost:3000",
    )
    return subject, html


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.REPORT_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
            start_tls=settings.SMTP_USE_TLS,
        )
        await smtp.connect()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info("email_sent", to=to_email, subject=subject)
    except Exception as exc:
        logger.error("email_send_failed", to=to_email, error=str(exc))
        raise


async def send_daily_report(
    analytics: AnalyticsResponse,
    recommendations: list[dict],
    to_email: str,
    report_date: Optional[date] = None,
) -> None:
    rd = report_date or date.today()
    subject, html = _render_daily_email(analytics, recommendations, rd)
    await send_email(to_email, subject, html)
