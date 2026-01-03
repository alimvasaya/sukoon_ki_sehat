# app.py
from flask import Flask, render_template_string, request, redirect, url_for
import math
import re
import sqlite3
import json
from urllib.parse import quote
from datetime import datetime, timedelta
from collections import Counter, defaultdict

app = Flask(__name__)

DB_PATH = "toto.db"

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Toto Gemma - Under-5 Screening</title>
  <style>
    :root {
      --bg: #0b1020;
      --surface: rgba(255,255,255,0.06);
      --card: rgba(255,255,255,0.08);
      --text: rgba(255,255,255,0.92);
      --muted: rgba(255,255,255,0.68);
      --border: rgba(255,255,255,0.14);
      --shadow: 0 10px 30px rgba(0,0,0,0.28);
      --accent: #7c6cff;
      --accent2: #20c997;
      --danger: #ff5c77;
      --warn: #ffcf5a;
      --ok: #2fd07c;
      --radius: 16px;
    }
    @media (prefers-color-scheme: light) {
      :root {
        --bg: #f6f7fb;
        --surface: rgba(0,0,0,0.03);
        --card: rgba(255,255,255,0.92);
        --text: rgba(10,14,28,0.92);
        --muted: rgba(10,14,28,0.62);
        --border: rgba(10,14,28,0.10);
        --shadow: 0 10px 30px rgba(10,14,28,0.10);
        --accent: #5b57ff;
        --accent2: #12b886;
        --danger: #e03131;
        --warn: #f59f00;
        --ok: #2f9e44;
      }
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(1200px 700px at 10% 0%, rgba(124,108,255,0.25), transparent 60%),
        radial-gradient(900px 500px at 90% 20%, rgba(32,201,151,0.20), transparent 55%),
        var(--bg);
    }

    a { color: inherit; }
    .container { max-width: 1100px; margin: 0 auto; padding: 18px 14px 28px; }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px;
      border: 1px solid var(--border);
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .brand { display: grid; gap: 2px; }
    .brand h1 { font-size: 1.05rem; margin: 0; letter-spacing: 0.2px; }
    .brand p { margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.3; }
    .badges { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
    .badge {
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      font-weight: 650;
      font-size: 0.88rem;
      white-space: nowrap;
    }
    .badge-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent2); box-shadow: 0 0 0 3px rgba(32,201,151,0.18); }

    .grid { display: grid; gap: 14px; margin-top: 14px; }
    @media (min-width: 980px) {
      .grid { grid-template-columns: 1.10fr 0.90fr; align-items: start; }
    }

    .card {
      border: 1px solid var(--border);
      background: var(--card);
      border-radius: var(--radius);
      padding: 14px;
      box-shadow: var(--shadow);
    }
    .card + .card { margin-top: 14px; }

    .card h2 { margin: 0 0 10px; font-size: 1.02rem; }
    .card h3 { margin: 0 0 10px; font-size: 0.98rem; }
    .muted { color: var(--muted); font-size: 0.95rem; }
    .hint { margin-top: 6px; color: var(--muted); font-size: 0.9rem; }
    .divider { height: 1px; background: var(--border); margin: 12px 0; }

    .result { position: relative; overflow: hidden; }
    .result::before {
      content: "";
      position: absolute;
      inset: -2px;
      background: radial-gradient(500px 250px at 15% 0%, rgba(124,108,255,0.35), transparent 60%);
      pointer-events: none;
      opacity: 0.6;
    }
    .result > * { position: relative; }

    .pill-row { display:flex; flex-wrap:wrap; gap: 8px; margin-bottom: 10px; }
    .pill {
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      font-weight: 700;
      font-size: 0.88rem;
    }
    .pill strong { font-weight: 800; }

    .danger { border-color: rgba(255,92,119,0.35); background: linear-gradient(180deg, rgba(255,92,119,0.16), rgba(255,255,255,0.06)); }
    .warn { border-color: rgba(255,207,90,0.35); background: linear-gradient(180deg, rgba(255,207,90,0.16), rgba(255,255,255,0.06)); }
    .ok { border-color: rgba(47,208,124,0.35); background: linear-gradient(180deg, rgba(47,208,124,0.16), rgba(255,255,255,0.06)); }

    form { margin: 0; }

    label { display:block; margin: 10px 0 6px; font-weight: 800; }
    .field label { line-height: 1.2; }
    /* Fix: align inputs when labels wrap (your screenshot issue) */
    .row3 { display: grid; grid-template-columns: 1fr; gap: 10px; align-items: end; }
    @media (min-width: 860px) { .row3 { grid-template-columns: 1fr 1fr 1fr; align-items: end; } }
    .row { display: grid; grid-template-columns: 1fr; gap: 10px; align-items: end; }
    @media (min-width: 640px) { .row { grid-template-columns: 1fr 1fr; } }

    input[type="number"], input[type="text"], input[type="tel"], select, textarea {
      width: 100%;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      outline: none;
      min-height: 46px;
      line-height: 1.2;
    }
    textarea { min-height: 132px; resize: vertical; }

    /* Fix: select dropdown/arrow + make the control consistent */
    select {
      appearance: none;
      padding-right: 44px;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 20px) 50%,
        calc(100% - 14px) 50%;
      background-size: 6px 6px, 6px 6px;
      background-repeat: no-repeat;
      background-clip: padding-box;
    }
    /* Best-effort for some browsers (not all allow styling options) */
    select option { color: #111; background: #fff; }
    @media (prefers-color-scheme: light) {
      select option { color: #111; background: #fff; }
    }

    input::placeholder, textarea::placeholder { color: rgba(255,255,255,0.45); }
    @media (prefers-color-scheme: light) { input::placeholder, textarea::placeholder { color: rgba(10,14,28,0.38); } }

    input:focus, select:focus, textarea:focus { border-color: rgba(124,108,255,0.65); box-shadow: 0 0 0 4px rgba(124,108,255,0.18); }

    .segmented {
      display: grid;
      grid-template-columns: 1fr 1fr;
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
      background: rgba(255,255,255,0.04);
      min-height: 46px;
      align-items: stretch;
    }
    .segmented input { position: absolute; opacity: 0; pointer-events: none; }
    .segmented label {
      margin: 0;
      padding: 10px 12px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      user-select: none;
      min-height: 46px;
      width: 100%;
    }
    .segmented label:hover { background: rgba(255,255,255,0.06); }
    .segmented input:focus-visible + label { outline: 3px solid rgba(124,108,255,0.45); outline-offset: -3px; }
    .segmented input:checked + label {
      background: rgba(124,108,255,0.20);
      border-left: 1px solid rgba(124,108,255,0.25);
      border-right: 1px solid rgba(124,108,255,0.25);
    }
    .segmented label:first-of-type { border-right: 1px solid var(--border); }

    .btn-row { display:flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
    .btn {
      padding: 12px 14px;
      border: 1px solid transparent;
      border-radius: 14px;
      font-weight: 900;
      cursor: pointer;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap: 10px;
      text-decoration:none;
      text-align:center;
      min-height: 44px;
      transition: transform 0.05s ease, filter 0.15s ease, background 0.15s ease;
      flex: 1 1 220px;
      user-select: none;
    }
    .btn:active { transform: translateY(1px); }
    .btn-primary { background: var(--accent); color: #fff; }
    .btn-secondary { background: rgba(255,255,255,0.08); border-color: var(--border); color: var(--text); }
    .btn-danger { background: rgba(255,92,119,0.18); border-color: rgba(255,92,119,0.35); color: var(--text); }
    .btn-whatsapp { background: #25D366; color: #fff; }
    .btn:focus-visible { outline: 3px solid rgba(124,108,255,0.55); outline-offset: 3px; }
    .btn svg { width: 18px; height: 18px; }

    .sticky-actions { position: sticky; bottom: 10px; margin-top: 14px; z-index: 3; }
    .hidden { display: none !important; }

    ul { margin: 8px 0 0 18px; }
    li { margin: 6px 0; }

    .table { width: 100%; border-collapse: collapse; }
    .table th, .table td { text-align: left; padding: 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
    .nowrap { white-space: nowrap; }
    .chip { display:inline-flex; align-items:center; gap:8px; padding: 6px 10px; border-radius: 999px; border:1px solid var(--border); background: rgba(255,255,255,0.06); font-weight: 800; font-size: 0.88rem; }

    .subgrid { display:grid; gap: 12px; }
    @media (min-width: 760px) { .subgrid { grid-template-columns: 1fr 1fr; } }

    .kpi {
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }
    .kpi .k {
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255,255,255,0.05);
      padding: 10px 12px;
    }
    .k .label { color: var(--muted); font-size: 0.85rem; font-weight: 800; }
    .k .val { font-size: 1.15rem; font-weight: 950; margin-top: 2px; }

    .msg { border: 1px solid rgba(255,207,90,0.35); background: rgba(255,207,90,0.12); border-radius: 14px; padding: 12px; }
  </style>
</head>
<body>
  {% macro selected(name, value, default_value='') -%}
    {% if form.get(name, default_value) == value %}selected{% endif %}
  {%- endmacro %}
  {% macro checked(name, value, default_value='No') -%}
    {% if form.get(name, default_value) == value %}checked{% endif %}
  {%- endmacro %}

  <div class="container">
    <div class="topbar">
      <div class="brand">
        <h1>Toto Gemma — Under-5 Screening</h1>
        <p>This tool is for screening and coaching. If danger signs are present, refer urgently.</p>
      </div>
      <div class="badges" aria-label="Status">
        <span class="badge"><span class="badge-dot" aria-hidden="true"></span>Offline-ready</span>
      </div>
    </div>

    {% if message %}
      <div class="card msg" style="margin-top:14px;">
        <strong>{{ message }}</strong>
      </div>
    {% endif %}

    <div class="grid">
      <main>
        {% if result %}
          <section class="card result {{ result.box_class }}" aria-label="Screening result">
            <div class="pill-row">
              <span class="pill"><strong>Risk</strong> {{ result.risk }}</span>
              <span class="pill"><strong>Most likely</strong> {{ result.top_condition }}</span>
              <span class="pill"><strong>Certainty</strong> {{ result.certainty }}%</span>
            </div>

            <h2>What to do now</h2>
            <ul>
              {% for s in result.actions %}
                <li>{{ s }}</li>
              {% endfor %}
            </ul>

            <div class="divider"></div>

            <h2>Coaching tips for caregiver</h2>
            <ul>
              {% for s in result.tips %}
                <li>{{ s }}</li>
              {% endfor %}
            </ul>

            <div class="divider"></div>

            <h2>Also consider</h2>
            <ul>
              {% for name, pct in result.alternatives %}
                <li>{{ name }} — {{ pct }}%</li>
              {% endfor %}
            </ul>

            <div class="btn-row" style="margin-top: 14px;">
              <a class="btn btn-secondary" href="#screen" aria-label="Go to screening form">Back to form</a>
            </div>
          </section>

          <section class="card" aria-label="Share via WhatsApp">
            <h2>Share via WhatsApp</h2>
            <p class="muted">This does not auto-send. It opens WhatsApp with a pre-filled summary. Review, then tap Send.</p>

            <label for="shareText">Message to share</label>
            <textarea id="shareText" readonly>{{ result.share_message }}</textarea>

            <div class="btn-row">
              <a class="btn btn-whatsapp" href="{{ result.wa_caregiver_url }}" target="_blank" rel="noopener">Share to caregiver</a>
              <a class="btn btn-whatsapp" href="{{ result.wa_supervisor_url }}" target="_blank" rel="noopener">Share to supervisor</a>
              <button class="btn btn-secondary" type="button" onclick="copyShareText()">Copy summary</button>
            </div>

            <p id="copyStatus" class="muted" style="margin-top:10px;"></p>
          </section>
        {% endif %}

        <section id="screen" class="card" aria-label="Under-5 screening form">
          <h2>Screening form</h2>
          <p class="muted">
            Answer the questions below. If you selected a patient, results will save to that patient’s history.
          </p>

          {% if selected_patient %}
            <div class="pill-row">
              <span class="pill"><strong>Patient</strong> {{ selected_patient.name }}</span>
              {% if selected_patient.village %}<span class="pill"><strong>Village</strong> {{ selected_patient.village }}</span>{% endif %}
              <span class="pill"><strong>Default age</strong> {{ selected_patient.age_group_label }}</span>
            </div>
          {% else %}
            <p class="muted">No patient selected (optional).</p>
          {% endif %}

          <form method="post" novalidate>
            <input type="hidden" name="action" value="run_screening">
            <input type="hidden" name="patient_id" value="{{ selected_patient.id if selected_patient else '' }}">

            <div class="row3">
              <div class="field">
                <label for="age_group">Age group</label>
                <select id="age_group" name="age_group" required>
                  <option value="0_2m" {{ 'selected' if default_age_group == '0_2m' else '' }}>0–2 months</option>
                  <option value="2_12m" {{ 'selected' if default_age_group == '2_12m' else '' }}>2–12 months</option>
                  <option value="1_5y" {{ 'selected' if default_age_group == '1_5y' else '' }}>1–5 years</option>
                </select>
              </div>

              <div class="field">
                <label for="wa_caregiver">Caregiver WhatsApp (optional)</label>
                <input id="wa_caregiver" type="tel" name="wa_caregiver" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_caregiver','') }}" placeholder="Digits only, include country code">
              </div>

              <div class="field">
                <label for="wa_supervisor">Supervisor WhatsApp (optional)</label>
                <input id="wa_supervisor" type="tel" name="wa_supervisor" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_supervisor','') }}" placeholder="Digits only, include country code">
              </div>
            </div>

            <div class="row">
              <div class="field">
                <label for="assessor">Assessor / CHW ID (for analytics)</label>
                <input id="assessor" type="text" name="assessor" value="{{ form.get('assessor', assessor_default) }}" placeholder="e.g., CHW-03">
              </div>

              <div class="field">
                <label>Include patient name/village in WhatsApp?</label>
                <div class="segmented" role="group" aria-label="Include patient identifiers">
                  <input id="id_no" type="radio" name="include_identifiers" value="No" {{ checked('include_identifiers','No','No') }}>
                  <label for="id_no">No</label>
                  <input id="id_yes" type="radio" name="include_identifiers" value="Yes" {{ checked('include_identifiers','Yes','No') }}>
                  <label for="id_yes">Yes</label>
                </div>
                <div class="hint">Default is No (privacy).</div>
              </div>
            </div>

            <div class="divider"></div>

            <div class="card warn" aria-label="Danger signs">
              <h3>Danger signs</h3>
              <p class="muted">If any are Yes, refer urgently.</p>

              <div class="row">
                <div class="field">
                  <label>Not able to drink/breastfeed?</label>
                  <div class="segmented" role="group" aria-label="Not able to drink or breastfeed">
                    <input id="ds_drink_no" type="radio" name="ds_drink" value="No" {{ checked('ds_drink','No','No') }}>
                    <label for="ds_drink_no">No</label>
                    <input id="ds_drink_yes" type="radio" name="ds_drink" value="Yes" {{ checked('ds_drink','Yes','No') }}>
                    <label for="ds_drink_yes">Yes</label>
                  </div>
                </div>

                <div class="field">
                  <label>Vomits everything?</label>
                  <div class="segmented" role="group" aria-label="Vomits everything">
                    <input id="ds_vomit_no" type="radio" name="ds_vomit" value="No" {{ checked('ds_vomit','No','No') }}>
                    <label for="ds_vomit_no">No</label>
                    <input id="ds_vomit_yes" type="radio" name="ds_vomit" value="Yes" {{ checked('ds_vomit','Yes','No') }}>
                    <label for="ds_vomit_yes">Yes</label>
                  </div>
                </div>

                <div class="field">
                  <label>Convulsions?</label>
                  <div class="segmented" role="group" aria-label="Convulsions">
                    <input id="ds_convulsions_no" type="radio" name="ds_convulsions" value="No" {{ checked('ds_convulsions','No','No') }}>
                    <label for="ds_convulsions_no">No</label>
                    <input id="ds_convulsions_yes" type="radio" name="ds_convulsions" value="Yes" {{ checked('ds_convulsions','Yes','No') }}>
                    <label for="ds_convulsions_yes">Yes</label>
                  </div>
                </div>

                <div class="field">
                  <label>Very sleepy/unconscious?</label>
                  <div class="segmented" role="group" aria-label="Very sleepy or unconscious">
                    <input id="ds_lethargy_no" type="radio" name="ds_lethargy" value="No" {{ checked('ds_lethargy','No','No') }}>
                    <label for="ds_lethargy_no">No</label>
                    <input id="ds_lethargy_yes" type="radio" name="ds_lethargy" value="Yes" {{ checked('ds_lethargy','Yes','No') }}>
                    <label for="ds_lethargy_yes">Yes</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>Main symptoms</h3>
            <div class="row">
              <div class="field">
                <label>Fever now or in last 2 days?</label>
                <div class="segmented" role="group" aria-label="Fever">
                  <input id="fever_no" type="radio" name="fever" value="No" {{ checked('fever','No','No') }}>
                  <label for="fever_no">No</label>
                  <input id="fever_yes" type="radio" name="fever" value="Yes" {{ checked('fever','Yes','No') }}>
                  <label for="fever_yes">Yes</label>
                </div>
              </div>

              <div class="field">
                <label>Cough or difficult breathing?</label>
                <div class="segmented" role="group" aria-label="Cough or difficult breathing">
                  <input id="cough_breath_no" type="radio" name="cough_breath" value="No" {{ checked('cough_breath','No','No') }}>
                  <label for="cough_breath_no">No</label>
                  <input id="cough_breath_yes" type="radio" name="cough_breath" value="Yes" {{ checked('cough_breath','Yes','No') }}>
                  <label for="cough_breath_yes">Yes</label>
                </div>
              </div>
            </div>

            <div class="field">
              <label for="rr">Breaths per minute (optional)</label>
              <input id="rr" type="number" name="rr" min="0" max="120" inputmode="numeric" value="{{ form.get('rr','') }}" placeholder="e.g., 48">
              <div class="hint">Tip: count breaths for 60 seconds while the child is calm.</div>
            </div>

            <div class="row" style="margin-top: 10px;">
              <div class="field">
                <label>Chest indrawing?</label>
                <div class="segmented" role="group" aria-label="Chest indrawing">
                  <input id="chest_indrawing_no" type="radio" name="chest_indrawing" value="No" {{ checked('chest_indrawing','No','No') }}>
                  <label for="chest_indrawing_no">No</label>
                  <input id="chest_indrawing_yes" type="radio" name="chest_indrawing" value="Yes" {{ checked('chest_indrawing','Yes','No') }}>
                  <label for="chest_indrawing_yes">Yes</label>
                </div>
              </div>

              <div class="field">
                <label>Stridor (noisy breathing when calm)?</label>
                <div class="segmented" role="group" aria-label="Stridor">
                  <input id="stridor_no" type="radio" name="stridor" value="No" {{ checked('stridor','No','No') }}>
                  <label for="stridor_no">No</label>
                  <input id="stridor_yes" type="radio" name="stridor" value="Yes" {{ checked('stridor','Yes','No') }}>
                  <label for="stridor_yes">Yes</label>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>Nutrition</h3>
            <div class="row">
              <div class="field">
                <label for="muac">MUAC color (6–59 months)</label>
                <select id="muac" name="muac" required>
                  <option value="not_measured" {{ selected('muac','not_measured','not_measured') }}>Not measured</option>
                  <option value="green" {{ selected('muac','green','not_measured') }}>Green</option>
                  <option value="yellow" {{ selected('muac','yellow','not_measured') }}>Yellow</option>
                  <option value="red" {{ selected('muac','red','not_measured') }}>Red</option>
                </select>
              </div>

              <div class="field">
                <label>Swelling on both feet?</label>
                <div class="segmented" role="group" aria-label="Swelling on both feet">
                  <input id="oedema_no" type="radio" name="oedema" value="No" {{ checked('oedema','No','No') }}>
                  <label for="oedema_no">No</label>
                  <input id="oedema_yes" type="radio" name="oedema" value="Yes" {{ checked('oedema','Yes','No') }}>
                  <label for="oedema_yes">Yes</label>
                </div>
              </div>
            </div>

            <div id="young_infant" class="card" style="margin-top: 14px;" aria-label="Young infant add-on">
              <h3>Young infant add-on (0–2 months)</h3>
              <p class="muted">Only answer if the age group is 0–2 months.</p>
              <div class="row">
                <div class="field">
                  <label>Not feeding well?</label>
                  <div class="segmented" role="group" aria-label="Not feeding well">
                    <input id="not_feeding_no" type="radio" name="not_feeding" value="No" {{ checked('not_feeding','No','No') }}>
                    <label for="not_feeding_no">No</label>
                    <input id="not_feeding_yes" type="radio" name="not_feeding" value="Yes" {{ checked('not_feeding','Yes','No') }}>
                    <label for="not_feeding_yes">Yes</label>
                  </div>
                </div>

                <div class="field">
                  <label>Moves only when stimulated?</label>
                  <div class="segmented" role="group" aria-label="Moves only when stimulated">
                    <input id="stim_only_no" type="radio" name="stim_only" value="No" {{ checked('stim_only','No','No') }}>
                    <label for="stim_only_no">No</label>
                    <input id="stim_only_yes" type="radio" name="stim_only" value="Yes" {{ checked('stim_only','Yes','No') }}>
                    <label for="stim_only_yes">Yes</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>Malaria test (if available)</h3>
            <div class="field">
              <label for="rdt">RDT result</label>
              <select id="rdt" name="rdt" required>
                <option value="not_done" {{ selected('rdt','not_done','not_done') }}>Not done</option>
                <option value="negative" {{ selected('rdt','negative','not_done') }}>Negative</option>
                <option value="positive" {{ selected('rdt','positive','not_done') }}>Positive</option>
              </select>
            </div>

            <div class="sticky-actions">
              <div class="btn-row">
                <button class="btn btn-primary" type="submit">Get result</button>
                <button class="btn btn-secondary" type="reset">Reset</button>
              </div>
            </div>
          </form>
        </section>
      </main>

      <aside>
        <!-- Patients moved to RIGHT column (what you asked for) -->
        <section class="card" aria-label="Patients">
          <h2>Patients (local only)</h2>
          <p class="muted">This saves on the device (SQLite). Keep info minimal.</p>

          <div class="subgrid">
            <div class="card" style="margin:0;">
              <h3>Add patient</h3>
              <form method="post">
                <input type="hidden" name="action" value="add_patient">
                <div class="field">
                  <label for="p_name">Name / nickname</label>
                  <input id="p_name" type="text" name="p_name" placeholder="e.g., Amina" required>
                </div>
                <div class="field">
                  <label for="p_village">Village (optional)</label>
                  <input id="p_village" type="text" name="p_village" placeholder="e.g., Kibera">
                </div>
                <div class="field">
                  <label for="p_age_group">Default age group</label>
                  <select id="p_age_group" name="p_age_group" required>
                    <option value="0_2m">0–2 months</option>
                    <option value="2_12m">2–12 months</option>
                    <option value="1_5y" selected>1–5 years</option>
                  </select>
                </div>
                <div class="btn-row">
                  <button class="btn btn-secondary" type="submit">Add patient</button>
                </div>
              </form>
            </div>

            <div class="card" style="margin:0;">
              <h3>Patient list</h3>
              {% if patients|length == 0 %}
                <p class="muted">No patients yet.</p>
              {% else %}
                <table class="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th class="nowrap">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for p in patients %}
                      <tr>
                        <td>
                          {{ p.name }}
                          {% if p.id == (selected_patient.id if selected_patient else -1) %}
                            <span class="chip">Selected</span>
                          {% endif %}
                          <div class="muted" style="margin-top:4px;">
                            {{ p.age_group_label }}{% if p.village %} • {{ p.village }}{% endif %}
                          </div>
                        </td>
                        <td class="nowrap">
                          <a class="btn btn-secondary" href="{{ url_for('index', patient_id=p.id, assessor=assessor_filter) }}">Select</a>
                          <form method="post" style="margin-top:8px;" onsubmit="return confirm('Delete this patient and history?');">
                            <input type="hidden" name="action" value="delete_patient">
                            <input type="hidden" name="patient_id" value="{{ p.id }}">
                            <button class="btn btn-danger" type="submit">Delete</button>
                          </form>
                        </td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              {% endif %}
              <div class="divider"></div>
              <p class="muted">Select a patient if you want to save screening history (optional).</p>
            </div>
          </div>

          {% if selected_patient %}
            <div class="divider"></div>
            <h3>Recent screenings (last 5)</h3>
            {% if history|length == 0 %}
              <p class="muted">No screenings yet for this patient.</p>
            {% else %}
              <table class="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Risk</th>
                    <th>Top</th>
                    <th>Cert.</th>
                  </tr>
                </thead>
                <tbody>
                  {% for h in history %}
                    <tr>
                      <td class="nowrap">{{ h.created_at }}</td>
                      <td>{{ h.risk }}</td>
                      <td>{{ h.top_condition }}</td>
                      <td>{{ h.certainty }}%</td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            {% endif %}
          {% endif %}
        </section>

        <!-- Lightweight analytics / progress tracking -->
        <section class="card" aria-label="Analytics">
          <h2>Progress tracking</h2>
          <p class="muted">Local analytics from saved screenings. Use Assessor filter to view one CHW or “All”.</p>

          <form method="get" style="margin-top:10px;">
            {% if selected_patient %}
              <input type="hidden" name="patient_id" value="{{ selected_patient.id }}">
            {% endif %}
            <div class="row">
              <div class="field">
                <label for="assessor_filter">Assessor filter</label>
                <select id="assessor_filter" name="assessor" onchange="this.form.submit()">
                  <option value="__all__" {{ 'selected' if assessor_filter == '__all__' else '' }}>All assessors</option>
                  {% for a in assessors %}
                    <option value="{{ a }}" {{ 'selected' if assessor_filter == a else '' }}>{{ a }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="field">
                <label for="days">Time window</label>
                <select id="days" name="days" onchange="this.form.submit()">
                  {% for d in [7, 14, 30, 90, 365] %}
                    <option value="{{ d }}" {{ 'selected' if analytics.days == d else '' }}>Last {{ d }} days</option>
                  {% endfor %}
                </select>
              </div>
            </div>
          </form>

          <div class="kpi">
            <div class="k">
              <div class="label">Total screenings</div>
              <div class="val">{{ analytics.total }}</div>
            </div>
            <div class="k">
              <div class="label">Unique patients screened</div>
              <div class="val">{{ analytics.unique_patients }}</div>
            </div>
            <div class="k">
              <div class="label">High-risk</div>
              <div class="val">{{ analytics.high }}{% if analytics.total > 0 %} ({{ analytics.high_pct }}%) {% endif %}</div>
            </div>
            <div class="k">
              <div class="label">Follow-up needed (High+Medium)</div>
              <div class="val">{{ analytics.followup }}</div>
            </div>
          </div>

          <div class="divider"></div>

          <h3>What admin should look at</h3>
          <ul>
            <li><strong>Top suspected conditions:</strong> {{ analytics.top_conditions_text }}</li>
            <li><strong>Average certainty:</strong> {{ analytics.avg_certainty }}%</li>
            <li><strong>Malaria RDT positivity:</strong> {{ analytics.rdt_pos_rate }}</li>
            <li><strong>SAM signals (MUAC red or oedema):</strong> {{ analytics.sam_signals }}</li>
            <li><strong>Danger signs flagged:</strong> {{ analytics.danger_signs }}</li>
          </ul>

          {% if analytics.insight %}
            <div class="divider"></div>
            <p class="muted"><strong>Insight:</strong> {{ analytics.insight }}</p>
          {% endif %}
        </section>

        <section class="card" aria-label="Quick guidance">
          <h2>Quick guidance</h2>
          <p class="muted">Use this as a structured checklist during assessment.</p>
          <ul>
            <li>Start with danger signs.</li>
            <li>Measure breathing rate if possible.</li>
            <li>Measure MUAC for 6–59 months when available.</li>
            <li>If unsure, arrange follow-up or refer per local protocol.</li>
          </ul>
        </section>

        <section class="card" aria-label="Privacy">
          <h2>Privacy</h2>
          <p class="muted">Keep messages short and avoid sensitive identifiers. WhatsApp numbers are optional.</p>
        </section>
      </aside>
    </div>
  </div>

  <script>
    function copyShareText() {
      const el = document.getElementById('shareText');
      const status = document.getElementById('copyStatus');
      if (!el) return;

      const text = el.value || el.textContent || "";
      const done = () => { if (status) status.textContent = "Copied."; };
      const fail = () => { if (status) status.textContent = "Copy failed. Long-press to copy."; };

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(fail);
        return;
      }

      el.focus();
      el.select();
      el.setSelectionRange(0, 999999);
      try { document.execCommand('copy'); done(); } catch (e) { fail(); }
      window.getSelection().removeAllRanges();
    }

    function syncYoungInfant() {
      const age = document.getElementById('age_group');
      const box = document.getElementById('young_infant');
      if (!age || !box) return;
      const show = age.value === '0_2m';
      box.classList.toggle('hidden', !show);
    }

    document.addEventListener('DOMContentLoaded', () => {
      const age = document.getElementById('age_group');
      if (age) age.addEventListener('change', syncYoungInfant);
      syncYoungInfant();
    });
  </script>
</body>
</html>
"""

# ---------------- DB ----------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
      CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        village TEXT,
        age_group TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    """)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        assessor TEXT,
        created_at TEXT NOT NULL,
        risk TEXT NOT NULL,
        top_condition TEXT NOT NULL,
        certainty INTEGER NOT NULL,
        share_message TEXT NOT NULL,
        raw_answers TEXT NOT NULL,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
      )
    """)
    conn.commit()
    conn.close()

def age_group_label(v: str) -> str:
    return {"0_2m": "0–2 months", "2_12m": "2–12 months", "1_5y": "1–5 years"}.get(v, v)

# ---------------- scoring ----------------

def softmax(scores: dict) -> dict:
    m = max(scores.values())
    exps = {k: math.exp(v - m) for k, v in scores.items()}
    s = sum(exps.values())
    return {k: (exps[k] / s if s else 0.25) for k in scores}

def digits_only(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\D+", "", s)

def make_whatsapp_link(message: str, phone_digits: str = "") -> str:
    encoded = quote(message)
    if phone_digits:
        return f"https://wa.me/{phone_digits}?text={encoded}"
    return f"https://wa.me/?text={encoded}"

def compute_result(a: dict, selected_patient=None):
    wa_caregiver = digits_only(a.get("wa_caregiver", ""))
    wa_supervisor = digits_only(a.get("wa_supervisor", ""))

    include_identifiers = (a.get("include_identifiers") == "Yes")

    danger = any(a.get(k) == "Yes" for k in ["ds_drink", "ds_vomit", "ds_convulsions", "ds_lethargy"])

    age = a.get("age_group", "1_5y")
    fever = (a.get("fever") == "Yes")
    cough = (a.get("cough_breath") == "Yes")

    rr = a.get("rr")
    rr = int(rr) if rr and str(rr).strip().isdigit() else None

    chest_indrawing = (a.get("chest_indrawing") == "Yes")
    stridor = (a.get("stridor") == "Yes")

    muac = a.get("muac", "not_measured")
    oedema = (a.get("oedema") == "Yes")

    not_feeding = (a.get("not_feeding") == "Yes")
    stim_only = (a.get("stim_only") == "Yes")

    rdt = a.get("rdt", "not_done")

    scores = {
        "Pneumonia": 0.0,
        "Malaria": 0.0,
        "Malnutrition": 0.0,
        "Neonatal complications": 0.0,
    }

    if age == "0_2m":
        scores["Neonatal complications"] += 2.0

    if fever:
        scores["Malaria"] += 2.5
        if age == "0_2m":
            scores["Neonatal complications"] += 2.0

    if cough:
        scores["Pneumonia"] += 2.5

    fast_breathing = False
    if rr is not None:
        if age == "2_12m" and rr >= 50:
            fast_breathing = True
        if age == "1_5y" and rr >= 40:
            fast_breathing = True
        if age == "0_2m" and rr >= 60:
            fast_breathing = True

    if fast_breathing:
        scores["Pneumonia"] += 3.0
        if age == "0_2m":
            scores["Neonatal complications"] += 2.5

    if chest_indrawing:
        scores["Pneumonia"] += 2.5
        if age == "0_2m":
            scores["Neonatal complications"] += 2.0

    if stridor:
        scores["Pneumonia"] += 2.0

    if rdt == "positive":
        scores["Malaria"] += 6.0
    elif rdt == "negative":
        scores["Malaria"] -= 3.0

    if oedema:
        scores["Malnutrition"] += 7.0
    if muac == "red":
        scores["Malnutrition"] += 6.0
    elif muac == "yellow":
        scores["Malnutrition"] += 3.0

    if age == "0_2m":
        if not_feeding:
            scores["Neonatal complications"] += 3.5
        if stim_only:
            scores["Neonatal complications"] += 3.5

    high_triggers = []
    if danger:
        high_triggers.append("General danger sign present")
    if oedema or muac == "red":
        high_triggers.append("Severe acute malnutrition signs")
    if (cough and (chest_indrawing or stridor)) or (cough and fast_breathing and age == "0_2m"):
        high_triggers.append("Severe breathing problem signs")
    if age == "0_2m" and (not_feeding or stim_only or fast_breathing or chest_indrawing or fever):
        high_triggers.append("Young infant severe illness signs")

    probs = softmax(scores)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    top_name, top_p = sorted_probs[0]
    alternatives = [(n, int(round(p * 100))) for n, p in sorted_probs[1:3]]
    certainty = int(round(top_p * 100))

    if high_triggers:
        risk = "High"
        box_class = "danger"
    elif certainty >= 80:
        risk = "Medium"
        box_class = "warn"
    else:
        risk = "Low"
        box_class = "ok"

    actions, tips = [], []

    if risk == "High":
        actions.append("Refer urgently to the nearest health facility now.")
        actions.append("Keep the child warm and continue breastfeeding/feeding if able.")
        if rdt == "positive":
            actions.append("If trained and stocked, follow local malaria protocol for confirmed malaria; otherwise refer.")
        if muac == "red" or oedema:
            actions.append("Ask for urgent nutrition program/clinical assessment (SAM).")
    else:
        actions.append("Follow local protocol; arrange follow-up if symptoms continue or worsen.")
        if top_name == "Pneumonia":
            actions.append("If breathing is fast for age or worsening, go to a facility the same day.")
        if top_name == "Malaria":
            actions.append("If fever continues, get a malaria test if available and follow local treatment guidance.")
        if top_name == "Malnutrition":
            actions.append("Measure MUAC if not done; link to community nutrition services if available.")
        if top_name == "Neonatal complications":
            actions.append("Young infants can deteriorate fast; seek facility assessment promptly.")

    if top_name == "Pneumonia":
        tips += [
            "Keep the child warm.",
            "Continue breastfeeding/feeding and offer fluids often.",
            "If breathing becomes difficult, chest pulls in, or the child cannot drink—go urgently.",
        ]
    elif top_name == "Malaria":
        tips += [
            "Treat fever with locally recommended fever care and keep the child hydrated.",
            "If you can, get a malaria rapid test as soon as possible.",
            "If the child becomes very sleepy, has convulsions, or cannot drink—go urgently.",
        ]
    elif top_name == "Malnutrition":
        tips += [
            "Continue breastfeeding if the child is breastfeeding.",
            "Give small, frequent, energy-dense meals if the child can eat.",
            "Wash hands and use safe water to reduce infections that worsen nutrition.",
        ]
    else:
        tips += [
            "Keep the baby warm (skin-to-skin if possible).",
            "Breastfeed frequently if the baby can feed.",
            "If feeding is poor, fever/low temperature, or low movement—go urgently.",
        ]

    action_short = actions[:2]
    alt_text = ", ".join([f"{n} {pct}%" for n, pct in alternatives])

    share_lines = ["Toto Gemma — Under-5 screening result"]

    # Optional identifiers (OFF by default)
    if include_identifiers and selected_patient:
        share_lines.append(f"Patient: {selected_patient['name']}")
        if selected_patient.get("village"):
            share_lines.append(f"Village: {selected_patient['village']}")

    share_lines += [
        f"Risk: {risk}",
        f"Most likely: {top_name} ({certainty}%)",
        f"Also consider: {alt_text}" if alt_text else "",
        "Next steps:",
    ]
    share_lines += [f"- {s}" for s in action_short]
    if danger:
        share_lines.append("Danger signs present: seek urgent care now.")

    share_message = "\n".join([x for x in share_lines if x.strip()])

    return {
        "risk": risk,
        "top_condition": top_name,
        "certainty": certainty,
        "alternatives": alternatives,
        "actions": actions,
        "tips": tips,
        "box_class": box_class,
        "share_message": share_message,
        "wa_caregiver_url": make_whatsapp_link(share_message, wa_caregiver),
        "wa_supervisor_url": make_whatsapp_link(share_message, wa_supervisor),
    }

# ---------------- analytics ----------------

def compute_analytics(conn, assessor_filter="__all__", days=30):
    days = int(days)
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M")

    params = [cutoff_str]
    where = "created_at >= ?"
    if assessor_filter and assessor_filter != "__all__":
        where += " AND assessor = ?"
        params.append(assessor_filter)

    rows = conn.execute(
        f"""SELECT id, patient_id, assessor, created_at, risk, top_condition, certainty, raw_answers
            FROM screenings
            WHERE {where}
            ORDER BY id DESC""",
        params
    ).fetchall()

    total = len(rows)
    if total == 0:
        return {
            "days": days,
            "total": 0,
            "unique_patients": 0,
            "high": 0, "high_pct": 0,
            "medium": 0, "low": 0,
            "followup": 0,
            "avg_certainty": 0,
            "top_conditions_text": "—",
            "rdt_pos_rate": "—",
            "sam_signals": "—",
            "danger_signs": "—",
            "insight": "No screenings in this time window."
        }

    risk_counts = Counter([r["risk"] for r in rows])
    high = risk_counts.get("High", 0)
    medium = risk_counts.get("Medium", 0)
    low = risk_counts.get("Low", 0)
    followup = high + medium
    high_pct = int(round((high / total) * 100)) if total else 0

    # Conditions
    cond_counts = Counter([r["top_condition"] for r in rows]).most_common(3)
    top_conditions_text = ", ".join([f"{c} ({n})" for c, n in cond_counts]) if cond_counts else "—"

    # Avg certainty
    avg_certainty = int(round(sum([r["certainty"] for r in rows]) / total))

    # Parse raw answers for a few useful admin metrics (no heavy analytics)
    rdt_done = 0
    rdt_pos = 0
    sam_signals = 0
    danger_flags = 0

    for r in rows:
        try:
            a = json.loads(r["raw_answers"])
        except Exception:
            a = {}

        rdt = a.get("rdt", "not_done")
        if rdt in ("positive", "negative"):
            rdt_done += 1
            if rdt == "positive":
                rdt_pos += 1

        muac = a.get("muac", "not_measured")
        oedema = a.get("oedema", "No")
        if muac == "red" or oedema == "Yes":
            sam_signals += 1

        if any(a.get(k) == "Yes" for k in ["ds_drink", "ds_vomit", "ds_convulsions", "ds_lethargy"]):
            danger_flags += 1

    rdt_pos_rate = "—"
    if rdt_done > 0:
        rdt_pos_rate = f"{int(round((rdt_pos/rdt_done)*100))}% ({rdt_pos}/{rdt_done})"

    # Unique patients (screens without patient_id count as 0-patient)
    unique_patients = len(set([r["patient_id"] for r in rows if r["patient_id"] is not None]))

    # Simple admin insight
    insight = ""
    if high_pct >= 25:
        insight = "High-risk share is elevated. Check referral capacity and follow-up completion."
    elif followup >= max(5, total * 0.3):
        insight = "Lots of Medium/High cases. Make sure follow-ups are happening in 24–48 hours."
    else:
        insight = "Risk levels look stable. Focus on consistent coverage and repeat checks."

    return {
        "days": days,
        "total": total,
        "unique_patients": unique_patients,
        "high": high,
        "high_pct": high_pct,
        "medium": medium,
        "low": low,
        "followup": followup,
        "avg_certainty": avg_certainty,
        "top_conditions_text": top_conditions_text,
        "rdt_pos_rate": rdt_pos_rate,
        "sam_signals": f"{sam_signals}/{total}",
        "danger_signs": f"{danger_flags}/{total}",
        "insight": insight
    }

# ---------------- routes ----------------

@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    conn = get_conn()

    message = None
    result = None
    form_data = {}

    patient_id = (request.args.get("patient_id") or "").strip()
    assessor_filter = (request.args.get("assessor") or "__all__").strip()
    days = (request.args.get("days") or "30").strip()
    try:
        days_int = int(days)
    except Exception:
        days_int = 30

    if request.method == "POST":
        action = request.form.get("action", "")
        form_data = request.form.to_dict()

        if action == "add_patient":
            name = (request.form.get("p_name") or "").strip()
            village = (request.form.get("p_village") or "").strip()
            age_group = request.form.get("p_age_group", "1_5y").strip()
            if not name:
                message = "Patient name is required."
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.execute(
                    "INSERT INTO patients (name, village, age_group, created_at) VALUES (?,?,?,?)",
                    (name, village, age_group, now),
                )
                conn.commit()
                new_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
                conn.close()
                return redirect(url_for("index", patient_id=new_id, assessor=assessor_filter, days=days_int))

        elif action == "delete_patient":
            del_id = (request.form.get("patient_id") or "").strip()
            if del_id.isdigit():
                conn.execute("DELETE FROM screenings WHERE patient_id = ?", (int(del_id),))
                conn.execute("DELETE FROM patients WHERE id = ?", (int(del_id),))
                conn.commit()
                if patient_id == del_id:
                    conn.close()
                    return redirect(url_for("index", assessor=assessor_filter, days=days_int))
            else:
                message = "Invalid patient id."

        elif action == "run_screening":
            # Resolve selected patient from hidden form field (not just query param)
            pid = (request.form.get("patient_id") or "").strip()
            selected_patient = None
            if pid.isdigit():
                row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(pid),)).fetchone()
                if row:
                    selected_patient = dict(row)

            result = compute_result(form_data, selected_patient=selected_patient)

            # Persist screening
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            assessor = (request.form.get("assessor") or "local_user").strip() or "local_user"
            pid_to_save = int(pid) if pid.isdigit() else None
            conn.execute(
                """INSERT INTO screenings
                   (patient_id, assessor, created_at, risk, top_condition, certainty, share_message, raw_answers)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    pid_to_save,
                    assessor,
                    now,
                    result["risk"],
                    result["top_condition"],
                    int(result["certainty"]),
                    result["share_message"],
                    json.dumps(form_data, ensure_ascii=False),
                ),
            )
            conn.commit()

            # Keep selection after submit
            patient_id = pid

    # Load patients list
    patients_rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    patients = []
    for r in patients_rows:
        d = dict(r)
        d["age_group_label"] = age_group_label(d["age_group"])
        patients.append(d)

    # Selected patient
    selected_patient = None
    default_age_group = "0_2m"  # sensible safe default in your current UI
    if patient_id.isdigit():
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
        if row:
            selected_patient = dict(row)
            selected_patient["age_group_label"] = age_group_label(selected_patient["age_group"])
            default_age_group = selected_patient["age_group"]

    # Patient history
    history = []
    if selected_patient:
        rows = conn.execute(
            "SELECT created_at, risk, top_condition, certainty FROM screenings WHERE patient_id = ? ORDER BY id DESC LIMIT 5",
            (int(patient_id),),
        ).fetchall()
        history = [dict(x) for x in rows]

    # Assessors for filter dropdown
    assessor_rows = conn.execute(
        "SELECT DISTINCT assessor FROM screenings WHERE assessor IS NOT NULL AND assessor != '' ORDER BY assessor ASC"
    ).fetchall()
    assessors = [r["assessor"] for r in assessor_rows if r["assessor"]]

    # Analytics
    analytics = compute_analytics(conn, assessor_filter=assessor_filter, days=days_int)

    conn.close()

    # default assessor for form field
    assessor_default = assessor_filter if assessor_filter != "__all__" else "local_user"

    return render_template_string(
        HTML,
        result=result,
        form=form_data,
        message=message,
        patients=patients,
        selected_patient=selected_patient,
        history=history,
        default_age_group=default_age_group,
        assessors=assessors,
        assessor_filter=assessor_filter,
        analytics=analytics,
        assessor_default=assessor_default,
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
