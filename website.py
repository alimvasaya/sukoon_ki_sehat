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

# -------------------- i18n (local) --------------------

TRANSLATIONS = {
    "en": {
        "app_title": "Toto Gemma — Under-5 Screening",
        "app_subtitle": "Screening + coaching only. If any danger sign is present, refer urgently.",
        "local_storage": "Local storage (SQLite)",
        "language": "Language",
        "translate": "Translate",
        "english": "English",
        "swahili": "Kiswahili",
        "hindi": "हिंदी",

        "add_patient_title": "Add patient (local only)",
        "add_patient_hint": "Saves only on this device. Keep info minimal.",
        "name_nickname": "Name / nickname",
        "village_optional": "Village (optional)",
        "default_age_group": "Default age group",
        "add_patient_btn": "Add patient",

        "patient_list": "Patient list",
        "no_patients": "No patients yet.",
        "select": "Select",
        "delete": "Delete",
        "select_hint": "Select a patient to save screening history under them (optional).",
        "recent_screenings": "Recent screenings (last 5)",
        "no_screenings": "No screenings for this patient yet.",

        "screening_form": "Screening form",
        "screening_hint": "Answer what applies. If you selected a patient on the right, screenings save under them.",
        "current_patient": "Current patient: {name}{village}",
        "age_group": "Age group",
        "caregiver_wa": "Caregiver WhatsApp (optional)",
        "supervisor_wa": "Supervisor WhatsApp (optional)",
        "digits_only": "Digits only, include country code",
        "assessor": "Assessor / CHW name (optional)",
        "include_patient_name": "Include patient name in WhatsApp?",
        "include_village": "Include village in WhatsApp?",
        "only_used_if_patient": "Only used if a patient is selected.",
        "no": "No",
        "yes": "Yes",

        "danger_signs": "Danger signs",
        "danger_signs_hint": "If any are Yes, refer urgently.",
        "ds_drink": "Not able to drink/breastfeed?",
        "ds_vomit": "Vomits everything?",
        "ds_convulsions": "Convulsions?",
        "ds_lethargy": "Very sleepy/unconscious?",

        "main_symptoms": "Main symptoms",
        "fever": "Fever now or in last 2 days?",
        "cough_breath": "Cough or difficult breathing?",
        "rr": "Breaths per minute (optional)",
        "rr_hint": "Tip: count breaths for 60 seconds while the child is calm.",
        "chest_indrawing": "Chest indrawing?",
        "stridor": "Stridor (noisy breathing when calm)?",

        "nutrition": "Nutrition",
        "muac": "MUAC color (6–59 months)",
        "muac_not_measured": "Not measured",
        "muac_green": "Green",
        "muac_yellow": "Yellow",
        "muac_red": "Red",
        "oedema": "Swelling on both feet?",

        "young_infant_title": "Young infant add-on (0–2 months)",
        "young_infant_hint": "Only answer if the age group is 0–2 months.",
        "not_feeding": "Not feeding well?",
        "stim_only": "Moves only when stimulated?",

        "malaria_test": "Malaria test (if available)",
        "rdt_result": "RDT result",
        "rdt_not_done": "Not done",
        "rdt_negative": "Negative",
        "rdt_positive": "Positive",

        "get_result": "Get result",
        "reset": "Reset",

        "result_actions": "What to do now",
        "result_tips": "Coaching tips",
        "also_consider": "Also consider",

        "share_title": "Share via WhatsApp",
        "share_hint": "This does not auto-send. It opens WhatsApp with a pre-filled summary.",
        "message_to_share": "Message to share",
        "share_caregiver": "Share to caregiver",
        "share_supervisor": "Share to supervisor",
        "copy_summary": "Copy summary",

        "analytics": "Analytics (local)",
        "analytics_hint": "Quick admin stats from saved screenings.",
        "time_range": "Time range",
        "last_7": "Last 7 days",
        "last_30": "Last 30 days",
        "all_time": "All time",
        "assessor_filter": "Assessor filter",
        "all": "All",
        "apply": "Apply",
        "reset_filters": "Reset",
        "total": "Total",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "top_conditions": "Top conditions",
        "common_danger_signs": "Common danger signs (from forms)",
        "assessor_performance": "Assessor performance",

        "quick_guidance": "Quick guidance",
        "privacy": "Privacy",
        "privacy_text": "Keep messages short and avoid sensitive identifiers. WhatsApp numbers are optional.",

        "cond_pneumonia": "Pneumonia",
        "cond_malaria": "Malaria",
        "cond_malnutrition": "Malnutrition",
        "cond_neonatal": "Neonatal complications",

        "share_header": "Toto Gemma — Under-5 screening result",
        "share_patient": "Patient: {name}",
        "share_village": "Village: {village}",
        "share_risk": "Risk: {risk}",
        "share_most_likely": "Most likely: {cond} ({pct}%)",
        "share_also": "Also consider: {alt}",
        "share_next_steps": "Next steps:",
        "share_danger_present": "Danger signs present: seek urgent care now.",

        "act_refer_urgent": "Refer urgently to the nearest health facility now.",
        "act_keep_warm_feed": "Keep the child warm and continue breastfeeding/feeding if able.",
        "act_malaria_protocol": "If trained and stocked, follow local malaria protocol for confirmed malaria; otherwise refer.",
        "act_sam_assess": "Ask for urgent nutrition program/clinical assessment (SAM).",
        "act_follow_local": "Follow local protocol; arrange follow-up if symptoms continue or worsen.",
        "act_pneumonia_same_day": "If breathing is fast for age or worsening, go to a facility the same day.",
        "act_malaria_test": "If fever continues, get a malaria test if available and follow local treatment guidance.",
        "act_muac_link": "Measure MUAC if not done; link to community nutrition services if available.",
        "act_young_infant_prompt": "Young infants can deteriorate fast; seek facility assessment promptly.",

        "tip_keep_warm": "Keep the child warm.",
        "tip_feed_fluids": "Continue breastfeeding/feeding and offer fluids often.",
        "tip_breathing_urgent": "If breathing becomes difficult, chest pulls in, or the child cannot drink—go urgently.",

        "tip_fever_care": "Treat fever with locally recommended fever care and keep the child hydrated.",
        "tip_get_rdt": "If you can, get a malaria rapid test as soon as possible.",
        "tip_severe_malaria_urgent": "If the child becomes very sleepy, has convulsions, or cannot drink—go urgently.",

        "tip_bf_continue": "Continue breastfeeding if the child is breastfeeding.",
        "tip_small_meals": "Give small, frequent, energy-dense meals if the child can eat.",
        "tip_safe_water": "Wash hands and use safe water to reduce infections that worsen nutrition.",

        "tip_skin_to_skin": "Keep the baby warm (skin-to-skin if possible).",
        "tip_bf_frequent": "Breastfeed frequently if the baby can feed.",
        "tip_neonate_urgent": "If feeding is poor, fever/low temperature, or low movement—go urgently.",
    },

    "sw": {
        "app_title": "Toto Gemma — Uchunguzi wa Chini ya Miaka 5",
        "app_subtitle": "Ni kwa uchunguzi na ushauri tu. Dalili ya hatari ikiwapo, peleka haraka kituoni.",
        "local_storage": "Hifadhi ya ndani (SQLite)",
        "language": "Lugha",
        "translate": "Tafsiri",
        "english": "English",
        "swahili": "Kiswahili",
        "hindi": "हिंदी",

        "add_patient_title": "Ongeza mtoto (hifadhi ya ndani)",
        "add_patient_hint": "Inahifadhi kwenye kifaa hiki tu. Weka taarifa chache.",
        "name_nickname": "Jina / jina la utani",
        "village_optional": "Kijiji (si lazima)",
        "default_age_group": "Kundi la umri (chaguo-msingi)",
        "add_patient_btn": "Ongeza",

        "patient_list": "Orodha ya watoto",
        "no_patients": "Bado hakuna watoto.",
        "select": "Chagua",
        "delete": "Futa",
        "select_hint": "Chagua mtoto ili kuhifadhi historia ya uchunguzi (si lazima).",
        "recent_screenings": "Uchunguzi wa hivi karibuni (5)",
        "no_screenings": "Bado hakuna uchunguzi kwa mtoto huyu.",

        "screening_form": "Fomu ya uchunguzi",
        "screening_hint": "Jibu kinachohusika. Ukichagua mtoto kulia, uchunguzi utaokolewa chini yake.",
        "age_group": "Kundi la umri",
        "caregiver_wa": "WhatsApp ya mlezi (si lazima)",
        "supervisor_wa": "WhatsApp ya msimamizi (si lazima)",
        "digits_only": "Nambari tu, pamoja na kodi ya nchi",
        "assessor": "Jina la mhudumu/CHW (si lazima)",
        "include_patient_name": "Ongeza jina la mtoto kwenye WhatsApp?",
        "include_village": "Ongeza kijiji kwenye WhatsApp?",
        "only_used_if_patient": "Hutumika tu kama umechagua mtoto.",
        "no": "Hapana",
        "yes": "Ndiyo",

        "danger_signs": "Dalili za hatari",
        "danger_signs_hint": "Ikiwa yoyote ni Ndiyo, peleka haraka.",
        "ds_drink": "Hawezi kunywa/kunyonya?",
        "ds_vomit": "Hutapika kila kitu?",
        "ds_convulsions": "Degedege?",
        "ds_lethargy": "Mchovu sana/amelala bila fahamu?",

        "main_symptoms": "Dalili kuu",
        "fever": "Homa sasa au siku 2 zilizopita?",
        "cough_breath": "Kikohozi au kupumua kwa shida?",
        "rr": "Pumzi kwa dakika (si lazima)",
        "rr_hint": "Dokezo: hesabu pumzi kwa sekunde 60 mtoto akiwa mtulivu.",
        "chest_indrawing": "Kifua kuvutika ndani?",
        "stridor": "Sauti ya kupumua wakati mtulivu?",

        "nutrition": "Lishe",
        "muac": "Rangi ya MUAC (miezi 6–59)",
        "muac_not_measured": "Haijapimwa",
        "muac_green": "Kijani",
        "muac_yellow": "Njano",
        "muac_red": "Nyekundu",
        "oedema": "Uvimbe miguu yote miwili?",

        "young_infant_title": "Sehemu ya mtoto mchanga (miezi 0–2)",
        "young_infant_hint": "Jibu tu kama umri ni miezi 0–2.",
        "not_feeding": "Hanyonyi/halishi vizuri?",
        "stim_only": "Husogea tu akichochewa?",

        "malaria_test": "Kipimo cha malaria (kikipatikana)",
        "rdt_result": "Matokeo ya RDT",
        "rdt_not_done": "Hakijafanywa",
        "rdt_negative": "Hasi",
        "rdt_positive": "Chanya",

        "get_result": "Pata matokeo",
        "reset": "Weka upya",

        "result_actions": "Hatua za sasa",
        "result_tips": "Ushauri kwa mlezi",
        "also_consider": "Pia zingatia",

        "share_title": "Shiriki kwa WhatsApp",
        "share_hint": "Haiwatumi moja kwa moja. Hufungua WhatsApp na ujumbe tayari.",
        "message_to_share": "Ujumbe wa kushiriki",
        "share_caregiver": "Shiriki kwa mlezi",
        "share_supervisor": "Shiriki kwa msimamizi",
        "copy_summary": "Nakili muhtasari",

        "analytics": "Takwimu (ndani)",
        "analytics_hint": "Muhtasari wa msimamizi kutoka uchunguzi uliohifadhiwa.",
        "time_range": "Kipindi",
        "last_7": "Siku 7",
        "last_30": "Siku 30",
        "all_time": "Muda wote",
        "assessor_filter": "Kichujio cha mhudumu",
        "all": "Zote",
        "apply": "Tumia",
        "reset_filters": "Weka upya",
        "total": "Jumla",
        "high": "Hatari kubwa",
        "medium": "Hatari ya kati",
        "low": "Hatari ndogo",
        "top_conditions": "Magonjwa yanayoongoza",
        "common_danger_signs": "Dalili za hatari (mara nyingi)",
        "assessor_performance": "Utendaji wa mhudumu",

        "quick_guidance": "Mwongozo wa haraka",
        "privacy": "Faragha",
        "privacy_text": "Weka ujumbe mfupi, epuka vitambulisho nyeti. Nambari za WhatsApp si lazima.",

        "cond_pneumonia": "Nimonia",
        "cond_malaria": "Malaria",
        "cond_malnutrition": "Utapiamlo",
        "cond_neonatal": "Matatizo ya mtoto mchanga",

        "share_header": "Toto Gemma — Matokeo ya uchunguzi",
        "share_patient": "Mtoto: {name}",
        "share_village": "Kijiji: {village}",
        "share_risk": "Hatari: {risk}",
        "share_most_likely": "Inawezekana zaidi: {cond} ({pct}%)",
        "share_also": "Pia zingatia: {alt}",
        "share_next_steps": "Hatua:",
        "share_danger_present": "Dalili za hatari zipo: peleka haraka.",

        "act_refer_urgent": "Peleka haraka kituo cha afya sasa.",
        "act_keep_warm_feed": "Mweke mtoto joto na endelea kumnyonyesha/kumlisha kama anaweza.",
        "act_malaria_protocol": "Ikiwezekana na umefunzwa, fuata mwongozo wa malaria; vinginevyo peleka kituoni.",
        "act_sam_assess": "Omba tathmini ya lishe/kliniki haraka (SAM).",
        "act_follow_local": "Fuata mwongozo wa eneo; panga ufuatiliaji kama dalili zinaendelea au zinaongezeka.",
        "act_pneumonia_same_day": "Kama pumzi ni nyingi kwa umri au hali inazidi, nenda kituoni siku hiyo.",
        "act_malaria_test": "Kama homa inaendelea, fanya kipimo cha malaria na fuata mwongozo wa matibabu.",
        "act_muac_link": "Pima MUAC kama haijapimwa; unganisha huduma za lishe kama zipo.",
        "act_young_infant_prompt": "Watoto wachanga huzorota haraka; tafuta tathmini ya kituo mapema.",

        "tip_keep_warm": "Mweke mtoto joto.",
        "tip_feed_fluids": "Endelea kumnyonyesha/kumlisha na mpe maji mara kwa mara.",
        "tip_breathing_urgent": "Kama kupumua kunakuwa kugumu, kifua kinavuta ndani, au hawezi kunywa—peleka haraka.",

        "tip_fever_care": "Hudumia homa kwa mwongozo wa eneo na mpe maji.",
        "tip_get_rdt": "Kama unaweza, pata kipimo cha haraka cha malaria mapema.",
        "tip_severe_malaria_urgent": "Akiwa mchovu sana, ana degedege, au hawezi kunywa—peleka haraka.",

        "tip_bf_continue": "Endelea kumnyonyesha kama ananyonyesha.",
        "tip_small_meals": "Mpe mlo mdogo mdogo mara nyingi kama anaweza kula.",
        "tip_safe_water": "Nawa mikono na tumia maji salama kupunguza maambukizi.",

        "tip_skin_to_skin": "Mweke joto (ngozi kwa ngozi ikiwezekana).",
        "tip_bf_frequent": "Mnyonyeshe mara kwa mara kama anaweza.",
        "tip_neonate_urgent": "Akiwa halei vizuri, ana homa/joto la chini, au hasogei—peleka haraka.",
    },

    "hi": {
        "app_title": "Toto Gemma — 5 साल से कम की स्क्रीनिंग",
        "app_subtitle": "यह सिर्फ स्क्रीनिंग/कोचिंग के लिए है। अगर खतरे के लक्षण हों तो तुरंत रेफर करें।",
        "local_storage": "लोकल स्टोरेज (SQLite)",
        "language": "भाषा",
        "translate": "अनुवाद",
        "english": "English",
        "swahili": "Kiswahili",
        "hindi": "हिंदी",

        "add_patient_title": "बच्चा जोड़ें (लोकल)",
        "add_patient_hint": "सिर्फ इसी डिवाइस पर सेव होता है। जानकारी कम रखें।",
        "name_nickname": "नाम / उपनाम",
        "village_optional": "गाँव (वैकल्पिक)",
        "default_age_group": "डिफ़ॉल्ट आयु समूह",
        "add_patient_btn": "जोड़ें",

        "patient_list": "बच्चों की सूची",
        "no_patients": "अभी कोई बच्चा नहीं।",
        "select": "चुनें",
        "delete": "हटाएँ",
        "select_hint": "हिस्ट्री सेव करने के लिए बच्चा चुनें (वैकल्पिक)।",
        "recent_screenings": "हाल की स्क्रीनिंग (5)",
        "no_screenings": "इस बच्चे की अभी कोई स्क्रीनिंग नहीं।",

        "screening_form": "स्क्रीनिंग फ़ॉर्म",
        "screening_hint": "जो लागू हो वही चुनें। दाईं ओर बच्चा चुना हो तो हिस्ट्री सेव होगी।",
        "age_group": "आयु समूह",
        "caregiver_wa": "केयरगिवर WhatsApp (वैकल्पिक)",
        "supervisor_wa": "सुपरवाइज़र WhatsApp (वैकल्पिक)",
        "digits_only": "सिर्फ अंक, देश कोड सहित",
        "assessor": "असेसर/CHW नाम (वैकल्पिक)",
        "include_patient_name": "WhatsApp में बच्चे का नाम जोड़ें?",
        "include_village": "WhatsApp में गाँव जोड़ें?",
        "only_used_if_patient": "सिर्फ तब जब बच्चा चुना हो।",
        "no": "नहीं",
        "yes": "हाँ",

        "danger_signs": "खतरे के लक्षण",
        "danger_signs_hint": "अगर कोई भी 'हाँ' हो, तुरंत रेफर करें।",
        "ds_drink": "पी/दूध नहीं पी पा रहा?",
        "ds_vomit": "सब कुछ उल्टी कर देता?",
        "ds_convulsions": "दौरे?",
        "ds_lethargy": "बहुत सुस्त/बेहोश?",

        "main_symptoms": "मुख्य लक्षण",
        "fever": "अभी या पिछले 2 दिनों में बुखार?",
        "cough_breath": "खाँसी या साँस में तकलीफ़?",
        "rr": "प्रति मिनट साँस (वैकल्पिक)",
        "rr_hint": "टिप: बच्चा शांत हो तब 60 सेकंड में साँस गिनें।",
        "chest_indrawing": "छाती अंदर धँसती है?",
        "stridor": "शांत होने पर भी सीटी जैसी आवाज़?",

        "nutrition": "पोषण",
        "muac": "MUAC रंग (6–59 महीने)",
        "muac_not_measured": "नहीं मापा",
        "muac_green": "हरा",
        "muac_yellow": "पीला",
        "muac_red": "लाल",
        "oedema": "दोनों पैरों में सूजन?",

        "young_infant_title": "नवजात/छोटा शिशु (0–2 महीने)",
        "young_infant_hint": "सिर्फ 0–2 महीने होने पर ही भरें।",
        "not_feeding": "ठीक से नहीं पी रहा?",
        "stim_only": "सिर्फ जगाने पर ही हिलता?",

        "malaria_test": "मलेरिया टेस्ट (यदि उपलब्ध)",
        "rdt_result": "RDT परिणाम",
        "rdt_not_done": "नहीं किया",
        "rdt_negative": "नकारात्मक",
        "rdt_positive": "सकारात्मक",

        "get_result": "परिणाम",
        "reset": "रीसेट",

        "result_actions": "अभी क्या करें",
        "result_tips": "केयरगिवर के लिए सलाह",
        "also_consider": "यह भी संभव",

        "share_title": "WhatsApp से शेयर करें",
        "share_hint": "ऑटो-सेंड नहीं होता। WhatsApp में मैसेज तैयार मिलेगा।",
        "message_to_share": "शेयर करने वाला संदेश",
        "share_caregiver": "केयरगिवर को",
        "share_supervisor": "सुपरवाइज़र को",
        "copy_summary": "कॉपी",

        "analytics": "एनालिटिक्स (लोकल)",
        "analytics_hint": "सेव की गई स्क्रीनिंग से एडमिन स्टैट्स।",
        "time_range": "समय",
        "last_7": "पिछले 7 दिन",
        "last_30": "पिछले 30 दिन",
        "all_time": "सभी",
        "assessor_filter": "असेसर फ़िल्टर",
        "all": "सभी",
        "apply": "लागू करें",
        "reset_filters": "रीसेट",
        "total": "कुल",
        "high": "हाई",
        "medium": "मीडियम",
        "low": "लो",
        "top_conditions": "टॉप कंडीशन्स",
        "common_danger_signs": "आम खतरे के लक्षण",
        "assessor_performance": "असेसर परफॉर्मेंस",

        "quick_guidance": "क्विक गाइड",
        "privacy": "प्राइवेसी",
        "privacy_text": "मैसेज छोटा रखें, संवेदनशील पहचान न जोड़ें। WhatsApp नंबर वैकल्पिक हैं।",

        "cond_pneumonia": "निमोनिया",
        "cond_malaria": "मलेरिया",
        "cond_malnutrition": "कुपोषण",
        "cond_neonatal": "नवजात जटिलताएँ",

        "share_header": "Toto Gemma — स्क्रीनिंग परिणाम",
        "share_patient": "बच्चा: {name}",
        "share_village": "गाँव: {village}",
        "share_risk": "रिस्क: {risk}",
        "share_most_likely": "सबसे संभव: {cond} ({pct}%)",
        "share_also": "यह भी संभव: {alt}",
        "share_next_steps": "अगले कदम:",
        "share_danger_present": "खतरे के लक्षण हैं: तुरंत इलाज लें।",

        "act_refer_urgent": "तुरंत नज़दीकी स्वास्थ्य केंद्र रेफर करें।",
        "act_keep_warm_feed": "बच्चे को गर्म रखें और संभव हो तो दूध/खाना जारी रखें।",
        "act_malaria_protocol": "अगर प्रशिक्षित हैं तो लोकल मलेरिया प्रोटोकॉल फॉलो करें, वरना रेफर करें।",
        "act_sam_assess": "तुरंत पोषण/क्लिनिक आकलन (SAM) करवाएँ।",
        "act_follow_local": "लोकल प्रोटोकॉल फॉलो करें; लक्षण बने रहें/बढ़ें तो फॉलो-अप करें।",
        "act_pneumonia_same_day": "साँस तेज़/बिगड़ रही हो तो उसी दिन केंद्र जाएँ।",
        "act_malaria_test": "बुखार जारी रहे तो टेस्ट कराएँ और लोकल गाइडेंस फॉलो करें।",
        "act_muac_link": "MUAC नहीं मापा तो मापें; पोषण सेवाओं से जोड़ें।",
        "act_young_infant_prompt": "छोटे शिशु जल्दी बिगड़ सकते हैं; जल्द आकलन कराएँ।",

        "tip_keep_warm": "बच्चे को गर्म रखें।",
        "tip_feed_fluids": "दूध/खाना जारी रखें और तरल दें।",
        "tip_breathing_urgent": "साँस मुश्किल, छाती धँसे, या पी न पाए—तुरंत जाएँ।",

        "tip_fever_care": "लोकल गाइडेंस के अनुसार बुखार देखभाल करें और हाइड्रेट रखें।",
        "tip_get_rdt": "हो सके तो जल्द मलेरिया रैपिड टेस्ट कराएँ।",
        "tip_severe_malaria_urgent": "बहुत सुस्त/दौरे/पी न पाए—तुरंत जाएँ।",

        "tip_bf_continue": "अगर बच्चा स्तनपान करता है तो जारी रखें।",
        "tip_small_meals": "छोटे-छोटे, बार-बार, ऊर्जा-युक्त भोजन दें।",
        "tip_safe_water": "हाथ धोएँ और सुरक्षित पानी उपयोग करें।",

        "tip_skin_to_skin": "बच्चे को गर्म रखें (त्वचा से त्वचा)।",
        "tip_bf_frequent": "बार-बार स्तनपान कराएँ।",
        "tip_neonate_urgent": "ठीक से न पिए/बुखार या ठंड/कम हिले—तुरंत जाएँ।",
    },
}

LANG_CHOICES = [("en", "english"), ("sw", "swahili"), ("hi", "hindi")]


def make_t(lang: str):
    base = TRANSLATIONS["en"]
    cur = TRANSLATIONS.get(lang, base)

    def t(key: str, **kwargs):
        s = cur.get(key, base.get(key, key))
        try:
            return s.format(**kwargs)
        except Exception:
            return s

    return t


def condition_label(lang: str, name: str) -> str:
    t = make_t(lang)
    mapping = {
        "Pneumonia": t("cond_pneumonia"),
        "Malaria": t("cond_malaria"),
        "Malnutrition": t("cond_malnutrition"),
        "Neonatal complications": t("cond_neonatal"),
    }
    return mapping.get(name, name)


# -------------------- UI --------------------

HTML = r"""
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{{ t('app_title') }}</title>
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

    .badges { display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:flex-end; }
    .badge {
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      font-weight: 700;
      font-size: 0.88rem;
      white-space: nowrap;
    }
    .badge-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent2); box-shadow: 0 0 0 3px rgba(32,201,151,0.18); }

    .langform { display:flex; align-items:center; gap:8px; }
    .langlabel { color: var(--muted); font-weight: 800; font-size: 0.88rem; }

    .langselect {
      min-height: 40px;
      padding: 8px 34px 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      outline: none;
      appearance: none;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position: calc(100% - 18px) 55%, calc(100% - 13px) 55%;
      background-size: 6px 6px, 6px 6px;
      background-repeat: no-repeat;
    }
    .langselect option { color: #0a0e1c; background: #ffffff; }

    /* Google Translate widget styling */
    .gt-wrap { display:flex; align-items:center; gap:8px; }
    .gt-label { color: var(--muted); font-weight: 800; font-size: 0.88rem; }
    #google_translate_element { display:inline-flex; align-items:center; }
    .goog-te-gadget { font-size: 0; } /* kill default text */
    .goog-te-gadget span { display:none; }
    .goog-te-combo {
      min-height: 40px !important;
      padding: 8px 34px 8px 10px !important;
      border-radius: 999px !important;
      border: 1px solid var(--border) !important;
      background: rgba(255,255,255,0.06) !important;
      color: var(--text) !important;
      outline: none !important;
      appearance: none !important;
      margin: 0 !important;
      font-size: 0.88rem !important;
    }
    /* the dropdown list itself is browser-native; options need contrast */
    .goog-te-combo option { color:#0a0e1c; background:#ffffff; }

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
    .pill, .chip {
      display:inline-flex;
      align-items:center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      font-weight: 900;
      font-size: 0.88rem;
      white-space: nowrap;
    }

    .danger { border-color: rgba(255,92,119,0.35); background: linear-gradient(180deg, rgba(255,92,119,0.16), rgba(255,255,255,0.06)); }
    .warn   { border-color: rgba(255,207,90,0.35); background: linear-gradient(180deg, rgba(255,207,90,0.16), rgba(255,255,255,0.06)); }
    .ok     { border-color: rgba(47,208,124,0.35); background: linear-gradient(180deg, rgba(47,208,124,0.16), rgba(255,255,255,0.06)); }

    form { margin: 0; }
    label { display:block; margin: 10px 0 6px; font-weight: 900; }

    .row { display: grid; grid-template-columns: 1fr; gap: 10px; }
    @media (min-width: 640px) { .row { grid-template-columns: 1fr 1fr; } }

    .row3 { display: grid; grid-template-columns: 1fr; gap: 10px; }
    @media (min-width: 960px) { .row3 { grid-template-columns: 1fr 1fr 1fr; align-items: end; } }

    /* Alignment fix: consistent label height on larger screens */
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
    textarea { min-height: 132px; resize: vertical; }

    /* Dropdown options visibility fix */
    select { color-scheme: light dark; }
    select option { color: #0a0e1c; background: #ffffff; }

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
      font-weight: 950;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      user-select: none;
      min-height: 44px;
    }
    .segmented label:hover { background: rgba(255,255,255,0.06); }
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
      font-weight: 950;
      cursor: pointer;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap: 10px;
      text-decoration:none;
      text-align:center;
      min-height: 44px;
      flex: 1 1 220px;
    }
    .btn-primary { background: var(--accent); color: #fff; }
    .btn-secondary { background: rgba(255,255,255,0.08); border-color: var(--border); color: var(--text); }
    .btn-danger { background: rgba(255,92,119,0.18); border-color: rgba(255,92,119,0.35); color: var(--text); }
    .btn-whatsapp { background: #25D366; color: #fff; }

    /* IMPORTANT: buttons only at bottom (NOT sticky/following) */
    .bottom-actions { margin-top: 14px; }

    .hidden { display: none !important; }

    ul { margin: 8px 0 0 18px; }
    li { margin: 6px 0; }

    .table { width: 100%; border-collapse: collapse; }
    .table th, .table td { text-align: left; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.10); vertical-align: top; }
    @media (prefers-color-scheme: light) { .table th, .table td { border-bottom: 1px solid rgba(10,14,28,0.10); } }
    .nowrap { white-space: nowrap; }

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
        <h1>{{ t('app_title') }}</h1>
        <p>{{ t('app_subtitle') }}</p>
      </div>

      <div class="badges" aria-label="Status">
        <span class="badge"><span class="badge-dot" aria-hidden="true"></span>{{ t('local_storage') }}</span>

        <!-- Local translations (fast/offline, your curated strings) -->
        <form class="langform" method="get">
          {% if selected_patient %}
            <input type="hidden" name="patient_id" value="{{ selected_patient['id'] }}">
          {% endif %}
          <input type="hidden" name="ar" value="{{ ar }}">
          <input type="hidden" name="aa" value="{{ aa }}">
          <span class="langlabel">{{ t('language') }}</span>
          <select class="langselect" name="lang" onchange="this.form.submit()">
            {% for code, label_key in lang_choices %}
              <option value="{{ code }}" {% if lang == code %}selected{% endif %}>{{ t(label_key) }}</option>
            {% endfor %}
          </select>
        </form>

        <!-- Google Translate (for any other language on-demand) -->
        <span class="badge">
          <span class="gt-label">{{ t('translate') }}</span>
          <span id="google_translate_element"></span>
        </span>
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
              <span class="pill">{{ t('share_risk', risk=result.risk) }}</span>
              <span class="pill">{{ t('share_most_likely', cond=result.top_condition_label, pct=result.certainty) }}</span>
              <span class="pill">{{ result.certainty }}%</span>
            </div>

            <h2>{{ t('result_actions') }}</h2>
            <ul>
              {% for s in result.actions %}
                <li>{{ s }}</li>
              {% endfor %}
            </ul>

            <div class="divider"></div>

            <h2>{{ t('result_tips') }}</h2>
            <ul>
              {% for s in result.tips %}
                <li>{{ s }}</li>
              {% endfor %}
            </ul>

            <div class="divider"></div>

            <h2>{{ t('also_consider') }}</h2>
            <ul>
              {% for name, pct in result.alternatives %}
                <li>{{ name }} — {{ pct }}%</li>
              {% endfor %}
            </ul>
          </section>

          <section class="card" aria-label="Share via WhatsApp">
            <h2>{{ t('share_title') }}</h2>
            <p class="muted">{{ t('share_hint') }}</p>

            <label for="shareText">{{ t('message_to_share') }}</label>
            <textarea id="shareText" readonly>{{ result.share_message }}</textarea>

            <div class="btn-row">
              <a class="btn btn-whatsapp" href="{{ result.wa_caregiver_url }}" target="_blank" rel="noopener">{{ t('share_caregiver') }}</a>
              <a class="btn btn-whatsapp" href="{{ result.wa_supervisor_url }}" target="_blank" rel="noopener">{{ t('share_supervisor') }}</a>
              <button class="btn btn-secondary" type="button" onclick="copyShareText()">{{ t('copy_summary') }}</button>
            </div>

            <p id="copyStatus" class="muted" style="margin-top:10px;"></p>
          </section>
        {% endif %}

        <section class="card" aria-label="Add patient">
          <h2>{{ t('add_patient_title') }}</h2>
          <p class="muted">{{ t('add_patient_hint') }}</p>

          <form method="post">
            <input type="hidden" name="action" value="add_patient">
            <input type="hidden" name="lang" value="{{ lang }}">
            <input type="hidden" name="ar" value="{{ ar }}">
            <input type="hidden" name="aa" value="{{ aa }}">

            <div class="row">
              <div>
                <label for="p_name">{{ t('name_nickname') }}</label>
                <input id="p_name" type="text" name="p_name" placeholder="e.g., Amina" required>
              </div>
              <div>
                <label for="p_village">{{ t('village_optional') }}</label>
                <input id="p_village" type="text" name="p_village" placeholder="e.g., Kibera">
              </div>
            </div>

            <label for="p_age_group">{{ t('default_age_group') }}</label>
            <select id="p_age_group" name="p_age_group" required>
              <option value="0_2m">0–2 months</option>
              <option value="2_12m">2–12 months</option>
              <option value="1_5y" selected>1–5 years</option>
            </select>

            <div class="btn-row">
              <button class="btn btn-secondary" type="submit">{{ t('add_patient_btn') }}</button>
            </div>
          </form>
        </section>

        <section id="screen" class="card" aria-label="Under-5 screening form">
          <h2>{{ t('screening_form') }}</h2>
          <p class="muted">{{ t('screening_hint') }}</p>

          {% if selected_patient %}
            <div class="pill-row">
              <span class="chip">
                {{ t('current_patient', name=selected_patient['name'], village=((" — " + selected_patient['village']) if selected_patient['village'] else "")) }}
              </span>
            </div>
          {% endif %}

          <form method="post" novalidate>
            <input type="hidden" name="action" value="run_screening">
            <input type="hidden" name="lang" value="{{ lang }}">
            <input type="hidden" name="ar" value="{{ ar }}">
            <input type="hidden" name="aa" value="{{ aa }}">

            <div class="row3">
              <div>
                <label for="age_group">{{ t('age_group') }}</label>
                <select id="age_group" name="age_group" required>
                  <option value="0_2m" {{ selected('age_group','0_2m', default_age_group) }}>0–2 months</option>
                  <option value="2_12m" {{ selected('age_group','2_12m', default_age_group) }}>2–12 months</option>
                  <option value="1_5y" {{ selected('age_group','1_5y', default_age_group) }}>1–5 years</option>
                </select>
              </div>
              <div>
                <label for="wa_caregiver">{{ t('caregiver_wa') }}</label>
                <input id="wa_caregiver" type="tel" name="wa_caregiver" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_caregiver','') }}" placeholder="{{ t('digits_only') }}">
              </div>
              <div>
                <label for="wa_supervisor">{{ t('supervisor_wa') }}</label>
                <input id="wa_supervisor" type="tel" name="wa_supervisor" inputmode="numeric" autocomplete="tel"
                       value="{{ form.get('wa_supervisor','') }}" placeholder="{{ t('digits_only') }}">
              </div>
            </div>

            <div class="row" style="margin-top: 6px;">
              <div>
                <label for="assessor">{{ t('assessor') }}</label>
                <input id="assessor" type="text" name="assessor" value="{{ form.get('assessor','') }}" placeholder="e.g., Fatima">
              </div>
              <div>
                <label>{{ t('include_patient_name') }}</label>
                <div class="segmented" role="group">
                  <input id="include_name_no" type="radio" name="include_name" value="No" {{ checked('include_name','No','No') }}>
                  <label for="include_name_no">{{ t('no') }}</label>
                  <input id="include_name_yes" type="radio" name="include_name" value="Yes" {{ checked('include_name','Yes','No') }}>
                  <label for="include_name_yes">{{ t('yes') }}</label>
                </div>
                <div class="hint">{{ t('only_used_if_patient') }}</div>
              </div>
            </div>

            <div class="row" style="margin-top: 6px;">
              <div>
                <label>{{ t('include_village') }}</label>
                <div class="segmented" role="group">
                  <input id="include_village_no" type="radio" name="include_village" value="No" {{ checked('include_village','No','No') }}>
                  <label for="include_village_no">{{ t('no') }}</label>
                  <input id="include_village_yes" type="radio" name="include_village" value="Yes" {{ checked('include_village','Yes','No') }}>
                  <label for="include_village_yes">{{ t('yes') }}</label>
                </div>
                <div class="hint">{{ t('only_used_if_patient') }}</div>
              </div>
              <div></div>
            </div>

            <div class="divider"></div>

            <div class="card warn" aria-label="Danger signs">
              <h3>{{ t('danger_signs') }}</h3>
              <p class="muted">{{ t('danger_signs_hint') }}</p>

              <div class="row">
                <div>
                  <label>{{ t('ds_drink') }}</label>
                  <div class="segmented" role="group">
                    <input id="ds_drink_no" type="radio" name="ds_drink" value="No" {{ checked('ds_drink','No','No') }}>
                    <label for="ds_drink_no">{{ t('no') }}</label>
                    <input id="ds_drink_yes" type="radio" name="ds_drink" value="Yes" {{ checked('ds_drink','Yes','No') }}>
                    <label for="ds_drink_yes">{{ t('yes') }}</label>
                  </div>
                </div>
                <div>
                  <label>{{ t('ds_vomit') }}</label>
                  <div class="segmented" role="group">
                    <input id="ds_vomit_no" type="radio" name="ds_vomit" value="No" {{ checked('ds_vomit','No','No') }}>
                    <label for="ds_vomit_no">{{ t('no') }}</label>
                    <input id="ds_vomit_yes" type="radio" name="ds_vomit" value="Yes" {{ checked('ds_vomit','Yes','No') }}>
                    <label for="ds_vomit_yes">{{ t('yes') }}</label>
                  </div>
                </div>
                <div>
                  <label>{{ t('ds_convulsions') }}</label>
                  <div class="segmented" role="group">
                    <input id="ds_convulsions_no" type="radio" name="ds_convulsions" value="No" {{ checked('ds_convulsions','No','No') }}>
                    <label for="ds_convulsions_no">{{ t('no') }}</label>
                    <input id="ds_convulsions_yes" type="radio" name="ds_convulsions" value="Yes" {{ checked('ds_convulsions','Yes','No') }}>
                    <label for="ds_convulsions_yes">{{ t('yes') }}</label>
                  </div>
                </div>
                <div>
                  <label>{{ t('ds_lethargy') }}</label>
                  <div class="segmented" role="group">
                    <input id="ds_lethargy_no" type="radio" name="ds_lethargy" value="No" {{ checked('ds_lethargy','No','No') }}>
                    <label for="ds_lethargy_no">{{ t('no') }}</label>
                    <input id="ds_lethargy_yes" type="radio" name="ds_lethargy" value="Yes" {{ checked('ds_lethargy','Yes','No') }}>
                    <label for="ds_lethargy_yes">{{ t('yes') }}</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>{{ t('main_symptoms') }}</h3>
            <div class="row">
              <div>
                <label>{{ t('fever') }}</label>
                <div class="segmented" role="group">
                  <input id="fever_no" type="radio" name="fever" value="No" {{ checked('fever','No','No') }}>
                  <label for="fever_no">{{ t('no') }}</label>
                  <input id="fever_yes" type="radio" name="fever" value="Yes" {{ checked('fever','Yes','No') }}>
                  <label for="fever_yes">{{ t('yes') }}</label>
                </div>
              </div>
              <div>
                <label>{{ t('cough_breath') }}</label>
                <div class="segmented" role="group">
                  <input id="cough_breath_no" type="radio" name="cough_breath" value="No" {{ checked('cough_breath','No','No') }}>
                  <label for="cough_breath_no">{{ t('no') }}</label>
                  <input id="cough_breath_yes" type="radio" name="cough_breath" value="Yes" {{ checked('cough_breath','Yes','No') }}>
                  <label for="cough_breath_yes">{{ t('yes') }}</label>
                </div>
              </div>
            </div>

            <label for="rr">{{ t('rr') }}</label>
            <input id="rr" type="number" name="rr" min="0" max="120" inputmode="numeric"
                   value="{{ form.get('rr','') }}" placeholder="e.g., 48">
            <div class="hint">{{ t('rr_hint') }}</div>

            <div class="row" style="margin-top: 10px;">
              <div>
                <label>{{ t('chest_indrawing') }}</label>
                <div class="segmented" role="group">
                  <input id="chest_indrawing_no" type="radio" name="chest_indrawing" value="No" {{ checked('chest_indrawing','No','No') }}>
                  <label for="chest_indrawing_no">{{ t('no') }}</label>
                  <input id="chest_indrawing_yes" type="radio" name="chest_indrawing" value="Yes" {{ checked('chest_indrawing','Yes','No') }}>
                  <label for="chest_indrawing_yes">{{ t('yes') }}</label>
                </div>
              </div>
              <div>
                <label>{{ t('stridor') }}</label>
                <div class="segmented" role="group">
                  <input id="stridor_no" type="radio" name="stridor" value="No" {{ checked('stridor','No','No') }}>
                  <label for="stridor_no">{{ t('no') }}</label>
                  <input id="stridor_yes" type="radio" name="stridor" value="Yes" {{ checked('stridor','Yes','No') }}>
                  <label for="stridor_yes">{{ t('yes') }}</label>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>{{ t('nutrition') }}</h3>
            <div class="row">
              <div>
                <label for="muac">{{ t('muac') }}</label>
                <select id="muac" name="muac" required>
                  <option value="not_measured" {{ selected('muac','not_measured','not_measured') }}>{{ t('muac_not_measured') }}</option>
                  <option value="green" {{ selected('muac','green','not_measured') }}>{{ t('muac_green') }}</option>
                  <option value="yellow" {{ selected('muac','yellow','not_measured') }}>{{ t('muac_yellow') }}</option>
                  <option value="red" {{ selected('muac','red','not_measured') }}>{{ t('muac_red') }}</option>
                </select>
              </div>
              <div>
                <label>{{ t('oedema') }}</label>
                <div class="segmented" role="group">
                  <input id="oedema_no" type="radio" name="oedema" value="No" {{ checked('oedema','No','No') }}>
                  <label for="oedema_no">{{ t('no') }}</label>
                  <input id="oedema_yes" type="radio" name="oedema" value="Yes" {{ checked('oedema','Yes','No') }}>
                  <label for="oedema_yes">{{ t('yes') }}</label>
                </div>
              </div>
            </div>

            <div id="young_infant" class="card" style="margin-top: 14px;" aria-label="Young infant add-on">
              <h3>{{ t('young_infant_title') }}</h3>
              <p class="muted">{{ t('young_infant_hint') }}</p>
              <div class="row">
                <div>
                  <label>{{ t('not_feeding') }}</label>
                  <div class="segmented" role="group">
                    <input id="not_feeding_no" type="radio" name="not_feeding" value="No" {{ checked('not_feeding','No','') }}>
                    <label for="not_feeding_no">{{ t('no') }}</label>
                    <input id="not_feeding_yes" type="radio" name="not_feeding" value="Yes" {{ checked('not_feeding','Yes','') }}>
                    <label for="not_feeding_yes">{{ t('yes') }}</label>
                  </div>
                </div>
                <div>
                  <label>{{ t('stim_only') }}</label>
                  <div class="segmented" role="group">
                    <input id="stim_only_no" type="radio" name="stim_only" value="No" {{ checked('stim_only','No','') }}>
                    <label for="stim_only_no">{{ t('no') }}</label>
                    <input id="stim_only_yes" type="radio" name="stim_only" value="Yes" {{ checked('stim_only','Yes','') }}>
                    <label for="stim_only_yes">{{ t('yes') }}</label>
                  </div>
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <h3>{{ t('malaria_test') }}</h3>
            <label for="rdt">{{ t('rdt_result') }}</label>
            <select id="rdt" name="rdt" required>
              <option value="not_done" {{ selected('rdt','not_done','not_done') }}>{{ t('rdt_not_done') }}</option>
              <option value="negative" {{ selected('rdt','negative','not_done') }}>{{ t('rdt_negative') }}</option>
              <option value="positive" {{ selected('rdt','positive','not_done') }}>{{ t('rdt_positive') }}</option>
            </select>

            <!-- Bottom-only actions (no sticky tracking) -->
            <div class="bottom-actions">
              <div class="btn-row">
                <button class="btn btn-primary" type="submit">{{ t('get_result') }}</button>
                <button class="btn btn-secondary" type="reset">{{ t('reset') }}</button>
              </div>
            </div>
          </form>
        </section>
      </main>

      <aside>
        <section class="card" aria-label="Patient list">
          <h2>{{ t('patient_list') }}</h2>
          {% if patients|length == 0 %}
            <p class="muted">{{ t('no_patients') }}</p>
          {% else %}
            <table class="table">
              <thead>
                <tr>
                  <th>{{ t('name_nickname') }}</th>
                  <th>{{ t('village_optional') }}</th>
                  <th class="nowrap">{{ t('age_group') }}</th>
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
                         href="{{ url_for('index', patient_id=p['id'], ar=ar, aa=aa, lang=lang) }}">{{ t('select') }}</a>

                      <form method="post" style="display:inline;" onsubmit="return confirm('Delete this patient and history?');">
                        <input type="hidden" name="action" value="delete_patient">
                        <input type="hidden" name="patient_id" value="{{ p['id'] }}">
                        <input type="hidden" name="lang" value="{{ lang }}">
                        <input type="hidden" name="ar" value="{{ ar }}">
                        <input type="hidden" name="aa" value="{{ aa }}">
                        <button class="btn btn-danger" style="padding:8px 10px; border-radius:12px; min-height:auto; flex:none;" type="submit">{{ t('delete') }}</button>
                      </form>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
            <div class="hint">{{ t('select_hint') }}</div>
          {% endif %}

          {% if selected_patient %}
            <div class="divider"></div>
            <h3>{{ t('recent_screenings') }}</h3>
            {% if history|length == 0 %}
              <p class="muted">{{ t('no_screenings') }}</p>
            {% else %}
              <table class="table">
                <thead>
                  <tr>
                    <th class="nowrap">Date</th>
                    <th>{{ t('high') }}/{{ t('medium') }}/{{ t('low') }}</th>
                    <th>{{ t('top_conditions') }}</th>
                    <th class="nowrap">%</th>
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
          <h2>{{ t('analytics') }}</h2>
          <p class="muted">{{ t('analytics_hint') }}</p>

          <form method="get">
            {% if selected_patient %}
              <input type="hidden" name="patient_id" value="{{ selected_patient['id'] }}">
            {% endif %}
            <input type="hidden" name="lang" value="{{ lang }}">
            <div class="row">
              <div>
                <label for="ar">{{ t('time_range') }}</label>
                <select id="ar" name="ar">
                  <option value="7"  {% if ar == '7' %}selected{% endif %}>{{ t('last_7') }}</option>
                  <option value="30" {% if ar == '30' %}selected{% endif %}>{{ t('last_30') }}</option>
                  <option value="all" {% if ar == 'all' %}selected{% endif %}>{{ t('all_time') }}</option>
                </select>
              </div>
              <div>
                <label for="aa">{{ t('assessor_filter') }}</label>
                <select id="aa" name="aa">
                  <option value="" {% if aa == '' %}selected{% endif %}>{{ t('all') }}</option>
                  {% for n in assessor_names %}
                    <option value="{{ n }}" {% if aa == n %}selected{% endif %}>{{ n }}</option>
                  {% endfor %}
                </select>
              </div>
            </div>
            <div class="btn-row" style="margin-top:10px;">
              <button class="btn btn-secondary" type="submit">{{ t('apply') }}</button>
              <a class="btn btn-secondary"
                 href="{{ url_for('index', patient_id=(selected_patient['id'] if selected_patient else None), lang=lang) }}">{{ t('reset_filters') }}</a>
            </div>
          </form>

          <div class="divider"></div>

          <div class="pill-row">
            <span class="pill">{{ t('total') }}: {{ analytics.total }}</span>
            <span class="pill">{{ t('high') }}: {{ analytics.risk_counts.get('High',0) }}</span>
            <span class="pill">{{ t('medium') }}: {{ analytics.risk_counts.get('Medium',0) }}</span>
            <span class="pill">{{ t('low') }}: {{ analytics.risk_counts.get('Low',0) }}</span>
          </div>

          <h3>{{ t('top_conditions') }}</h3>
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

          <h3>{{ t('common_danger_signs') }}</h3>
          {% if analytics.danger_signs|length == 0 %}
            <p class="muted">No data yet.</p>
          {% else %}
            <ul>
              {% for name, cnt in analytics.danger_signs %}
                <li>{{ name }} — {{ cnt }}</li>
              {% endfor %}
            </ul>
          {% endif %}

          <div class="divider"></div>

          <h3>{{ t('assessor_performance') }}</h3>
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
          <h2>{{ t('quick_guidance') }}</h2>
          <ul>
            <li>Start with danger signs.</li>
            <li>Measure breathing rate if possible.</li>
            <li>Measure MUAC for 6–59 months when available.</li>
            <li>If unsure, arrange follow-up or refer per local protocol.</li>
          </ul>
        </section>

        <section class="card" aria-label="Privacy">
          <h2>{{ t('privacy') }}</h2>
          <p class="muted">{{ t('privacy_text') }}</p>
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
        clearRadioGroup('not_feeding');
        clearRadioGroup('stim_only');
        return;
      }

      // If nothing selected yet, default to "No"
      if (!document.querySelector('input[name="not_feeding"]:checked')) setRadio('not_feeding', 'No');
      if (!document.querySelector('input[name="stim_only"]:checked')) setRadio('stim_only', 'No');
    }

    document.addEventListener('DOMContentLoaded', () => {
      const age = document.getElementById('age_group');
      if (age) age.addEventListener('change', syncYoungInfant);
      syncYoungInfant();
    });
  </script>

  <!-- Google Translate (client-side, any language) -->
  <script>
    function googleTranslateElementInit() {
      new google.translate.TranslateElement(
        {
          pageLanguage: "{{ 'sw' if lang=='sw' else ('hi' if lang=='hi' else 'en') }}",
          autoDisplay: false
        },
        "google_translate_element"
      );
    }
  </script>
  <script src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
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

    # migrations (safe)
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

def compute_result(a: dict, lang: str, selected_patient=None):
    t = make_t(lang)

    wa_caregiver = digits_only(a.get("wa_caregiver", ""))
    wa_supervisor = digits_only(a.get("wa_supervisor", ""))

    include_name = (a.get("include_name", "No") == "Yes")
    include_village = (a.get("include_village", "No") == "Yes")
    assessor = (a.get("assessor") or "").strip()

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
        if not_feeding: scores["Neonatal complications"] += 3.5
        if stim_only: scores["Neonatal complications"] += 3.5

    high_triggers = []
    if danger: high_triggers.append("danger")
    if oedema or muac == "red": high_triggers.append("sam")
    if (cough and (chest_indrawing or stridor)) or (cough and fast_breathing and age == "0_2m"): high_triggers.append("breathing")
    if age == "0_2m" and (not_feeding or stim_only or fast_breathing or chest_indrawing or fever): high_triggers.append("young_infant")

    probs = softmax(scores)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    top_name, top_p = sorted_probs[0]
    certainty = int(round(top_p * 100))

    alt = [(condition_label(lang, n), int(round(p * 100))) for n, p in sorted_probs[1:3]]
    top_label = condition_label(lang, top_name)

    if high_triggers:
        risk = "High"
        box_class = "danger"
    elif certainty >= 80:
        risk = "Medium"
        box_class = "warn"
    else:
        risk = "Low"
        box_class = "ok"

    actions = []
    tips = []

    if risk == "High":
        actions.append(t("act_refer_urgent"))
        actions.append(t("act_keep_warm_feed"))
        if rdt == "positive":
            actions.append(t("act_malaria_protocol"))
        if muac == "red" or oedema:
            actions.append(t("act_sam_assess"))
    else:
        actions.append(t("act_follow_local"))
        if top_name == "Pneumonia":
            actions.append(t("act_pneumonia_same_day"))
        if top_name == "Malaria":
            actions.append(t("act_malaria_test"))
        if top_name == "Malnutrition":
            actions.append(t("act_muac_link"))
        if top_name == "Neonatal complications":
            actions.append(t("act_young_infant_prompt"))

    if top_name == "Pneumonia":
        tips += [t("tip_keep_warm"), t("tip_feed_fluids"), t("tip_breathing_urgent")]
    elif top_name == "Malaria":
        tips += [t("tip_fever_care"), t("tip_get_rdt"), t("tip_severe_malaria_urgent")]
    elif top_name == "Malnutrition":
        tips += [t("tip_bf_continue"), t("tip_small_meals"), t("tip_safe_water")]
    else:
        tips += [t("tip_skin_to_skin"), t("tip_bf_frequent"), t("tip_neonate_urgent")]

    action_short = actions[:2]
    alt_text = ", ".join([f"{n} {pct}%" for n, pct in alt if n])

    share_lines = [t("share_header")]

    if selected_patient and include_name:
        share_lines.append(t("share_patient", name=selected_patient["name"]))
    if selected_patient and include_village and selected_patient.get("village"):
        share_lines.append(t("share_village", village=selected_patient["village"]))

    share_lines.append(t("share_risk", risk=risk))
    share_lines.append(t("share_most_likely", cond=top_label, pct=certainty))
    if alt_text:
        share_lines.append(t("share_also", alt=alt_text))
    share_lines.append(t("share_next_steps"))
    share_lines += [f"- {s}" for s in action_short]
    if danger:
        share_lines.append(t("share_danger_present"))

    share_message = "\n".join([x for x in share_lines if x.strip()])

    return {
        "risk": risk,
        "top_condition": top_label,
        "top_condition_label": top_label,
        "certainty": certainty,
        "alternatives": alt,
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
            assessor_rollup.setdefault(assessor, {"total": 0, "high": 0})
            assessor_rollup[assessor]["total"] += 1
            if risk == "High":
                assessor_rollup[assessor]["high"] += 1

        try:
            a = json.loads(r["raw_answers"] or "{}")
        except Exception:
            a = {}

        if a.get("ds_drink") == "Yes": danger_counts["Not able to drink/breastfeed"] += 1
        if a.get("ds_vomit") == "Yes": danger_counts["Vomits everything"] += 1
        if a.get("ds_convulsions") == "Yes": danger_counts["Convulsions"] += 1
        if a.get("ds_lethargy") == "Yes": danger_counts["Very sleepy/unconscious"] += 1

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

    lang = (request.args.get("lang") or request.form.get("lang") or "en").strip().lower()
    if lang not in TRANSLATIONS:
        lang = "en"
    t = make_t(lang)

    patient_id = (request.args.get("patient_id") or "").strip()

    ar = (request.args.get("ar") or request.form.get("ar") or "30").strip()   # 7, 30, all
    aa = (request.args.get("aa") or request.form.get("aa") or "").strip()     # assessor name

    message = None
    result = None
    form_data = {}

    conn = get_conn()

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
                return redirect(url_for("index", patient_id=new_id, ar=ar, aa=aa, lang=lang))

        elif action == "delete_patient":
            del_id = (request.form.get("patient_id") or "").strip()
            if del_id.isdigit():
                conn.execute("DELETE FROM screenings WHERE patient_id = ?", (int(del_id),))
                conn.execute("DELETE FROM patients WHERE id = ?", (int(del_id),))
                conn.commit()
                if patient_id == del_id:
                    conn.close()
                    return redirect(url_for("index", ar=ar, aa=aa, lang=lang))
            else:
                message = "Invalid patient id."

        elif action == "run_screening":
            selected_patient = None
            if patient_id.isdigit():
                row = conn.execute("SELECT * FROM patients WHERE id = ?", (int(patient_id),)).fetchone()
                if row:
                    selected_patient = dict(row)

            result = compute_result(form_data, lang=lang, selected_patient=selected_patient)

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

    # patients
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

    # history
    history = []
    if selected_patient:
        rows = conn.execute(
            "SELECT created_at, risk, top_condition, certainty FROM screenings WHERE patient_id = ? ORDER BY id DESC LIMIT 5",
            (int(patient_id),),
        ).fetchall()
        history = [dict(x) for x in rows]

    # assessor dropdown
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
        t=t,
        lang=lang,
        lang_choices=LANG_CHOICES,
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
