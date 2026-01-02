# app.py
from flask import Flask, render_template_string, request
import math

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Toto Gemma - Under-5 Screening</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 16px; max-width: 760px; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 14px; margin: 12px 0; }
    label { display:block; margin: 8px 0 4px; font-weight: 600; }
    input[type="number"], select { width: 100%; padding: 10px; border-radius: 10px; border: 1px solid #ccc; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .btn { padding: 12px 14px; border: 0; border-radius: 10px; font-weight: 700; cursor: pointer; }
    .btn-primary { background: #111; color: #fff; width: 100%; }
    .pill { display:inline-block; padding: 6px 10px; border-radius: 999px; background: #f4f4f4; margin-right: 8px; font-weight: 700; }
    .warn { background: #fff3cd; border: 1px solid #ffe69c; }
    .danger { background: #f8d7da; border: 1px solid #f1aeb5; }
    .ok { background: #d1e7dd; border: 1px solid #a3cfbb; }
    small { color:#555; }
  </style>
</head>
<body>
  <h1>Toto Gemma (Offline) — Under-5 Screening</h1>
  <p><small>This tool is for screening and coaching. It does not replace clinical care. If danger signs are present, refer urgently.</small></p>

  {% if result %}
    <div class="card {{ result.box_class }}">
      <div>
        <span class="pill">Risk: {{ result.risk }}</span>
        <span class="pill">Top: {{ result.top_condition }}</span>
        <span class="pill">Certainty: {{ result.certainty }}%</span>
      </div>
      <h3>What to do now</h3>
      <ul>
        {% for s in result.actions %}
          <li>{{ s }}</li>
        {% endfor %}
      </ul>

      <h3>Coaching tips for caregiver</h3>
      <ul>
        {% for s in result.tips %}
          <li>{{ s }}</li>
        {% endfor %}
      </ul>

      <h3>Also consider</h3>
      <ul>
        {% for name, pct in result.alternatives %}
          <li>{{ name }} — {{ pct }}%</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

  <form method="post" class="card">
    <h2>Child basics</h2>
    <label>Age group</label>
    <select name="age_group" required>
      <option value="0_2m">0–2 months</option>
      <option value="2_12m">2–12 months</option>
      <option value="1_5y">1–5 years</option>
    </select>

    <div class="card warn">
      <h3>Danger signs (tap Yes/No)</h3>
      <div class="row">
        <div>
          <label>Not able to drink/breastfeed?</label>
          <select name="ds_drink" required><option>No</option><option>Yes</option></select>
        </div>
        <div>
          <label>Vomits everything?</label>
          <select name="ds_vomit" required><option>No</option><option>Yes</option></select>
        </div>
        <div>
          <label>Convulsions?</label>
          <select name="ds_convulsions" required><option>No</option><option>Yes</option></select>
        </div>
        <div>
          <label>Very sleepy/unconscious?</label>
          <select name="ds_lethargy" required><option>No</option><option>Yes</option></select>
        </div>
      </div>
    </div>

    <h2>Main symptoms</h2>
    <div class="row">
      <div>
        <label>Fever now or in last 2 days?</label>
        <select name="fever" required><option>No</option><option>Yes</option></select>
      </div>
      <div>
        <label>Cough or difficult breathing?</label>
        <select name="cough_breath" required><option>No</option><option>Yes</option></select>
      </div>
    </div>

    <label>Breaths per minute (optional but recommended)</label>
    <input type="number" name="rr" min="0" max="120" placeholder="e.g., 48">

    <div class="row">
      <div>
        <label>Chest indrawing?</label>
        <select name="chest_indrawing" required><option>No</option><option>Yes</option></select>
      </div>
      <div>
        <label>Stridor (noisy breathing when calm)?</label>
        <select name="stridor" required><option>No</option><option>Yes</option></select>
      </div>
    </div>

    <h2>Nutrition</h2>
    <div class="row">
      <div>
        <label>MUAC color (6–59 months)</label>
        <select name="muac" required>
          <option value="not_measured">Not measured</option>
          <option value="green">Green</option>
          <option value="yellow">Yellow</option>
          <option value="red">Red</option>
        </select>
      </div>
      <div>
        <label>Swelling on both feet?</label>
        <select name="oedema" required><option>No</option><option>Yes</option></select>
      </div>
    </div>

    <h2>Young infant add-on (only matters if age 0–2 months)</h2>
    <div class="row">
      <div>
        <label>Not feeding well?</label>
        <select name="not_feeding" required><option>No</option><option>Yes</option></select>
      </div>
      <div>
        <label>Moves only when stimulated?</label>
        <select name="stim_only" required><option>No</option><option>Yes</option></select>
      </div>
    </div>

    <h2>Malaria test (if available)</h2>
    <label>RDT result</label>
    <select name="rdt" required>
      <option value="not_done">Not done</option>
      <option value="negative">Negative</option>
      <option value="positive">Positive</option>
    </select>

    <button class="btn btn-primary" type="submit">Get result</button>
  </form>
</body>
</html>
"""

def softmax(scores: dict) -> dict:
    # Stable softmax
    m = max(scores.values())
    exps = {k: math.exp(v - m) for k, v in scores.items()}
    s = sum(exps.values())
    return {k: (exps[k] / s if s else 0.25) for k in scores}

def compute_result(a: dict):
    # Danger signs (IMCI override)
    danger = any(a[k] == "Yes" for k in ["ds_drink","ds_vomit","ds_convulsions","ds_lethargy"])

    age = a["age_group"]
    fever = (a["fever"] == "Yes")
    cough = (a["cough_breath"] == "Yes")
    rr = a.get("rr")
    rr = int(rr) if rr and str(rr).strip().isdigit() else None
    chest_indrawing = (a["chest_indrawing"] == "Yes")
    stridor = (a["stridor"] == "Yes")

    muac = a["muac"]
    oedema = (a["oedema"] == "Yes")

    not_feeding = (a["not_feeding"] == "Yes")
    stim_only = (a["stim_only"] == "Yes")

    rdt = a["rdt"]  # not_done / negative / positive

    # Initialize scores
    scores = {
        "Pneumonia": 0.0,
        "Malaria": 0.0,
        "Malnutrition": 0.0,
        "Neonatal complications": 0.0,  # sick young infant serious illness proxy
    }

    # Age gating: neonatal only meaningful in 0–2 months
    if age == "0_2m":
        scores["Neonatal complications"] += 2.0

    # Fever drives malaria + neonatal
    if fever:
        scores["Malaria"] += 2.5
        if age == "0_2m":
            scores["Neonatal complications"] += 2.0

    # Cough/difficult breathing drives pneumonia
    if cough:
        scores["Pneumonia"] += 2.5

    # Fast breathing thresholds (IMCI)
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

    # Malaria test is a strong discriminator
    if rdt == "positive":
        scores["Malaria"] += 6.0
    elif rdt == "negative":
        scores["Malaria"] -= 3.0

    # Nutrition scoring (MUAC + oedema)
    if oedema:
        scores["Malnutrition"] += 7.0
    if muac == "red":
        scores["Malnutrition"] += 6.0
    elif muac == "yellow":
        scores["Malnutrition"] += 3.0
    elif muac == "green":
        scores["Malnutrition"] += 0.0

    # Young infant signs
    if age == "0_2m":
        if not_feeding:
            scores["Neonatal complications"] += 3.5
        if stim_only:
            scores["Neonatal complications"] += 3.5

    # Risk tier logic (simple + safe)
    high_triggers = []
    if danger:
        high_triggers.append("General danger sign present")

    if oedema or muac == "red":
        high_triggers.append("Severe acute malnutrition signs")

    # Severe respiratory signs
    if (cough and (chest_indrawing or stridor)) or (cough and fast_breathing and age == "0_2m"):
        high_triggers.append("Severe breathing problem signs")

    # Young infant severe illness signs
    if age == "0_2m" and (not_feeding or stim_only or fast_breathing or chest_indrawing or fever):
        high_triggers.append("Young infant severe illness signs")

    probs = softmax(scores)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    top_name, top_p = sorted_probs[0]
    alternatives = [(n, int(round(p*100))) for n,p in sorted_probs[1:3]]

    certainty = int(round(top_p * 100))

    # Choose risk
    if high_triggers:
        risk = "High"
        box_class = "danger"
    elif certainty >= 80:
        risk = "Medium"
        box_class = "warn"
    else:
        risk = "Low"
        box_class = "ok"

    # Actions + tips (no dosing; refer to protocol)
    actions = []
    tips = []

    if risk == "High":
        actions.append("Refer urgently to the nearest health facility now.")
        actions.append("Keep the child warm and continue breastfeeding/feeding if able.")
        if rdt == "positive":
            actions.append("If trained and stocked, follow local malaria protocol for confirmed malaria; otherwise refer.")
        if muac in ("red",) or oedema:
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

    # Coaching tips (plain language)
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
    else:  # Neonatal
        tips += [
            "Keep the baby warm (skin-to-skin if possible).",
            "Breastfeed frequently if the baby can feed.",
            "If feeding is poor, fever/low temperature, or low movement—go urgently.",
        ]

    return {
        "risk": risk,
        "top_condition": top_name,
        "certainty": certainty,
        "alternatives": alternatives,
        "actions": actions,
        "tips": tips,
        "box_class": box_class,
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        result = compute_result(request.form.to_dict())
    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    # Runs offline on local network / device
    app.run(host="0.0.0.0", port=5000, debug=False)
