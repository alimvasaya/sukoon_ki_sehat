# app.py
from flask import Flask, render_template_string, request, redirect, url_for
import math
import re
import sqlite3
import json
from urllib.parse import quote
from datetime import datetime

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
    .container { max-width: 1060px; margin: 0 auto; padding: 18px 14px 28px; }
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
    @media (min-width: 920px) {
      .grid { grid-template-columns: 1.1fr 0.9fr; align-items: start; }
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
    }

    .danger { border-color: rgba(255,92,119,0.35); background: linear-gradient(180deg, rgba(255,92,119,0.16), rgba(255,255,255,0.06)); }
    .warn   { border-color: rgba(255,207,90,0.35);  background: linear-gradient(180deg, rgba(255,207,90,0.16), rgba(255,255,255,0.06)); }
    .ok     { border-color: rgba(47,208,124,0.35);  background: linear-gradient(180deg, rgba(47,208,124,0.16), rgba(255,255,255,0.06)); }

    form { margin: 0; }
    label { display:block; margin: 10px 0 6px; font-weight: 800; }

    .row { display: grid; grid-template-columns: 1fr; gap: 10px; }
    @media (min-width: 700px) { .row { grid-template-columns: 1fr 1fr; } }

    .row3 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  align-items: end; /* <-- this fixes the misaligned inputs */
}
@media (min-width: 820px) {
  .row3 {
    grid-template-columns: 1fr 1fr 1fr;
    align-items: end; /* keep it on the 3-col layout too */
  }
}


    input[type="number"], input[type="text"], input[type="tel"], select, textarea {
      width: 100%;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      outline: none;
    }

    /* dropdown options visibility on dark themes */
    select { color-scheme: light; }
    select option { background: #ffffff; color: #111111; }

    textarea { min-height: 132px; resize: vertical; }

    select {
      appearance: none;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 18px) calc(1em + 2px),
        calc(100% - 13px) calc(1em + 2px);
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

    /* segmented alignment */
    .segmented {
      display: grid;
      grid-template-columns: 1fr 1fr;
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
      background: rgba(255,255,255,0.04);
    }
    .segmented input { position: absolute; opacity: 0; pointer-events: none; }
    .segmented label {
      margin: 0;
      padding: 12px 12px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      user-select: none;
      min-height: 46px;
    }
    .segmented label:hover { background: rgba(255,255,255,0.06); }
    .segmented label:first-of-type { border-right: 1px solid var(--border); }
    .segmented input:checked + label {
      background: rgba(124,108,255,0.22);
      box-shadow: inset 0 0 0 1px rgba(124,108,255,0.35);
    }
    .segmented input:focus-visible + label { outline: 3px solid rgba(124,108,255,0.45); outline-offset: -3px; }

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
      min-height: 46px;
      transition: transform 0.05s ease, filter 0.15s ease, background 0.15s ease;
      flex: 1 1 220px;
    }
    .btn:active { transform: translateY(1px); }
    .btn-primary { background: var(--accent); color: #fff; }
    .btn-secondary { background: rgba(255,255,255,0.08); border-color: var(--border); color: var(--text); }
    .btn-danger { background: rgba(255,92,119,0.22); border-color: rgba(255,92,119,0.30); color: var(--text); }
    .btn-whatsapp { background: #25D366; color: #fff; }
    .btn:focus-visible { outline: 3px solid rgba(124,108,255,0.55); outline-offset: 3px; }
    .btn svg { width: 18px; height: 18px; }

    .sticky-actions { position: sticky; bottom: 10px; margin-top: 14px; z-index: 3; }
    .hidden { display: none !important; }
    ul { margin: 8px 0 0 18px; }
    li { margin: 6px 0; }

    .table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    .table th, .table td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      font-size: 0.95rem;
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
      font-size: 0.85rem;
      margin-left: 8px;
    }
    .chip-dot {
      width: 9px; height: 9px; border-radius: 50%;
      background: var(--accent2);
      box-shadow: 0 0 0 3px rgba(32,201,151,0.18);
    }
  </style>
</head>
<body>
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

    <div class="grid">
      <main>

        {% if message %}
          <section class="card warn" aria-label="Message">
            <strong>{{ message }}</strong>
          </section>
        {% endif %}

        <!-- LEFT: Add patient only -->
        <section class="card" aria-label="Add patient">
          <h2>Patients (local only)</h2>
          <p class="muted">This saves on the device (SQLite). Keep info minimal.</p>

          <h3>Add patient</h3>
          <form method="post" action="{{ url_for('index', patient_id=(selected_patient['id'] if selected_patient else None)) }}">
            <input type="hidden" name="action" value="add_patient">

            <label for="p_name">Name / nickname</label>
            <input id="p_name" type="text" name="p_name" required placeholder="e.g., Amina">

            <label for="p_village">Village (optional)</label>
            <input id="p_village" type="text" name="p_village" placeholder="e.g., Kibera">

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
              <a class="btn btn-secondary" href="#screen" aria-label="Go to screening form">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M12 19V5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M6 11L12 5l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Back to form
              </a>
            </div>
          </section>

          <section class="card" aria-label="Share via WhatsApp">
            <h2>Share via WhatsApp</h2>
            <p class="muted">
              This does not auto-send. It opens WhatsApp with a pre-filled summary. Review, then tap Send.
            </p>

            <label for="shareText">Message to share</label>
            <textarea id="shareText" readonly>{{ result.share_message }}</textarea>

            <div class="btn-row">
              <a class="btn btn-whatsapp" href="{{ result.wa_caregiver_url }}" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M20 12a8 8 0 0 1-11.82 6.94L4 20l1.12-4.06A8 8 0 1 1 20 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Share to caregiver
              </a>
              <a class="btn btn-whatsapp" href="{{ result.wa_supervisor_url }}" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M20 12a8 8 0 0 1-11.82 6.94L4 20l1.12-4.06A8 8 0 1 1 20 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Share to supervisor
              </a>
              <button class="btn btn-secondary" type="button" onclick="copyShareText()">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M9 9h10v10H9V9Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                  <path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                Copy summary
              </button>
            </div>

            <p id="copyStatus" class="muted" style="margin-top:10px;"></p>
          </section>
        {% endif %}

        <section id="screen" class="card" aria-label="Under-5 screening form">
          <h2>Screening form</h2>
          <p class="muted">Answer the questions below. Defaults are set to reduce taps; change anything that applies.</p>

          <form method="post" novalidate>
            <input type="hidden" name="action" value="run_screening">

            <div class="row3">
              <div>
                <label for="age_group">Age group</label>
                <select id="age_group" name="age_group" required>
                  <option value="0_2m" {{ 'selected' if default_age_group=='0_2m' else '' }}>0–2 months</option>
                  <option value="2_12m" {{ 'selected' if default_age_group=='2_12m' else '' }}>2–12 months</option>
                  <option value="1_5y" {{ 'selected' if default_age_group=='1_5y' else '' }}>1–5 years</option>
                </select>
              </div>
              <div>
                <label for="wa_caregiver">Caregiver WhatsApp (optional)</label>
                <input id="wa_caregiver" type="tel" name="wa_caregiver" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_caregiver','') }}"
                       placeholder="Digits only, include country code">
              </div>
              <div>
                <label for="wa_supervisor">Supervisor WhatsApp (optional)</label>
                <input id="wa_supervisor" type="tel" name="wa_supervisor" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_supervisor','') }}"
                       placeholder="Digits only, include country code">
              </div>
            </div>

            <div class="row" style="margin-top:10px;">
              <div>
                <label>Include patient name in WhatsApp message?</label>
                <div class="segmented" role="group" aria-label="Include patient name">
                  <input id="include_name_no" type="radio" name="include_name" value="No" {{ checked('include_name','No','No') }}>
                  <label for="include_name_no">No</label>
                  <input id="include_name_yes" type="radio" name="include_name" value="Yes" {{ checked('include_name','Yes','No') }}>
                  <label for="include_name_yes">Yes</label>
                </div>
              </div>
              <div>
                <label>Include village in WhatsApp message?</label>
                <div class="segmented" role="group" aria-label="Include village">
                  <input id="include_village_no" type="radio" name="include_village" value="No" {{ checked('include_village','No','No') }}>
                  <label for="include_village_no">No</label>
                  <input id="include_village_yes" type="radio" name="include_village" value="Yes" {{ checked('include_village','Yes','No') }}>
                  <label for="include_village_yes">Yes</label>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <div class="card warn" aria-label="Danger signs">
              <h3>Danger signs</h3>
              <p class="muted">If any are Yes, refer urgently.</p>

              <div class="row">
                <div>
                  <label>Not able to drink/breastfeed?</label>
                  <div class="segmented" role="group" aria-label="Not able to drink or breastfeed">
                    <input id="ds_drink_no" type="radio" name="ds_drink" value="No" {{ checked('ds_drink','No','No') }}>
                    <label for="ds_drink_no">No</label>
                    <input id="ds_drink_yes" type="radio" name="ds_drink" value="Yes" {{ checked('ds_drink','Yes','No') }}>
                    <label for="ds_drink_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Vomits everything?</label>
                  <div class="segmented" role="group" aria-label="Vomits everything">
                    <input id="ds_vomit_no" type="radio" name="ds_vomit" value="No" {{ checked('ds_vomit','No','No') }}>
                    <label for="ds_vomit_no">No</label>
                    <input id="ds_vomit_yes" type="radio" name="ds_vomit" value="Yes" {{ checked('ds_vomit','Yes','No') }}>
                    <label for="ds_vomit_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Convulsions?</label>
                  <div class="segmented" role="group" aria-label="Convulsions">
                    <input id="ds_convulsions_no" type="radio" name="ds_convulsions" value="No" {{ checked('ds_convulsions','No','No') }}>
                    <label for="ds_convulsions_no">No</label>
                    <input id="ds_convulsions_yes" type="radio" name="ds_convulsions" value="Yes" {{ checked('ds_convulsions','Yes','No') }}>
                    <label for="ds_convulsions_yes">Yes</label>
                  </div>
                </div>
                <div>
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
              <div>
                <label>Fever now or in last 2 days?</label>
                <div class="segmented" role="group" aria-label="Fever">
                  <input id="fever_no" type="radio" name="fever" value="No" {{ checked('fever','No','No') }}>
                  <label for="fever_no">No</label>
                  <input id="fever_yes" type="radio" name="fever" value="Yes" {{ checked('fever','Yes','No') }}>
                  <label for="fever_yes">Yes</label>
                </div>
              </div>
              <div>
                <label>Cough or difficult breathing?</label>
                <div class="segmented" role="group" aria-label="Cough or difficult breathing">
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
                <div class="segmented" role="group" aria-label="Chest indrawing">
                  <input id="chest_indrawing_no" type="radio" name="chest_indrawing" value="No" {{ checked('chest_indrawing','No','No') }}>
                  <label for="chest_indrawing_no">No</label>
                  <input id="chest_indrawing_yes" type="radio" name="chest_indrawing" value="Yes" {{ checked('chest_indrawing','Yes','No') }}>
                  <label for="chest_indrawing_yes">Yes</label>
                </div>
              </div>
              <div>
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
              <div>
                <label for="muac">MUAC color (6–59 months)</label>
                <select id="muac" name="muac" required>
                  <option value="not_measured">Not measured</option>
                  <option value="green">Green</option>
                  <option value="yellow">Yellow</option>
                  <option value="red">Red</option>
                </select>
              </div>
              <div>
                <label>Swelling on both feet?</label>
                <div class="segmented" role="group" aria-label="Swelling on both feet">
                  <input id="oedema_no" type="radio" name="oedema" value="No" checked>
                  <label for="oedema_no">No</label>
                  <input id="oedema_yes" type="radio" name="oedema" value="Yes">
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
                  <div class="segmented" role="group" aria-label="Not feeding well">
                    <input id="not_feeding_no" type="radio" name="not_feeding" value="No" checked>
                    <label for="not_feeding_no">No</label>
                    <input id="not_feeding_yes" type="radio" name="not_feeding" value="Yes">
                    <label for="not_feeding_yes">Yes</label>
                  </div>
                </div>
                <div>
                  <label>Moves only when stimulated?</label>
                  <div class="segmented" role="group" aria-label="Moves only when stimulated">
                    <input id="stim_only_no" type="radio" name="stim_only" value="No" checked>
                    <label for="stim_only_no">No</label>
                    <input id="stim_only_yes" type="radio" name="stim_only" value="Yes">
                    <label for="stim_only_yes">Yes</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>Malaria test (if available)</h3>
            <label for="rdt">RDT result</label>
            <select id="rdt" name="rdt" required>
              <option value="not_done" selected>Not done</option>
              <option value="negative">Negative</option>
              <option value="positive">Positive</option>
            </select>

            <div class="sticky-actions">
              <div class="btn-row">
                <button class="btn btn-primary" type="submit">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Get result
                </button>
                <button class="btn btn-secondary" type="reset">Reset</button>
              </div>
            </div>
          </form>
        </section>
      </main>

      <aside>
        <!-- RIGHT: Patient list moved into the right column -->
        <section class="card" aria-label="Patient list">
          <h2>Patient list</h2>

          {% if patients|length == 0 %}
            <p class="muted">No patients yet.</p>
            <div class="divider"></div>
            <p class="muted">Select a patient if you want to save screening history (optional).</p>
          {% else %}
            <table class="table" aria-label="Patient list table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th class="nowrap">Default</th>
                  <th class="nowrap">Actions</th>
                </tr>
              </thead>
              <tbody>
                {% for p in patients %}
                  <tr>
                    <td>
                      {{ p['name'] }}
                      {% if selected_patient and selected_patient['id'] == p['id'] %}
                        <span class="chip"><span class="chip-dot"></span>Selected</span>
                      {% endif %}
                      {% if p['village'] %}
                        <div class="muted" style="margin-top:4px;">{{ p['village'] }}</div>
                      {% endif %}
                    </td>
                    <td class="nowrap">{{ p['age_group_label'] }}</td>
                    <td class="nowrap">
                      <a class="btn btn-secondary"
                         style="padding:10px 12px; min-height:0; flex:0 0 auto;"
                         href="{{ url_for('index', patient_id=p['id']) }}">Select</a>

                      <form method="post"
                            action="{{ url_for('index', patient_id=(selected_patient['id'] if selected_patient else None)) }}"
                            style="display:inline;"
                            onsubmit="return confirm('Delete this patient and history?');">
                        <input type="hidden" name="action" value="delete_patient">
                        <input type="hidden" name="patient_id" value="{{ p['id'] }}">
                        <button class="btn btn-danger"
                                style="padding:10px 12px; min-height:0; flex:0 0 auto;"
                                type="submit">Delete</button>
                      </form>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>

            <div class="divider"></div>

            {% if selected_patient %}
              <p class="muted" style="margin:0 0 8px;">
                Current: <strong>{{ selected_patient['name'] }}</strong>
                {% if selected_patient.get('village') %} — {{ selected_patient['village'] }}{% endif %}
              </p>

              <h3 style="margin:10px 0 8px;">Recent screenings (last 5)</h3>
              {% if history|length == 0 %}
                <p class="muted">No screenings for this patient yet.</p>
              {% else %}
                <table class="table" aria-label="Recent screenings">
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
            {% else %}
              <p class="muted">Select a patient if you want to save screening history (optional).</p>
            {% endif %}
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

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

def compute_result(a: dict, selected_patient=None):
    wa_caregiver = digits_only(a.get("wa_caregiver", ""))
    wa_supervisor = digits_only(a.get("wa_supervisor", ""))

    include_name = (a.get("include_name", "No") == "Yes")
    include_village = (a.get("include_village", "No") == "Yes")

    danger = any(a.get(k, "No") == "Yes" for k in ["ds_drink", "ds_vomit", "ds_convulsions", "ds_lethargy"])

    age = a.get("age_group", "0_2m")
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

    if selected_patient and include_name:
        share_lines.append(f"Patient: {selected_patient['name']}")
    if selected_patient and include_village and (selected_patient.get("village") or "").strip():
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

    wa_caregiver_url = make_whatsapp_link(share_message, wa_caregiver)
    wa_supervisor_url = make_whatsapp_link(share_message, wa_supervisor)

    return {
        "risk": risk,
        "top_condition": top_name,
        "certainty": certainty,
        "alternatives": alternatives,
        "actions": actions,
        "tips": tips,
        "box_class": box_class,
        "share_message": share_message,
        "wa_caregiver_url": wa_caregiver_url,
        "wa_supervisor_url": wa_supervisor_url,
        "raw_answers": a,
    }

@app.route("/", methods=["GET", "POST"])
def index():
    init_db()
    conn = get_conn()

    patient_id = (request.args.get("patient_id") or "").strip()
    message = None
    result = None
    form_data = {}

    if request.method == "POST":
        action = request.form.get("action", "")

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
                return redirect(url_for("index", patient_id=new_id))

        elif action == "delete_patient":
            del_id = (request.form.get("patient_id") or "").strip()
            if del_id.isdigit():
                conn.execute("DELETE FROM screenings WHERE patient_id = ?", (int(del_id),))
                conn.execute("DELETE FROM patients WHERE id = ?", (int(del_id),))
                conn.commit()
                conn.close()
                if patient_id == del_id:
                    return redirect(url_for("index"))
                return redirect(url_for("index", patient_id=patient_id if patient_id.isdigit() else None))
            else:
                message = "Invalid patient id."

        elif action == "run_screening":
            form_data = request.form.to_dict()

            selected_patient = None
            if patient_id.isdigit():
                row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
                if row:
                    selected_patient = dict(row)

            result = compute_result(form_data, selected_patient=selected_patient)

            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            pid_to_save = int(patient_id) if patient_id.isdigit() else None

            conn.execute(
                """INSERT INTO screenings
                   (patient_id, created_at, risk, top_condition, certainty, share_message, raw_answers)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    pid_to_save,
                    now,
                    result["risk"],
                    result["top_condition"],
                    int(result["certainty"]),
                    result["share_message"],
                    json.dumps(result["raw_answers"], ensure_ascii=False),
                ),
            )
            conn.commit()

    patients_rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    patients = []
    for r in patients_rows:
        d = dict(r)
        d["age_group_label"] = age_group_label(d["age_group"])
        patients.append(d)

    selected_patient = None
    default_age_group = "0_2m"
    history = []

    if patient_id.isdigit():
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
        if row:
            selected_patient = dict(row)
            selected_patient["age_group_label"] = age_group_label(selected_patient["age_group"])
            default_age_group = selected_patient["age_group"]
            rows = conn.execute(
                "SELECT created_at, risk, top_condition, certainty FROM screenings WHERE patient_id = ? ORDER BY id DESC LIMIT 5",
                (int(patient_id),),
            ).fetchall()
            history = [dict(x) for x in rows]

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
    )

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
