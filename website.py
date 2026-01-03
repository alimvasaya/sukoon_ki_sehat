# website.py
from flask import Flask, render_template_string, request, redirect, url_for
import math
import re
import sqlite3
import json
from urllib.parse import quote
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = "toto.db"

HTML = r"""
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
    .brand p { margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.35; }

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
      .grid { grid-template-columns: 1.15fr 0.85fr; align-items: start; }
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
      font-weight: 800;
      font-size: 0.88rem;
      white-space: nowrap;
    }

    .danger { border-color: rgba(255,92,119,0.35); background: linear-gradient(180deg, rgba(255,92,119,0.16), rgba(255,255,255,0.06)); }
    .warn   { border-color: rgba(255,207,90,0.35); background: linear-gradient(180deg, rgba(255,207,90,0.16), rgba(255,255,255,0.06)); }
    .ok     { border-color: rgba(47,208,124,0.35); background: linear-gradient(180deg, rgba(47,208,124,0.16), rgba(255,255,255,0.06)); }

    form { margin: 0; }
    label { display:block; margin: 10px 0 6px; font-weight: 800; }

    .row { display: grid; grid-template-columns: 1fr; gap: 10px; }
    @media (min-width: 640px) { .row { grid-template-columns: 1fr 1fr; } }

    .row3 { display: grid; grid-template-columns: 1fr; gap: 10px; }
    @media (min-width: 960px) {
      .row3 { grid-template-columns: 1fr 1fr 1fr; align-items: end; }
    }

    /* Fix alignment: give labels a consistent height on larger screens */
    @media (min-width: 640px) {
      .row > div > label,
      .row3 > div > label { min-height: 2.6em; display:flex; align-items:flex-end; }
    }

    input[type="number"], input[type="text"], input[type="tel"], select, textarea {
      width: 100%;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      outline: none;
      min-height: 44px;
    }

    /* Fix dropdown options not showing: force option colors */
    select { color-scheme: light dark; }
    select option { color: #0a0e1c; background: #ffffff; }
    @media (prefers-color-scheme: light) {
      select option { color: #0a0e1c; background: #ffffff; }
    }

    textarea { min-height: 132px; resize: vertical; }

    select {
      appearance: none;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position: calc(100% - 18px) calc(1em + 2px), calc(100% - 13px) calc(1em + 2px);
      background-size: 6px 6px, 6px 6px;
      background-repeat: no-repeat;
      padding-right: 40px;
    }

    input::placeholder, textarea::placeholder { color: rgba(255,255,255,0.45); }
    @media (prefers-color-scheme: light) {
      input::placeholder, textarea::placeholder { color: rgba(10,14,28,0.38); }
    }
    input:focus, select:focus, textarea:focus {
      border-color: rgba(124,108,255,0.65);
      box-shadow: 0 0 0 4px rgba(124,108,255,0.18);
    }

    .segmented {
      display: grid;
      grid-template-columns: 1fr 1fr;
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
      background: rgba(255,255,255,0.04);
      min-height: 44px;
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
      min-height: 44px;
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
    .table th, .table td { text-align: left; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.10); vertical-align: top; }
    @media (prefers-color-scheme: light) {
      .table th, .table td { border-bottom: 1px solid rgba(10,14,28,0.10); }
    }
    .nowrap { white-space: nowrap; }
    .chip {
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      font-weight: 850;
      font-size: 0.88rem;
      white-space: nowrap;
    }

    .mini-bar {
      height: 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid var(--border);
      overflow: hidden;
    }
    .mini-bar > div {
      height: 100%;
      background: rgba(124,108,255,0.55);
      width: 0%;
    }
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
        <p>Screening + coaching only. If any danger sign is present, refer urgently.</p>
      </div>
      <div class="badges" aria-label="Status">
        <span class="badge"><span class="badge-dot" aria-hidden="true"></span>Offline-ready (SQLite)</span>
      </div>
    </div>

    {% if message %}
      <div class="card warn" style="margin-top:14px;">
        <strong>{{ message }}</strong>
      </div>
    {% endif %}

    <div class="grid">
      <main>
        {% if result %}
          <section class="card result {{ result.box_class }}" aria-label="Screening result">
            <div class="pill-row">
              <span class="pill">Risk: {{ result.risk }}</span>
              <span class="pill">Most likely: {{ result.top_condition }}</span>
              <span class="pill">Certainty: {{ result.certainty }}%</span>
            </div>

            <h2>What to do now</h2>
            <ul>
              {% for s in result.actions %}
                <li>{{ s }}</li>
              {% endfor %}
            </ul>

            <div class="divider"></div>

            <h2>Coaching tips</h2>
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
          </section>

          <section class="card" aria-label="Share via WhatsApp">
            <h2>Share via WhatsApp</h2>
            <p class="muted">This does not auto-send. It opens WhatsApp with a pre-filled summary.</p>

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

        <section class="card" aria-label="Add patient">
          <h2>Add patient (local only)</h2>
          <p class="muted">Saves only on this device. Keep info minimal.</p>

          <form method="post">
            <input type="hidden" name="action" value="add_patient">

            <div class="row">
              <div>
                <label for="p_name">Name / nickname</label>
                <input id="p_name" type="text" name="p_name" placeholder="e.g., Amina" required>
              </div>
              <div>
                <label for="p_village">Village (optional)</label>
                <input id="p_village" type="text" name="p_village" placeholder="e.g., Kibera">
              </div>
            </div>

            <label for="p_age_group">Default age group</label>
            <select id="p_age_group" name="p_age_group" required>
              <option value="0_2m">0–2 months</option>
              <option value="2_12m">2–12 months</option>
              <option value="1_5y" selected>1–5 years</option>
            </select>

            <div class="btn-row">
              <button class="btn btn-secondary" type="submit">Add patient</button>
            </div>
          </form>
        </section>

        <section id="screen" class="card" aria-label="Under-5 screening form">
          <h2>Screening form</h2>
          <p class="muted">Answer what applies. If you selected a patient on the right, screenings save under them.</p>

          {% if selected_patient %}
            <div class="pill-row">
              <span class="chip">Current patient: {{ selected_patient['name'] }}{% if selected_patient['village'] %} — {{ selected_patient['village'] }}{% endif %}</span>
            </div>
          {% endif %}

          <form method="post" novalidate>
            <input type="hidden" name="action" value="run_screening">

            <div class="row3">
              <div>
                <label for="age_group">Age group</label>
                <select id="age_group" name="age_group" required>
                  <option value="0_2m" {{ selected('age_group','0_2m', default_age_group) }}>0–2 months</option>
                  <option value="2_12m" {{ selected('age_group','2_12m', default_age_group) }}>2–12 months</option>
                  <option value="1_5y" {{ selected('age_group','1_5y', default_age_group) }}>1–5 years</option>
                </select>
              </div>
              <div>
                <label for="wa_caregiver">Caregiver WhatsApp (optional)</label>
                <input id="wa_caregiver" type="tel" name="wa_caregiver" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_caregiver','') }}" placeholder="Digits only, include country code">
              </div>
              <div>
                <label for="wa_supervisor">Supervisor WhatsApp (optional)</label>
                <input id="wa_supervisor" type="tel" name="wa_supervisor" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_supervisor','') }}" placeholder="Digits only, include country code">
              </div>
            </div>

            <div class="row" style="margin-top: 6px;">
              <div>
                <label for="assessor">Assessor / CHW name (optional)</label>
                <input id="assessor" type="text" name="assessor" value="{{ form.get('assessor','') }}" placeholder="e.g., Fatima">
              </div>
              <div>
                <label>Include patient name in WhatsApp?</label>
                <div class="segmented" role="group" aria-label="Include patient name">
                  <input id="include_name_no" type="radio" name="include_name" value="No" {{ checked('include_name','No','No') }}>
                  <label for="include_name_no">No</label>
                  <input id="include_name_yes" type="radio" name="include_name" value="Yes" {{ checked('include_name','Yes','No') }}>
                  <label for="include_name_yes">Yes</label>
                </div>
                <div class="hint">Only used if a patient is selected.</div>
              </div>
            </div>

            <div class="row" style="margin-top: 6px;">
              <div>
                <label>Include village in WhatsApp?</label>
                <div class="segmented" role="group" aria-label="Include village">
                  <input id="include_village_no" type="radio" name="include_village" value="No" {{ checked('include_village','No','No') }}>
                  <label for="include_village_no">No</label>
                  <input id="include_village_yes" type="radio" name="include_village" value="Yes" {{ checked('include_village','Yes','No') }}>
                  <label for="include_village_yes">Yes</label>
                </div>
                <div class="hint">Only used if a patient is selected.</div>
              </div>
              <div></div>
            </div>

            <div class="divider"></div>

            <div class="card warn" aria-label="Danger signs">
              <h3>Danger signs</h3>
              <p class="muted">If any are Yes, refer urgently.</p>

              <div class="row">
                <div>
                  <label>Not able to drink/breastfeed?</label>
                  <div class="segmented" role="group">
                    <input id="ds_drink_no" type="radio" name="ds_drink" value="No" {{ checked('ds_drink','No','No') }}>
                    <label for="ds_drink_no">No</label>
                    <input id="ds_drink_yes" type="radio" name="ds_drink" value="Yes" {{ checked('ds_drink','Yes','No') }}>
                    <label for="ds_drink_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Vomits everything?</label>
                  <div class="segmented" role="group">
                    <input id="ds_vomit_no" type="radio" name="ds_vomit" value="No" {{ checked('ds_vomit','No','No') }}>
                    <label for="ds_vomit_no">No</label>
                    <input id="ds_vomit_yes" type="radio" name="ds_vomit" value="Yes" {{ checked('ds_vomit','Yes','No') }}>
                    <label for="ds_vomit_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Convulsions?</label>
                  <div class="segmented" role="group">
                    <input id="ds_convulsions_no" type="radio" name="ds_convulsions" value="No" {{ checked('ds_convulsions','No','No') }}>
                    <label for="ds_convulsions_no">No</label>
                    <input id="ds_convulsions_yes" type="radio" name="ds_convulsions" value="Yes" {{ checked('ds_convulsions','Yes','No') }}>
                    <label for="ds_convulsions_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Very sleepy/unconscious?</label>
                  <div class="segmented" role="group">
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
              <div>
                <label>Fever now or in last 2 days?</label>
                <div class="segmented" role="group">
                  <input id="fever_no" type="radio" name="fever" value="No" {{ checked('fever','No','No') }}>
                  <label for="fever_no">No</label>
                  <input id="fever_yes" type="radio" name="fever" value="Yes" {{ checked('fever','Yes','No') }}>
                  <label for="fever_yes">Yes</label>
                </div>
              </div>
              <div>
                <label>Cough or difficult breathing?</label>
                <div class="segmented" role="group">
                  <input id="cough_breath_no" type="radio" name="cough_breath" value="No" {{ checked('cough_breath','No','No') }}>
                  <label for="cough_breath_no">No</label>
                  <input id="cough_breath_yes" type="radio" name="cough_breath" value="Yes" {{ checked('cough_breath','Yes','No') }}>
                  <label for="cough_breath_yes">Yes</label>
                </div>
              </div>
            </div>

            <label for="rr">Breaths per minute (optional)</label>
            <input id="rr" type="number" name="rr" min="0" max="120" inputmode="numeric"
                   value="{{ form.get('rr','') }}" placeholder="e.g., 48">
            <div class="hint">Tip: count breaths for 60 seconds while the child is calm.</div>

            <div class="row" style="margin-top: 10px;">
              <div>
                <label>Chest indrawing?</label>
                <div class="segmented" role="group">
                  <input id="chest_indrawing_no" type="radio" name="chest_indrawing" value="No" {{ checked('chest_indrawing','No','No') }}>
                  <label for="chest_indrawing_no">No</label>
                  <input id="chest_indrawing_yes" type="radio" name="chest_indrawing" value="Yes" {{ checked('chest_indrawing','Yes','No') }}>
                  <label for="chest_indrawing_yes">Yes</label>
                </div>
              </div>
              <div>
                <label>Stridor (noisy breathing when calm)?</label>
                <div class="segmented" role="group">
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
              <div>
                <label for="muac">MUAC color (6–59 months)</label>
                <select id="muac" name="muac" required>
                  <option value="not_measured" {{ selected('muac','not_measured','not_measured') }}>Not measured</option>
                  <option value="green" {{ selected('muac','green','not_measured') }}>Green</option>
                  <option value="yellow" {{ selected('muac','yellow','not_measured') }}>Yellow</option>
                  <option value="red" {{ selected('muac','red','not_measured') }}>Red</option>
                </select>
              </div>
              <div>
                <label>Swelling on both feet?</label>
                <div class="segmented" role="group">
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
                <div>
                  <label>Not feeding well?</label>
                  <div class="segmented" role="group">
                    <!-- IMPORTANT: default is '' so it's not pre-selected unless 0_2m is chosen -->
                    <input id="not_feeding_no" type="radio" name="not_feeding" value="No" {{ checked('not_feeding','No','') }}>
                    <label for="not_feeding_no">No</label>
                    <input id="not_feeding_yes" type="radio" name="not_feeding" value="Yes" {{ checked('not_feeding','Yes','') }}>
                    <label for="not_feeding_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Moves only when stimulated?</label>
                  <div class="segmented" role="group">
                    <!-- IMPORTANT: default is '' so it's not pre-selected unless 0_2m is chosen -->
                    <input id="stim_only_no" type="radio" name="stim_only" value="No" {{ checked('stim_only','No','') }}>
                    <label for="stim_only_no">No</label>
                    <input id="stim_only_yes" type="radio" name="stim_only" value="Yes" {{ checked('stim_only','Yes','') }}>
                    <label for="stim_only_yes">Yes</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>Malaria test (if available)</h3>
            <label for="rdt">RDT result</label>
            <select id="rdt" name="rdt" required>
              <option value="not_done" {{ selected('rdt','not_done','not_done') }}>Not done</option>
              <option value="negative" {{ selected('rdt','negative','not_done') }}>Negative</option>
              <option value="positive" {{ selected('rdt','positive','not_done') }}>Positive</option>
            </select>

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
        <section class="card" aria-label="Patient list">
          <h2>Patient list</h2>
          {% if patients|length == 0 %}
            <p class="muted">No patients yet.</p>
          {% else %}
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Village</th>
                  <th>Age</th>
                  <th class="nowrap">Actions</th>
                </tr>
              </thead>
              <tbody>
                {% for p in patients %}
                  <tr>
                    <td class="nowrap">
                      {{ p['name'] }}
                      {% if selected_patient and selected_patient['id'] == p['id'] %}
                        <span class="chip" style="margin-left:6px;">Selected</span>
                      {% endif %}
                    </td>
                    <td>{{ p['village'] or "-" }}</td>
                    <td class="nowrap">{{ p['age_group_label'] }}</td>
                    <td class="nowrap">
                      <a class="btn btn-secondary" style="padding:8px 10px; border-radius:12px; min-height:auto; flex:none;"
                         href="{{ url_for('index', patient_id=p['id'], ar=ar, aa=aa) }}">Select</a>

                      <form method="post" style="display:inline;" onsubmit="return confirm('Delete this patient and history?');">
                        <input type="hidden" name="action" value="delete_patient">
                        <input type="hidden" name="patient_id" value="{{ p['id'] }}">
                        <button class="btn btn-danger" style="padding:8px 10px; border-radius:12px; min-height:auto; flex:none;" type="submit">Delete</button>
                      </form>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
            <div class="hint">Select a patient to save screening history under them (optional).</div>
          {% endif %}

          {% if selected_patient %}
            <div class="divider"></div>
            <h3>Recent screenings (last 5)</h3>
            {% if history|length == 0 %}
              <p class="muted">No screenings for this patient yet.</p>
            {% else %}
              <table class="table">
                <thead>
                  <tr>
                    <th class="nowrap">Date</th>
                    <th>Risk</th>
                    <th>Top</th>
                    <th class="nowrap">Certainty</th>
                  </tr>
                </thead>
                <tbody>
                  {% for h in history %}
                    <tr>
                      <td class="nowrap">{{ h['created_at'] }}</td>
                      <td>{{ h['risk'] }}</td>
                      <td>{{ h['top_condition'] }}</td>
                      <td class="nowrap">{{ h['certainty'] }}%</td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            {% endif %}
          {% endif %}
        </section>

        <section class="card" aria-label="Analytics">
          <h2>Analytics (local)</h2>
          <p class="muted">Quick admin stats from saved screenings.</p>

          <form method="get">
            <input type="hidden" name="patient_id" value="{{ selected_patient['id'] if selected_patient else '' }}">
            <div class="row">
              <div>
                <label for="ar">Time range</label>
                <select id="ar" name="ar">
                  <option value="7"  {% if ar == '7' %}selected{% endif %}>Last 7 days</option>
                  <option value="30" {% if ar == '30' %}selected{% endif %}>Last 30 days</option>
                  <option value="all" {% if ar == 'all' %}selected{% endif %}>All time</option>
                </select>
              </div>
              <div>
                <label for="aa">Assessor filter</label>
                <select id="aa" name="aa">
                  <option value="" {% if aa == '' %}selected{% endif %}>All</option>
                  {% for n in assessor_names %}
                    <option value="{{ n }}" {% if aa == n %}selected{% endif %}>{{ n }}</option>
                  {% endfor %}
                </select>
              </div>
            </div>
            <div class="btn-row" style="margin-top:10px;">
              <button class="btn btn-secondary" type="submit" style="flex:1 1 220px;">Apply</button>
              <a class="btn btn-secondary" style="flex:1 1 220px;"
                 href="{{ url_for('index', patient_id=(selected_patient['id'] if selected_patient else None)) }}">Reset</a>
            </div>
          </form>

          <div class="divider"></div>

          <div class="pill-row">
            <span class="pill">Total: {{ analytics.total }}</span>
            <span class="pill">High: {{ analytics.risk_counts.get('High',0) }}</span>
            <span class="pill">Medium: {{ analytics.risk_counts.get('Medium',0) }}</span>
            <span class="pill">Low: {{ analytics.risk_counts.get('Low',0) }}</span>
          </div>

          <h3>Top conditions</h3>
          {% if analytics.top_conditions|length == 0 %}
            <p class="muted">No data yet.</p>
          {% else %}
            <ul>
              {% for name, cnt, pct in analytics.top_conditions %}
                <li>
                  <strong>{{ name }}</strong> — {{ cnt }} ({{ pct }}%)
                  <div class="mini-bar" aria-hidden="true" style="margin-top:6px;">
                    <div style="width: {{ pct }}%;"></div>
                  </div>
                </li>
              {% endfor %}
            </ul>
          {% endif %}

          <div class="divider"></div>

          <h3>Common danger signs (from forms)</h3>
          {% if analytics.danger_signs|length == 0 %}
            <p class="muted">No danger-sign data yet.</p>
          {% else %}
            <ul>
              {% for name, cnt in analytics.danger_signs %}
                <li>{{ name }} — {{ cnt }}</li>
              {% endfor %}
            </ul>
          {% endif %}

          <div class="divider"></div>

          <h3>Assessor performance</h3>
          {% if analytics.assessor_stats|length == 0 %}
            <p class="muted">No assessor data yet.</p>
          {% else %}
            <ul>
              {% for row in analytics.assessor_stats %}
                <li>
                  <strong>{{ row.name }}</strong> — {{ row.total }} screenings, High-risk: {{ row.high }} ({{ row.high_rate }}%)
                </li>
              {% endfor %}
            </ul>
          {% endif %}
        </section>

        <section class="card" aria-label="Quick guidance">
          <h2>Quick guidance</h2>
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
      try { document.execCommand('copy'); done(); }
      catch (e) { fail(); }
      window.getSelection().removeAllRanges();
    }

    function clearRadioGroup(name) {
      document.querySelectorAll(`input[name="${name}"]`).forEach(i => { i.checked = false; });
    }
    function setRadio(name, value) {
      const el = document.querySelector(`input[name="${name}"][value="${value}"]`);
      if (el) el.checked = true;
    }
    function setGroupDisabled(name, disabled) {
      document.querySelectorAll(`input[name="${name}"]`).forEach(i => { i.disabled = disabled; });
    }

    function syncYoungInfant() {
      const age = document.getElementById('age_group');
      const box = document.getElementById('young_infant');
      if (!age || !box) return;

      const show = age.value === '0_2m';
      box.classList.toggle('hidden', !show);

      // Disable so they aren't submitted when not relevant
      setGroupDisabled('not_feeding', !show);
      setGroupDisabled('stim_only', !show);

      if (!show) {
        // Not 0–2m => force deselect
        clearRadioGroup('not_feeding');
        clearRadioGroup('stim_only');
        return;
      }

      // 0–2m => if nothing selected yet, default to "No" (reduces taps)
      if (!document.querySelector('input[name="not_feeding"]:checked')) setRadio('not_feeding', 'No');
      if (!document.querySelector('input[name="stim_only"]:checked')) setRadio('stim_only', 'No');
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

# -------------------- DB --------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _has_column(conn, table: str, col: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == col for r in rows)

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

    # Base schema (we’ll migrate older DBs safely)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        created_at TEXT NOT NULL,
        risk TEXT NOT NULL,
        top_condition TEXT NOT NULL,
        certainty INTEGER NOT NULL,
        share_message TEXT NOT NULL,
        raw_answers TEXT NOT NULL,
        assessor TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
      )
    """)

    # Migrations for older dbs (fix your "no such column: assessor" crash)
    if not _has_column(conn, "screenings", "assessor"):
        conn.execute("ALTER TABLE screenings ADD COLUMN assessor TEXT")
    if not _has_column(conn, "screenings", "raw_answers"):
        conn.execute("ALTER TABLE screenings ADD COLUMN raw_answers TEXT NOT NULL DEFAULT '{}'")

    conn.commit()
    conn.close()

# -------------------- Helpers --------------------

def age_group_label(v: str) -> str:
    return {"0_2m": "0–2 months", "2_12m": "2–12 months", "1_5y": "1–5 years"}.get(v, v)

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

# -------------------- Screening logic --------------------

def compute_result(a: dict, selected_patient=None):
    # WhatsApp numbers (optional)
    wa_caregiver = digits_only(a.get("wa_caregiver", ""))
    wa_supervisor = digits_only(a.get("wa_supervisor", ""))

    include_name = (a.get("include_name", "No") == "Yes")
    include_village = (a.get("include_village", "No") == "Yes")

    assessor = (a.get("assessor") or "").strip()

    # Danger signs
    danger = any(a.get(k, "No") == "Yes" for k in ["ds_drink", "ds_vomit", "ds_convulsions", "ds_lethargy"])

    age = a.get("age_group", "1_5y")
    fever = (a.get("fever", "No") == "Yes")
    cough = (a.get("cough_breath", "No") == "Yes")

    rr = a.get("rr")
    rr = int(rr) if rr and str(rr).strip().isdigit() else None

    chest_indrawing = (a.get("chest_indrawing", "No") == "Yes")
    stridor = (a.get("stridor", "No") == "Yes")

    muac = a.get("muac", "not_measured")
    oedema = (a.get("oedema", "No") == "Yes")

    # IMPORTANT: default to "No" if not present (because we disable them when age != 0_2m)
    not_feeding = (a.get("not_feeding", "No") == "Yes")
    stim_only = (a.get("stim_only", "No") == "Yes")

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
        if age == "2_12m" and rr >= 50: fast_breathing = True
        if age == "1_5y" and rr >= 40: fast_breathing = True
        if age == "0_2m" and rr >= 60: fast_breathing = True

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
    alt_text = ", ".join([f"{n} {pct}%" for n, pct in alternatives if n])

    share_lines = ["Toto Gemma — Under-5 screening result"]

    # Optional identifiers
    if selected_patient and include_name:
        share_lines.append(f"Patient: {selected_patient['name']}")
    if selected_patient and include_village and selected_patient.get("village"):
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
        "assessor": assessor,
        "raw_answers": a,
    }

# -------------------- Analytics --------------------

def compute_analytics(conn, ar: str, aa: str):
    # ar: '7' | '30' | 'all'
    where = []
    params = []

    if ar in ("7", "30"):
        days = int(ar)
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
        where.append("created_at >= ?")
        params.append(start)

    if aa:
        where.append("assessor = ?")
        params.append(aa)

    sql = "SELECT risk, top_condition, raw_answers, assessor FROM screenings"
    if where:
        sql += " WHERE " + " AND ".join(where)

    rows = conn.execute(sql, params).fetchall()

    total = len(rows)
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    cond_counts = {}
    danger_counts = {
        "Not able to drink/breastfeed": 0,
        "Vomits everything": 0,
        "Convulsions": 0,
        "Very sleepy/unconscious": 0,
    }
    assessor_rollup = {}

    for r in rows:
        risk = r["risk"]
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

        cond = r["top_condition"]
        cond_counts[cond] = cond_counts.get(cond, 0) + 1

        assessor = (r["assessor"] or "").strip()
        if assessor:
            if assessor not in assessor_rollup:
                assessor_rollup[assessor] = {"total": 0, "high": 0}
            assessor_rollup[assessor]["total"] += 1
            if risk == "High":
                assessor_rollup[assessor]["high"] += 1

        # danger signs from raw_answers
        try:
            a = json.loads(r["raw_answers"] or "{}")
        except Exception:
            a = {}
        if a.get("ds_drink") == "Yes":
            danger_counts["Not able to drink/breastfeed"] += 1
        if a.get("ds_vomit") == "Yes":
            danger_counts["Vomits everything"] += 1
        if a.get("ds_convulsions") == "Yes":
            danger_counts["Convulsions"] += 1
        if a.get("ds_lethargy") == "Yes":
            danger_counts["Very sleepy/unconscious"] += 1

    # top conditions
    top_conditions = sorted(cond_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_conditions_fmt = []
    for name, cnt in top_conditions:
        pct = int(round((cnt / total) * 100)) if total else 0
        top_conditions_fmt.append((name, cnt, pct))

    danger_sorted = sorted(danger_counts.items(), key=lambda x: x[1], reverse=True)
    danger_sorted = [(k, v) for k, v in danger_sorted if v > 0][:4]

    assessor_stats = []
    for name, d in sorted(assessor_rollup.items(), key=lambda x: x[1]["total"], reverse=True):
        total_a = d["total"]
        high_a = d["high"]
        rate = int(round((high_a / total_a) * 100)) if total_a else 0
        assessor_stats.append(type("Row", (), {"name": name, "total": total_a, "high": high_a, "high_rate": rate}))

    return {
        "total": total,
        "risk_counts": risk_counts,
        "top_conditions": top_conditions_fmt,
        "danger_signs": danger_sorted,
        "assessor_stats": assessor_stats,
    }

# -------------------- Routes --------------------

@app.route("/", methods=["GET", "POST"])
def index():
    init_db()

    patient_id = (request.args.get("patient_id") or "").strip()

    # analytics params (GET)
    ar = (request.args.get("ar") or "30").strip()   # 7, 30, all
    aa = (request.args.get("aa") or "").strip()     # assessor name

    message = None
    result = None
    form_data = {}

    conn = get_conn()

    # POST actions
    if request.method == "POST":
        action = request.form.get("action", "")
        form_data = request.form.to_dict()

        if action == "add_patient":
            name = (request.form.get("p_name") or "").strip()
            village = (request.form.get("p_village") or "").strip()
            age_group = request.form.get("p_age_group", "1_5y")

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
                return redirect(url_for("index", patient_id=new_id, ar=ar, aa=aa))

        elif action == "delete_patient":
            del_id = (request.form.get("patient_id") or "").strip()
            if del_id.isdigit():
                conn.execute("DELETE FROM screenings WHERE patient_id = ?", (int(del_id),))
                conn.execute("DELETE FROM patients WHERE id = ?", (int(del_id),))
                conn.commit()
                if patient_id == del_id:
                    conn.close()
                    return redirect(url_for("index", ar=ar, aa=aa))
            else:
                message = "Invalid patient id."

        elif action == "run_screening":
            # load selected patient
            selected_patient = None
            if patient_id.isdigit():
                row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
                if row:
                    selected_patient = dict(row)

            # compute result
            result = compute_result(form_data, selected_patient=selected_patient)

            # save screening
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            pid_to_save = int(patient_id) if patient_id.isdigit() else None

            conn.execute(
                """INSERT INTO screenings
                   (patient_id, created_at, risk, top_condition, certainty, share_message, raw_answers, assessor)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    pid_to_save,
                    now,
                    result["risk"],
                    result["top_condition"],
                    int(result["certainty"]),
                    result["share_message"],
                    json.dumps(result["raw_answers"], ensure_ascii=False),
                    result["assessor"],
                ),
            )
            conn.commit()

    # load patients
    patients_rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    patients = []
    for r in patients_rows:
        d = dict(r)
        d["age_group_label"] = age_group_label(d["age_group"])
        patients.append(d)

    # selected patient + default age group
    selected_patient = None
    default_age_group = "1_5y"
    if patient_id.isdigit():
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
        if row:
            selected_patient = dict(row)
            default_age_group = selected_patient["age_group"]

    # patient history
    history = []
    if selected_patient:
        rows = conn.execute(
            "SELECT created_at, risk, top_condition, certainty FROM screenings WHERE patient_id = ? ORDER BY id DESC LIMIT 5",
            (int(patient_id),),
        ).fetchall()
        history = [dict(x) for x in rows]

    # assessor list (for analytics dropdown)
    try:
        assessor_rows = conn.execute(
            "SELECT DISTINCT assessor FROM screenings WHERE assessor IS NOT NULL AND assessor != '' ORDER BY assessor ASC"
        ).fetchall()
        assessor_names = [r["assessor"] for r in assessor_rows]
    except sqlite3.OperationalError:
        assessor_names = []

    analytics = compute_analytics(conn, ar=ar, aa=aa)

    conn.close()

    return render_template_string(
        HTML,
        result=result,
        form=form_data,
        message=message,
        patients=patients,
        selected_patient=selected_patient,
        history=history,
        default_age_group=default_age_group,
        analytics=analytics,
        assessor_names=assessor_names,
        ar=ar,
        aa=aa,
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
