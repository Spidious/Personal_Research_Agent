"""
Phase 1 — static pipeline (no agentic loop yet).

Flow:
  1. Load topic + sources from sources.yaml
  2. Fetch each source
  3. Summarize each item with the workhorse model (Haiku)
  4. Format a digest
  5. Send via Resend

The agent contract from §5:
  agent(topic, candidate_items, user_profile) -> briefing
Prompts NEVER contain topic-specific text — topic context is passed as data.
"""
import html as html_lib
from dataclasses import dataclass

import yaml

from ..config import settings
from ..services import fetcher, llm, mailer

SUMMARIZE_SYSTEM = (
    "You are a research assistant. Given an article's title and content, "
    "write a 2–3 sentence summary that captures the key finding or announcement. "
    "Be factual and concise. Do not add opinion."
)


@dataclass
class TopicConfig:
    name: str
    description: str
    sources: list[dict]


def load_topics() -> list[TopicConfig]:
    """Parse sources.yaml and return a typed list of topic configs."""
    with open(settings.sources_yaml_path) as f: # todo: Query DB instead of YAML
        data = yaml.safe_load(f)
    return [
        TopicConfig(
            name=t["name"],
            description=t.get("description", ""),
            sources=t.get("sources", []),
        )
        for t in data.get("topics", [])
    ]


def _summarize_item(title: str, content: str) -> str:
    """Call Claude Haiku to produce a 2–3 sentence factual summary of a single article."""
    plain_content = html_lib.unescape(content)[:3000]
    response = llm.create_message(
        model=settings.workhorse_model,
        system=SUMMARIZE_SYSTEM,
        messages=[
            {"role": "user", "content": f"Title: {title}\n\nContent:\n{plain_content}"}
        ],
        max_tokens=256,
        calling_function="pipeline.summarize_item",
    )
    return response.content[0].text.strip()


def _render_html(topic: TopicConfig, summaries: list[dict]) -> str:
    """Render the full HTML email body for one topic briefing."""
    items_html = ""
    for i, s in enumerate(summaries, 1):
        items_html += f"""
        <div style="margin-bottom:24px;">
          <p style="margin:0 0 4px;font-size:13px;color:#666;">#{i}</p>
          <a href="{s['url']}" style="font-size:16px;font-weight:600;color:#1a1a1a;text-decoration:none;">
            {html_lib.escape(s['title'])}
          </a>
          <p style="margin:8px 0 0;font-size:14px;color:#333;line-height:1.5;">{html_lib.escape(s['summary'])}</p>
        </div>
        """
    return f"""
    <html><body style="font-family:sans-serif;max-width:640px;margin:0 auto;padding:24px;">
      <h1 style="font-size:22px;margin-bottom:4px;">{html_lib.escape(topic.name)} Briefing</h1>
      <p style="color:#666;font-size:13px;margin-top:0;">{html_lib.escape(topic.description)}</p>
      <hr style="margin:16px 0;">
      {items_html}
      <p style="font-size:12px;color:#999;margin-top:32px;">
        Powered by Personal Research Agent
      </p>
    </body></html>
    """


def run_pipeline(*, to_email: str, topic_name: str | None = None) -> list[str]:
    """
    Generate and send email topics
    Run the Phase 1 pipeline for all (or one) topic.
    Returns list of Resend message IDs.
    """
    topics = load_topics()
    if topic_name:
        topics = [t for t in topics if t.name == topic_name]

    sent_ids = []
    # Loop through each topic
    for topic in topics:
        summaries = []
        seen_urls: set[str] = set()

        # Loop through each source in topic
        for src in topic.sources:
            items = fetcher.fetch_source(src["type"], src["url"])

            # Loop through each item in source
            for item in items:
                # Skip duplicate items
                if item.url in seen_urls:
                    continue # todo: Consider switching this to compare subjects rather than exact emails (i.e. 2 articles reporting the same thing)
                seen_urls.add(item.url)
                summary = _summarize_item(item.title, item.content)
                summaries.append({
                    "title": item.title,
                    "url": item.url,
                    "summary": summary,
                })

        if not summaries:
            continue

        # Send email to client
        html_body = _render_html(topic, summaries)
        msg_id = mailer.send_briefing(
            to=to_email,
            subject=f"{topic.name} Briefing",
            html=html_body,
        )
        sent_ids.append(msg_id)

    return sent_ids
