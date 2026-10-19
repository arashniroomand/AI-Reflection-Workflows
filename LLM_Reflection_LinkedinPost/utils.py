"""UI helpers for the LinkedIn Reflection notebook.

These functions render the workflow outputs as colored, right-to-left (RTL)
HTML cards so the Persian posts are easy to read inside a Jupyter notebook.
Import them from the notebook and just call them.
"""

from html import escape
import json

from IPython.display import display, HTML


def render_results_html(results):
    """Render each topic as 3 colored cards: draft / feedback / final (RTL Farsi)."""

    style = """
    <style>
      .ln-wrap{
        font-family: Tahoma, 'Segoe UI', Vazirmatn, sans-serif;
        direction: rtl;
        max-width: 1000px;
        margin: 0 auto;
        color: #1f2937;
      }
      .ln-topic{
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
        padding: 14px 18px;
        border-radius: 14px;
        margin: 28px 0 14px 0;
        box-shadow: 0 6px 16px rgba(99,102,241,.25);
      }
      .ln-topic h2{ margin:0; font-size:19px; }
      .ln-topic .chip{
        display:inline-block; margin-top:6px; font-size:13px;
        background: rgba(255,255,255,.22); padding:3px 10px; border-radius:20px;
      }
      .ln-cards{ display:flex; gap:14px; align-items:stretch; flex-wrap:wrap; }
      .ln-card{
        flex:1 1 300px; min-width:260px;
        border-radius:14px; padding:14px 16px;
        box-shadow:0 4px 12px rgba(0,0,0,.08);
        border-right:6px solid;
      }
      .ln-card h3{ margin:0 0 10px 0; font-size:15px; }
      .ln-card .body{
        white-space:pre-wrap; font-size:14px; line-height:1.8;
        background:#fff; border-radius:8px; padding:10px 12px;
        border:1px solid rgba(0,0,0,.06);
      }
      /* draft = blue, feedback = amber, final = green */
      .ln-draft  { background:#eef4ff; border-color:#2563eb; }
      .ln-draft h3 { color:#1e40af; }
      .ln-feed   { background:#fff8ec; border-color:#d97706; }
      .ln-feed  h3 { color:#92400e; }
      .ln-final  { background:#ecfdf5; border-color:#059669; }
      .ln-final h3 { color:#065f46; }
    </style>
    """

    blocks = ""
    for r in results:
        blocks += f"""
        <div class="ln-topic">
          <h2>📌 {escape(r['topic'])}</h2>
          <span class="chip">لحن: {escape(r.get('tone','حرفه‌ای'))}</span>
        </div>
        <div class="ln-cards">
          <div class="ln-card ln-draft">
            <h3>📝 پیش‌نویس اول</h3>
            <div class="body">{escape(r['draft'])}</div>
          </div>
          <div class="ln-card ln-feed">
            <h3>🔍 بازخورد</h3>
            <div class="body">{escape(r['feedback'])}</div>
          </div>
          <div class="ln-card ln-final">
            <h3>✅ نسخه‌ی نهایی</h3>
            <div class="body">{escape(r['revised'])}</div>
          </div>
        </div>
        """

    display(HTML(style + f'<div class="ln-wrap">{blocks}</div>'))


def render_comparison_html(signals, fb_no, fb_yes):
    """Render the raw quality signals and two feedback cards (with/without signals)."""
    style = """
    <style>
      .cmp-wrap{
        font-family: Tahoma, 'Segoe UI', Vazirmatn, sans-serif;
        direction: rtl; max-width:1000px; margin:0 auto; color:#1f2937;
      }
      .cmp-signals{
        background:#f1f5f9; border:1px dashed #94a3b8; border-radius:10px;
        padding:10px 14px; margin:14px 0; font-size:14px;
      }
      .cmp-signals code{ background:#e2e8f0; padding:2px 6px; border-radius:6px; }
      .cmp-cards{ display:flex; gap:14px; flex-wrap:wrap; align-items:stretch; }
      .cmp-card{
        flex:1 1 400px; min-width:320px; border-radius:14px; padding:14px 16px;
        box-shadow:0 4px 12px rgba(0,0,0,.08); border-right:6px solid;
      }
      .cmp-card h3{ margin:0 0 10px 0; font-size:16px; }
      .cmp-card .body{
        white-space:pre-wrap; font-size:14px; line-height:1.9;
        background:#fff; border-radius:8px; padding:10px 12px;
        border:1px solid rgba(0,0,0,.06);
      }
      .cmp-vague { background:#fff8ec; border-color:#d97706; }
      .cmp-vague h3 { color:#92400e; }
      .cmp-exact { background:#eef4ff; border-color:#2563eb; }
      .cmp-exact h3 { color:#1e40af; }
    </style>
    """
    signals_pretty = escape(json.dumps(signals, ensure_ascii=False, indent=2))
    html = f"""
    <div class="cmp-wrap">
      <div class="cmp-signals">
        📊 سیگنال‌های خام بررسی خودکار:
        <pre style="margin:6px 0 0 0; white-space:pre-wrap;">{signals_pretty}</pre>
      </div>
      <div class="cmp-cards">
        <div class="cmp-card cmp-vague">
          <h3>🔁 بازخورد بدون سیگنال (نسخه‌ی Part 1)</h3>
          <div class="body">{escape(fb_no)}</div>
        </div>
        <div class="cmp-card cmp-exact">
          <h3>🎯 بازخورد با سیگنال (نسخه‌ی Part 2)</h3>
          <div class="body">{escape(fb_yes)}</div>
        </div>
      </div>
    </div>
    """
    display(HTML(style + html))


def render_finals_html(post_no, check_no, post_yes, check_yes):
    """Render the two final posts side by side, each with a pass/fail pill."""
    style = """
    <style>
      .fin-wrap{
        font-family: Tahoma,'Segoe UI',Vazirmatn,sans-serif;
        direction:rtl; max-width:1000px; margin:0 auto; color:#1f2937;
      }
      .fin-cards{ display:flex; gap:14px; flex-wrap:wrap; align-items:stretch; }
      .fin-card{
        flex:1 1 400px; min-width:320px; border-radius:14px; padding:14px 16px;
        box-shadow:0 4px 12px rgba(0,0,0,.08); border-right:6px solid;
      }
      .fin-card h3{ margin:0 0 10px 0; font-size:16px; }
      .fin-card .body{
        white-space:pre-wrap; font-size:14px; line-height:1.9;
        background:#fff; border-radius:8px; padding:10px 12px;
        border:1px solid rgba(0,0,0,.06);
      }
      .fin-card .pill{
        display:inline-block; margin-top:8px; font-size:12px;
        padding:3px 10px; border-radius:20px;
      }
      .fin-pass{ background:#ecfdf5; border-color:#059669; }
      .fin-pass h3{ color:#065f46; }
      .fin-pass .pill{ background:#059669; color:#fff; }
      .fin-vague{ background:#fff8ec; border-color:#d97706; }
      .fin-vague h3{ color:#92400e; }
      .fin-vague .pill{ background:#d97706; color:#fff; }
      .fin-fail .pill{ background:#dc2626; color:#fff; }
    </style>
    """
    def pill(chk):
        ok = chk["within_length_limit"] and chk["within_hashtag_range"]
        label = "✅ مطابق محدودیت" if ok else "❌ نقض محدودیت"
        cls = "fin-pass" if ok else "fin-fail"
        return f'<span class="pill {cls}">{label} — طول: {chk["length"]} | هشتگ: {chk["hashtag_count"]}</span>'

    html = f"""
    <div class="fin-wrap">
      <div class="fin-cards">
        <div class="fin-card fin-vague">
          <h3>🏁 نسخه‌ی نهایی — از بازخوردِ بدون سیگنال</h3>
          <div class="body">{escape(post_no)}</div>
          {pill(check_no)}
        </div>
        <div class="fin-card fin-pass">
          <h3>🏁 نسخه‌ی نهایی — از بازخوردِ با سیگنال</h3>
          <div class="body">{escape(post_yes)}</div>
          {pill(check_yes)}
        </div>
      </div>
    </div>
    """
    display(HTML(style + html))