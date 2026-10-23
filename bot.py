import os
import sys
import time
import json
import queue
import urllib.parse
import hashlib
import threading
import sqlite3
import requests
import feedparser
import urllib3
import re
import html
import random
import base64
import logging
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d-%m-%Y %I:%M:%S %p'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DB_FILE = "current_affairs_master.db"
SETTINGS_FILE = "bot_settings.json"
CUSTOM_BACKUP_FILE = "user_added_sources.json"

# PROTOCOL BUILDERS (Brackets and Markdown hyperlink proof)
TG_BASE = "".join(["http", "s://", "api.", "telegram.", "org", "/bot"])
GEMINI_BASE = "".join(["http", "s://", "generativelanguage.", "googleapis.", "com", "/v1beta/models/"])

def get_current_time():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p")

def get_current_ist_datetime():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist)

def clean_env_var(val):
    if not val:
        return ""
    v = str(val).strip()
    v = re.sub(r'\[.*?\]\(.*?\)', '', v)
    v = re.sub(r'https?://[^\s]+', '', v)
    return v.replace("[", "").replace("]", "").replace("(", "").replace(")", "").strip()

def clean_telegram_token(raw_val):
    if not raw_val:
        return ""
    m = re.search(r'(\d{8,11}:[A-Za-z0-9_-]{30,40})', str(raw_val))
    if m:
        return m.group(1).strip()
    return clean_env_var(raw_val)

TELEGRAM_BOT_TOKEN = clean_telegram_token(os.getenv("TELEGRAM_BOT_TOKEN", ""))
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
GEMINI_API_KEY = clean_env_var(os.getenv("GEMINI_API_KEY", ""))
GITHUB_TOKEN = clean_env_var(os.getenv("GITHUB_TOKEN", ""))
GITHUB_REPO = os.getenv("GITHUB_REPO", "sandeep012rr/news-auto-bot").strip()
PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL", "@currentaffair_news").strip()

WHATSAPP_GROUP_LINK = "".join(["http", "s://chat.whatsapp.com/CorqFF4smxf7fraUl7gSUP?s=cl&p=a&mlu=4&ilr=4"])

bot_mode = "both"
post_interval_seconds = 35
is_bot_active = True
auto_daily_pdf_active = True
last_pdf_sent_date = ""

pinned_msg_id = None
live_scan_count = 0
current_scan_progress = 0
last_active_portal_name = "Ready"

broadcast_queue = queue.Queue()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "hi-IN,hi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache"
}

DEFAULT_IMG_IN = "".join(["http", "s://images.unsplash.com/photo-1532375810709-75b1da00537c?w=1280&h=720&fit=crop"])
DEFAULT_IMG_RJ = "".join(["http", "s://images.unsplash.com/photo-1599661046289-e31897846e41?w=1280&h=720&fit=crop"])

PERMANENT_PORTALS = [
    ("PIB समग्र राष्ट्रीय समाचार", "https://pib.gov.in/RssMain.aspx?ModId=6&LangId=2", "महत्वपूर्ण घटनाएं", "rss", DEFAULT_IMG_IN),
    ("DIPR राजस्थान सरकार", "https://dipr.rajasthan.gov.in/press-release-list/85", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("दिव्यांगजन सशक्तिकरण विभाग (DEPwD)", "https://depwd.gov.in/en/whats-new/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("दिव्यांगजन सशक्तिकरण पोर्टल (Main)", "https://depwd.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("भारतीय कृत्रिम अंग निर्माण निगम (ALIMCO)", "https://alimco.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("सामाजिक न्याय एवं अधिकारिता मंत्रालय", "https://socialjustice.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("भारतीय पुनर्वास परिषद (RCI)", "https://rehabcouncil.nic.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Tribal Affairs", "https://tribal.nic.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Minority Affairs", "https://minorityaffairs.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Women and Child Development", "https://wcd.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Prime Minister's Office", "https://www.pmindia.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("President of India", "https://presidentofindia.nic.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Cabinet Secretariat", "https://cabsec.nic.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Education", "https://www.education.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Finance", "https://www.finmin.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Home Affairs", "https://www.mha.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Defence", "https://www.mod.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of External Affairs", "https://www.mea.gov.in/", "अंतर्राष्ट्रीय समसामयिकी", "web", DEFAULT_IMG_IN),
    ("Ministry of Health and Family Welfare", "https://mohfw.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Agriculture and Farmers Welfare", "https://agriwelfare.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Labour and Employment", "https://labour.gov.in/", "कौशल विकास और स्टार्ट-अप पहल", "web", DEFAULT_IMG_IN),
    ("Ministry of Law and Justice", "https://lawmin.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Railways", "https://indianrailways.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Road Transport and Highways", "https://morth.nic.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Ministry of Communications", "https://dot.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("Ministry of Electronics and IT (MeitY)", "https://www.meity.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("Ministry of Environment Forest and Climate Change", "https://moef.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("Ministry of Jal Shakti", "https://jalshakti-dowr.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Rural Development", "https://rural.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Panchayati Raj", "https://panchayat.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Youth Affairs and Sports", "https://yas.gov.in/", "खेल और खिलाड़ी", "web", DEFAULT_IMG_IN),
    ("Ministry of Corporate Affairs", "https://www.mca.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of Commerce and Industry", "https://www.commerce.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_IN),
    ("Ministry of MSME", "https://msme.gov.in/", "कौशल विकास और स्टार्ट-अप पहल", "web", DEFAULT_IMG_IN),
    ("Ministry of Skill Development", "https://www.msde.gov.in/", "कौशल विकास और स्टार्ट-अप पहल", "web", DEFAULT_IMG_IN),
    ("Ministry of Science and Technology", "https://dst.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("ISRO (Department of Space)", "https://www.isro.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("Unique Identification Authority (UIDAI)", "https://uidai.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_IN),
    ("Union Public Service Commission", "https://upsc.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("Staff Selection Commission", "https://ssc.gov.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("National Testing Agency", "https://nta.ac.in/", "महत्वपूर्ण घटनाएं", "web", DEFAULT_IMG_IN),
    ("National Career Service", "https://www.ncs.gov.in/", "कौशल विकास और स्टार्ट-अप पहल", "web", DEFAULT_IMG_IN),
    ("वित्त विभाग राजस्थान (Finance)", "https://finance.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("शिक्षा विभाग (Shala Darpan)", "https://rajshaladarpan.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("आबकारी विभाग (Excise Dept)", "https://excise.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("सामान्य प्रशासन विभाग (GAD)", "https://gad.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("गृह विभाग राजस्थान (Home Dept)", "https://home.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("सूचना प्रौद्योगिकी विभाग (DOITC)", "https://doitc.rajasthan.gov.in/", "विज्ञान, प्रौद्योगिकी और पर्यावरण", "web", DEFAULT_IMG_RJ),
    ("कार्मिक विभाग राजस्थान (DOP)", "https://dop.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("सामाजिक न्याय एवं अधिकारिता (SJE RJ)", "https://sje.rajasthan.gov.in/", "सामाजिक और आर्थिक संकेतक", "web", DEFAULT_IMG_RJ),
    ("पंजीयन एवं मुद्रांक विभाग (IGRS)", "https://igrs.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("राजस्थान लोक सेवा आयोग (RPSC)", "https://rpsc.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("राजस्थान कर्मचारी चयन बोर्ड (RSSB)", "https://rssb.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("माध्यमिक शिक्षा बोर्ड राजस्थान (RBSE)", "https://rajeduboard.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("राजस्थान पुलिस (Rajasthan Police)", "https://police.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("राजस्थान संपर्क पोर्टल (Sampark)", "https://sampark.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ),
    ("जन सूचना पोर्टल राजस्थान", "https://jansoochna.rajasthan.gov.in/", "राजस्थान समसामयिकी", "web", DEFAULT_IMG_RJ)
]

DEPARTMENT_SCHEME_DIRECTORY = [
    {
        "dept": "सामाजिक न्याय एवं अधिकारिता विभाग (SJE Rajasthan)",
        "portal": "https://sje.rajasthan.gov.in/",
        "schemes": [
            "पालनहार योजना (Palanhar Scheme)",
            "मुख्यमंत्री अनुप्रति कोचिंग योजना",
            "राजस्थान विशेष योग्यजन पेंशन योजना",
            "मुख्यमंत्री वृद्धजन सम्मान पेंशन योजना",
            "मुख्यमंत्री एकल नारी सम्मान पेंशन योजना",
            "मुख्यमंत्री कन्यादान / हथलेवा योजना"
        ]
    },
    {
        "dept": "चिकित्सा एवं स्वास्थ्य विभाग, राजस्थान",
        "portal": "https://chiranjeevi.rajasthan.gov.in/",
        "schemes": [
            "मुख्यमंत्री आयुष्मान आरोग्य योजना (MAA)",
            "मुख्यमंत्री निःशुल्क दवा योजना",
            "मुख्यमंत्री निःशुल्क जांच योजना",
            "निरोगी राजस्थान अभियान",
            "शुद्ध के लिए युद्ध अभियान"
        ]
    },
    {
        "dept": "उच्च एवं माध्यमिक शिक्षा विभाग, राजस्थान",
        "portal": "https://rajeduboard.rajasthan.gov.in/",
        "schemes": [
            "कालीबाई भील मेधावी छात्रा स्कूटी योजना",
            "देवनारायण छात्रा स्कूटी एवं प्रोत्साहन राशि योजना",
            "मुख्यमंत्री बाल गोपाल योजना (दूध वितरण)",
            "मुख्यमंत्री निःशुल्क यूनिफॉर्म वितरण योजना",
            "महात्मा गांधी अंग्रेजी माध्यम विद्यालय योजना"
        ]
    },
    {
        "dept": "स्वायत्त शासन विभाग (LSG Rajasthan)",
        "portal": "https://urban.rajasthan.gov.in/",
        "schemes": [
            "श्री अन्नपूर्णा रसोई योजना (मात्र ₹8 में थाली)",
            "इंदिरा गांधी शहरी रोजगार गारंटी योजना (125 दिन रोजगार)",
            "इंदिरा गांधी शहरी क्रेडिट कार्ड योजना"
        ]
    },
    {
        "dept": "दिव्यांगजन सशक्तिकरण विभाग (DEPwD, भारत सरकार)",
        "portal": "https://depwd.gov.in/",
        "schemes": [
            "ADIP योजना (सहायक उपकरण एवं कृत्रिम अंग वितरण)",
            "स्वावलंबन कार्ड (UDID Unique Disability ID Project)",
            "सुगम्य भारत अभियान (Accessible India Campaign)",
            "दिव्यांगजन राष्ट्रीय छात्रवृत्ति योजना"
        ]
    },
    {
        "dept": "कौशल विकास एवं सूक्ष्म, लघु उद्यम मंत्रालय (MSME)",
        "portal": "https://msme.gov.in/",
        "schemes": [
            "प्रधानमंत्री विश्वकर्मा योजना (PM Vishwakarma)",
            "प्रधानमंत्री रोजगार सृजन कार्यक्रम (PMEGP)",
            "उद्यम पंजीकरण एवं क्रेडिट गारंटी योजना"
        ]
    },
    {
        "dept": "कृषि एवं किसान कल्याण मंत्रालय, भारत सरकार",
        "portal": "https://agriwelfare.gov.in/",
        "schemes": [
            "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN ₹6000/वर्ष)",
            "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
            "किसान क्रेडिट कार्ड (KCC) योजना",
            "मृदा स्वास्थ्य कार्ड (Soil Health Card) योजना"
        ]
    },
    {
        "dept": "महिला एवं बाल विकास मंत्रालय, भारत सरकार",
        "portal": "https://wcd.gov.in/",
        "schemes": [
            "मिशन शक्ति (संबल एवं सामर्थ्य उप-योजनाएं)",
            "मिशन वात्सल्य (बाल कल्याण एवं सुरक्षा)",
            "प्रधानमंत्री मातृ वंदना योजना (PMMVY)",
            "सक्षम आंगनवाड़ी एवं पोषण 2.0"
        ]
    },
    {
        "dept": "आवासन और शहरी कार्य मंत्रालय, भारत सरकार",
        "portal": "https://pmay-urban.gov.in/",
        "schemes": [
            "प्रधानमंत्री आवास योजना - शहरी (PMAY-U)",
            "प्रधानमंत्री आवास योजना - ग्रामीण (PMAY-G)",
            "पीएम स्वनिधि योजना (स्ट्रीट वेंडर्स आत्मनिर्भर निधि)"
        ]
    }
]

GARBAGE_KEYWORDS = [
    "screen reader", "skip to", "login", "feedback", "tender",
    "sitemap", "gallery", "disclaimer", "privacy policy", "copyright",
    "about us", "contact us", "citizen charter", "rti", "vigilance",
    "terms of use", "web policy", "help desk",
    "monthly one liner", "download pdf", "free ebook", "mock test",
    "capsule pdf", "question paper pdf", "quiz questions", "free pdf"
]

def is_garbage_title(title_text):
    t = title_text.strip().lower()
    if len(t) < 12:
        return True
    return any(bad in t for bad in GARBAGE_KEYWORDS)

def load_user_custom_sources():
    if not os.path.exists(CUSTOM_BACKUP_FILE):
        return []
    try:
        with open(CUSTOM_BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cleaned = [x for x in data if "testbook.com" not in x.get("url", "").lower() and "adda247.com" not in x.get("url", "").lower()]
            return cleaned
    except Exception as e:
        logger.error(f"Error loading custom sources: {e}")
        return []

def save_user_custom_sources(sources_list):
    try:
        cleaned = [x for x in sources_list if "testbook.com" not in x.get("url", "").lower() and "adda247.com" not in x.get("url", "").lower()]
        with open(CUSTOM_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving custom sources: {e}")

if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            SOURCE_CHANNEL = cfg.get("channel", SOURCE_CHANNEL)
            bot_mode = cfg.get("mode", bot_mode)
            post_interval_seconds = cfg.get("interval", post_interval_seconds)
            auto_daily_pdf_active = cfg.get("auto_pdf", auto_daily_pdf_active)
            pinned_msg_id = cfg.get("pinned_msg_id", None)
    except Exception as e:
        logger.error(f"Settings load error: {e}")

def save_bot_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "channel": SOURCE_CHANNEL,
                "mode": bot_mode,
                "interval": post_interval_seconds,
                "auto_pdf": auto_daily_pdf_active,
                "pinned_msg_id": pinned_msg_id
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Settings save error: {e}")

def init_master_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sent_news (
            hash TEXT PRIMARY KEY,
            title TEXT,
            category TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE,
            category TEXT,
            feed_type TEXT,
            img_url TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS monthly_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            facts TEXT,
            date TEXT,
            date_only TEXT
        )
    """)
    conn.commit()

    c.execute("DELETE FROM custom_sources WHERE url LIKE '%testbook.com%' OR url LIKE '%adda247.com%'")
    conn.commit()

    c.executemany("""
        INSERT OR REPLACE INTO custom_sources (name, url, category, feed_type, img_url)
        VALUES (?, ?, ?, ?, ?)
    """, PERMANENT_PORTALS)

    saved_custom = load_user_custom_sources()
    for item in saved_custom:
        c.execute("""
            INSERT OR REPLACE INTO custom_sources (name, url, category, feed_type, img_url)
            VALUES (?, ?, ?, ?, ?)
        """, (item["name"], item["url"], item["category"], item.get("type", "rss"), item.get("img", DEFAULT_IMG_IN)))

    conn.commit()
    conn.close()

init_master_db()

sent_hashes = set()
def reload_sent_hashes():
    global sent_hashes
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT hash FROM sent_news")
        sent_hashes = set(r[0] for r in c.fetchall())
        conn.close()
        logger.info(f"Loaded {len(sent_hashes)} sent hashes from database.")
    except Exception as e:
        logger.error(f"Error loading sent hashes: {e}")

reload_sent_hashes()

def get_normalized_signature(title_text):
    clean_words = "".join(ch for ch in title_text.lower() if ch.isalnum() or ch.isspace()).split()
    return hashlib.sha256("".join(clean_words[:6]).encode("utf-8")).hexdigest()

def is_news_already_sent(title_text):
    return get_normalized_signature(title_text) in sent_hashes

def record_news_as_sent(title_text, category, summary_str):
    thash = get_normalized_signature(title_text)
    sent_hashes.add(thash)
    now_dt = get_current_ist_datetime()
    date_only = now_dt.strftime("%d-%m-%Y")
    full_date = now_dt.strftime("%d-%m-%Y %I:%M %p")
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO sent_news (hash, title, category) VALUES (?, ?, ?)", (thash, title_text, category))
        c.execute("INSERT INTO monthly_archive (title, category, facts, date, date_only) VALUES (?, ?, ?, ?, ?)",
                  (title_text, category, summary_str, full_date, date_only))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error recording news: {e}")

def get_all_db_sources():
    sources = []
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, name, url, category, feed_type, img_url FROM custom_sources")
        for row in c.fetchall():
            sources.append({
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "category": row[3],
                "type": row[4],
                "img": row[5] or DEFAULT_IMG_IN
            })
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching sources from DB: {e}")
    return sources

def add_source_to_db(name, url, category, feed_type="rss"):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        img = DEFAULT_IMG_IN
        c.execute("INSERT OR REPLACE INTO custom_sources (name, url, category, feed_type, img_url) VALUES (?, ?, ?, ?, ?)",
                  (name, url, category, feed_type, img))
        conn.commit()
        conn.close()

        existing = load_user_custom_sources()
        if not any(x["url"] == url for x in existing):
            existing.append({"name": name, "url": url, "category": category, "type": feed_type, "img": img})
            save_user_custom_sources(existing)
        return True
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        return False

def delete_source_from_db(source_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT url FROM custom_sources WHERE id = ?", (source_id,))
        row = c.fetchone()
        target_url = row[0] if row else None

        c.execute("DELETE FROM custom_sources WHERE id = ?", (source_id,))
        conn.commit()
        conn.close()

        if target_url:
            existing = load_user_custom_sources()
            updated = [x for x in existing if x["url"] != target_url]
            save_user_custom_sources(updated)
        return True
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        return False

def make_progress_bar(percent):
    filled = int(percent / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

def build_counter_text():
    all_s = get_all_db_sources()
    bar = make_progress_bar(current_scan_progress)
    return (
        f"⚡ <b>BOT LIVE ACTIVITY MONITOR (24/7)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Status:</b> <code>ONLINE & ACTIVE</code>\n"
        f"🔄 <b>Checking Portal:</b> <code>{html.escape(last_active_portal_name)}</code>\n"
        f"📊 <b>Scan Progress:</b> <code>[{bar}] {current_scan_progress}%</code>\n"
        f"🔢 <b>Total Scans Completed:</b> <code>{live_scan_count}</code>\n"
        f"🌐 <b>Total Portals Monitored:</b> <code>{len(all_s)}</code>\n"
        f"📬 <b>Pending Queue:</b> <code>{broadcast_queue.qsize()} posts</code>\n"
        f"🕒 <b>Last Ping:</b> <code>{get_current_time()}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ℹ️ <i>Auto-update running every 60 seconds.</i>"
    )

def update_or_create_pinned_counter(chat_id):
    global pinned_msg_id
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return

    text = build_counter_text()
    token = TELEGRAM_BOT_TOKEN

    if pinned_msg_id:
        edit_url = TG_BASE + token + "/editMessageText"
        payload = {
            "chat_id": str(chat_id).strip(),
            "message_id": pinned_msg_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            r = requests.post(edit_url, json=payload, timeout=5).json()
            if r.get("ok"):
                return
        except Exception:
            pass

    send_url = TG_BASE + token + "/sendMessage"
    payload = {
        "chat_id": str(chat_id).strip(),
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(send_url, json=payload, timeout=8).json()
        if res.get("ok"):
            pinned_msg_id = res["result"]["message_id"]
            save_bot_settings()
            pin_url = TG_BASE + token + "/pinChatMessage"
            requests.post(pin_url, json={"chat_id": str(chat_id).strip(), "message_id": pinned_msg_id, "disable_notification": True}, timeout=5)
    except Exception as e:
        logger.error(f"Pin message error: {e}")

LAST_AI_CALL_TIME = 0
AI_MIN_INTERVAL = 2

def execute_self_code_modification(instruction):
    if not GITHUB_TOKEN:
        return False, "❌ Error: <code>GITHUB_TOKEN</code> environment variable set nahi hai. Render par add karein."
    if not GEMINI_API_KEY:
        return False, "❌ Error: <code>GEMINI_API_KEY</code> set nahi hai."

    headers = {
        "Authorization": "token " + GITHUB_TOKEN,
        "Accept": "application/vnd.github.v3+json"
    }
    url = "".join(["http", "s://api.", "github.", "com/repos/"]) + GITHUB_REPO + "/contents/bot.py?ref=main"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return False, f"❌ GitHub se file fetch nahi ho saki: {r.status_code} ({r.text[:120]})"

        file_data = r.json()
        current_sha = file_data["sha"]
        current_code = base64.b64decode(file_data["content"]).decode("utf-8")

        prompt = f"""
Aap ek elite Python system software engineer hain. Hamare pass production me chal raha Telegram bot hai (bot.py).
User ki demand ke anusaar code ko MODIFY karein.

USER INSTRUCTION:
{instruction}

CURRENT CODE:
{current_code}

CRITICAL RULES:
1. Complete executable Python code return karein.
2. Sirf aur sirf pure Python code output karein.
3. Koi function ya permanent portals delete na karein jab tak user na kahe.
4. Syntax aur indentation 100% correct honi chahiye.
"""
        ai_url = GEMINI_BASE + "gemini-1.5-pro:generateContent?key=" + GEMINI_API_KEY
        ai_resp = requests.post(ai_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=90)

        if ai_resp.status_code != 200:
            return False, "❌ Gemini code generate nahi kar paya."

        raw_text = ai_resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        new_code = raw_text.strip()
        if new_code.startswith("```python"):
            new_code = new_code[len("```python"):].strip()
        if new_code.startswith("```"):
            new_code = new_code[len("```"):].strip()
        if new_code.endswith("```"):
            new_code = new_code[:-3].strip()

        try:
            compile(new_code, "<string>", "exec")
        except Exception as compile_err:
            return False, f"⚠️ Syntax Error detected: {compile_err}. Auto-update abort kar diya gaya hai."

        encoded_content = base64.b64encode(new_code.encode("utf-8")).decode("utf-8")
        commit_payload = {
            "message": f"🤖 Autonomous Self-Update: {instruction[:45]}",
            "content": encoded_content,
            "sha": current_sha,
            "branch": "main"
        }

        put_resp = requests.put(url, headers=headers, json=commit_payload, timeout=20)
        if put_resp.status_code in [200, 201]:
            return True, "✅ <b>Code Successfully GitHub Par Update Ho Gaya!</b>\nRender ab automatically naya build deploy kar raha hai (1-2 minute me live hoga)."
        else:
            return False, f"❌ GitHub Commit failed: {put_resp.status_code} ({put_resp.text[:120]})"

    except Exception as e:
        return False, f"❌ Self-code update exception: {str(e)}"

def generate_short_facts_and_quiz(title, raw_text, default_category):
    global LAST_AI_CALL_TIME
    if not GEMINI_API_KEY:
        return default_category, None, None

    elapsed = time.time() - LAST_AI_CALL_TIME
    if elapsed < AI_MIN_INTERVAL:
        time.sleep(AI_MIN_INTERVAL - elapsed)

    prompt = f"""
Aap ek senior competitive exam mentor hain. Di gayi sarkari release ko dhyan se padhein aur bina kisi formality ke puri khabar ka sachha saransh banayein.

RULES:
1. TOPIC: Inme se chuney (राजस्थान समसामयिकी, सामाजिक और आर्थिक संकेतक, विज्ञान, प्रौद्योगिकी और पर्यावरण, खेल और खिलाड़ी, कौशल विकास और स्टार्ट-अप पहल, महत्वपूर्ण घटनाएं, अंतर्राष्ट्रीय समसामयिकी).
2. SUMMARY: 3 se 4 factual sentences me likhein ki kya nirnay hua, kisne shuru kiya, aur iska aam nagrikon/chhatron par kya asar padega.
3. QUIZ: Isi ghatna par aadharit 1 Telegram Poll MCQ banayein (Question <= 100 chars, Options <= 40 chars).

Strict Output Format:
TOPIC: [Topic Name]
SUMMARY: [Puri khabar ka vistrit factual saransh]
QUIZ:
Q: [Question]
O1: [Option 1]
O2: [Option 2]
O3: [Option 3]
O4: [Option 4]
ANS: [1/2/3/4]
EXP: [Explanation in 1 short line]

Title: {title}
Content: {raw_text[:3500]}
"""
    url = GEMINI_BASE + "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        LAST_AI_CALL_TIME = time.time()
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            ai_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            detected_topic = default_category
            summary_lines = []
            quiz_data = {}
            section = None

            for line in ai_text.split("\n"):
                l = line.strip()
                if l.startswith("TOPIC:"):
                    detected_topic = l.replace("TOPIC:", "").strip()
                elif l.startswith("SUMMARY:"):
                    section = "summary"
                    c = l.replace("SUMMARY:", "").strip()
                    if c: summary_lines.append(c)
                elif l.startswith("QUIZ:"):
                    section = "quiz"
                elif section == "summary":
                    if l: summary_lines.append(l)
                elif section == "quiz":
                    if l.startswith("Q:"): quiz_data["question"] = l.replace("Q:", "").strip()
                    elif l.startswith("O1:"): quiz_data["opt1"] = l.replace("O1:", "").strip()
                    elif l.startswith("O2:"): quiz_data["opt2"] = l.replace("O2:", "").strip()
                    elif l.startswith("O3:"): quiz_data["opt3"] = l.replace("O3:", "").strip()
                    elif l.startswith("O4:"): quiz_data["opt4"] = l.replace("O4:", "").strip()
                    elif l.startswith("ANS:"):
                        digits = re.findall(r'\d+', l)
                        quiz_data["correct_id"] = int(digits[0]) - 1 if digits else 0
                    elif l.startswith("EXP:"): quiz_data["explanation"] = l.replace("EXP:", "").strip()

            full_summary = " ".join(summary_lines).strip()

            valid_quiz = None
            if "question" in quiz_data and "opt4" in quiz_data and "correct_id" in quiz_data:
                valid_quiz = {
                    "question": quiz_data["question"][:250],
                    "options": [quiz_data["opt1"][:90], quiz_data["opt2"][:90], quiz_data["opt3"][:90], quiz_data["opt4"][:90]],
                    "correct_option_id": max(0, min(3, quiz_data.get("correct_id", 0))),
                    "explanation": quiz_data.get("explanation", "आधिकारिक विज्ञप्ति पर आधारित।")[:180]
                }

            if len(full_summary) > 20:
                return detected_topic, full_summary, valid_quiz
    except Exception as e:
        logger.error(f"Gemini API Call Exception: {e}")

    return default_category, None, None

def generate_ai_scheme_post(scheme_name, dept_context="", official_link=""):
    if not GEMINI_API_KEY:
        return None, None, None, None

    prompt = f"""
Aap Rajasthan aur Kendriya (Bharat Sarkar) pratiyogi parikshaon ke senior vishleshak hain.
Neeche di gayi yojana ko VISTAR SE aur PURE FACTUAL format me samjhaiye:

Yojana: {scheme_name}
Vibhag Context: {dept_context}

RULES:
1. TOPIC: 'राजस्थान समसामयिकी' ya 'सामाजिक और आर्थिक संकेतक'
2. DEPT: Yojana ko chalane wala verified vibhag/mantralaya.
3. SUMMARY: 3-4 factual sentences me vistaar se batayein (Mukhya Uddeshya, Patrata, aur Labh).
4. QUIZ: Isi yojana par aadharit 1 Telegram Poll MCQ (Question <= 120 chars, Options <= 45 chars).

Strict Output Format:
TOPIC: [Topic Name]
DEPT: [Ministry / Department Name]
SUMMARY: [Vistrit Factual Saransh]
QUIZ:
Q: [Question]
O1: [Option 1]
O2: [Option 2]
O3: [Option 3]
O4: [Option 4]
ANS: [1/2/3/4]
EXP: [Explanation in 1 short line]
"""
    url = GEMINI_BASE + "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, json=payload, timeout=14)
        if resp.status_code == 200:
            ai_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            detected_topic = "सामाजिक और आर्थिक संकेतक"
            dept_name = dept_context or "भारत / राजस्थान सरकार"
            summary_lines = []
            quiz_data = {}
            section = None

            for line in ai_text.split("\n"):
                l = line.strip()
                if l.startswith("TOPIC:"):
                    detected_topic = l.replace("TOPIC:", "").strip()
                elif l.startswith("DEPT:"):
                    dept_name = l.replace("DEPT:", "").strip()
                elif l.startswith("SUMMARY:"):
                    section = "summary"
                    c = l.replace("SUMMARY:", "").strip()
                    if c: summary_lines.append(c)
                elif l.startswith("QUIZ:"):
                    section = "quiz"
                elif section == "summary":
                    if l: summary_lines.append(l)
                elif section == "quiz":
                    if l.startswith("Q:"): quiz_data["question"] = l.replace("Q:", "").strip()
                    elif l.startswith("O1:"): quiz_data["opt1"] = l.replace("O1:", "").strip()
                    elif l.startswith("O2:"): quiz_data["opt2"] = l.replace("O2:", "").strip()
                    elif l.startswith("O3:"): quiz_data["opt3"] = l.replace("O3:", "").strip()
                    elif l.startswith("O4:"): quiz_data["opt4"] = l.replace("O4:", "").strip()
                    elif l.startswith("ANS:"):
                        digits = re.findall(r'\d+', l)
                        quiz_data["correct_id"] = int(digits[0]) - 1 if digits else 0
                    elif l.startswith("EXP:"): quiz_data["explanation"] = l.replace("EXP:", "").strip()

            full_summary = " ".join(summary_lines).strip()
            valid_quiz = None
            if "question" in quiz_data and "opt4" in quiz_data and "correct_id" in quiz_data:
                valid_quiz = {
                    "question": quiz_data["question"][:250],
                    "options": [quiz_data["opt1"][:90], quiz_data["opt2"][:90], quiz_data["opt3"][:90], quiz_data["opt4"][:90]],
                    "correct_option_id": max(0, min(3, quiz_data.get("correct_id", 0))),
                    "explanation": quiz_data.get("explanation", "आधिकारिक पोर्टल पर आधारित तथ्य।")[:180]
                }
            return detected_topic, dept_name, full_summary, valid_quiz
    except Exception as e:
        logger.error(f"Gemini Scheme Error: {e}")
    return None, None, None, None

def dispatch_auto_department_scheme():
    global broadcast_queue
    try:
        all_candidates = []
        for d in DEPARTMENT_SCHEME_DIRECTORY:
            for sc in d["schemes"]:
                all_candidates.append({
                    "scheme": sc,
                    "dept": d["dept"],
                    "portal": d["portal"]
                })

        unsent = [c for c in all_candidates if not is_news_already_sent(c["scheme"])]
        chosen = unsent[0] if unsent else random.choice(all_candidates)

        topic, dept_name, summary, quiz = generate_ai_scheme_post(chosen["scheme"], chosen["dept"], chosen["portal"])

        if not summary or len(summary) < 20:
            summary = f"यह योजना {chosen['dept']} द्वारा पात्र नागरिकों एवं विद्यार्थियों के सामाजिक-आर्थिक उत्थान हेतु संचालित है।"

        safe_title = html.escape(chosen["scheme"].strip())
        safe_dept = html.escape((dept_name or chosen["dept"]).strip())
        safe_cat = html.escape(topic.strip() if topic else "सामाजिक और आर्थिक संकेतक")
        safe_sum = html.escape(summary.strip())[:480]
        link = chosen["portal"]

        is_rj = "राजस्थान" in safe_dept or "राजस्थान" in safe_title
        header_badge = "🏛️ <b>राजस्थान सरकार: प्रमुख फ्लैगशिप योजना</b>" if is_rj else "🇮🇳 <b>भारत सरकार: प्रमुख जनकल्याणकारी योजना</b>"

        caption = (
            f"{header_badge}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>{safe_title}</b>\n\n"
            f"🏢 <b>संचालक विभाग:</b> <code>{safe_dept}</code>\n"
            f"🏷️ <code>[ श्रेणी: {safe_cat} ]</code>\n\n"
            f"📝 <b>योजना का सार एवं मुख्य लाभ:</b>\n"
            f"{safe_sum}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <a href='{link}'>👉 आधिकारिक पोर्टल लिंक यहाँ देखें 👈</a>\n\n"
            f"📢 <b>Join Telegram:</b> {SOURCE_CHANNEL}\n"
            f"💬 <a href='{WHATSAPP_GROUP_LINK}'>👉 Join WhatsApp Group 👈</a>"
        )

        record_news_as_sent(chosen["scheme"], safe_cat, summary)
        tricolor_img = DEFAULT_IMG_RJ if is_rj else DEFAULT_IMG_IN

        broadcast_queue.put({
            "caption": caption,
            "img_url": tricolor_img,
            "title": chosen["scheme"],
            "quiz": quiz,
            "pdf_url": None,
            "dept_name": safe_dept
        })
        logger.info(f"[AUTO SCHEME QUEUED] {chosen['scheme']}")
        return True
    except Exception as e:
        logger.error(f"Error in auto scheme dispatch: {e}")
        return False

def build_post_caption(source_name, title, category, summary_text, link, has_pdf=False):
    safe_title = html.escape(title.strip())
    safe_category = html.escape(category.strip())
    safe_source = html.escape(source_name.strip())
    safe_summary = html.escape(summary_text.strip())[:520]

    header_tag = "📄 <b>आधिकारिक सरकारी परिपत्र (OFFICIAL PDF)</b>" if has_pdf else "🚨 <b>EXAM SPECIAL CURRENT AFFAIRS</b>"
    link_line = f'\n🔗 <a href="{link}">👉 पूरी आधिकारिक विज्ञप्ति यहाँ पढ़ें 👈</a>' if link and link.startswith("http") else ""

    caption = (
        f"{header_tag}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{safe_title}</b>\n\n"
        f"🏷️ <code>[ विषय: {safe_category} ]</code>\n\n"
        f"📝 <b>पूरी खबर का सार (Detailed Summary):</b>\n"
        f"{safe_summary}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ <b>प्रमाणित स्रोत:</b> <code>{safe_source}</code>"
        f"{link_line}\n\n"
        f"📢 <b>Join Telegram:</b> {SOURCE_CHANNEL}\n"
        f"💬 <a href='{WHATSAPP_GROUP_LINK}'>👉 Join WhatsApp Group 👈</a>"
    )
    return caption

def get_verified_gov_photo(article_url):
    if not article_url or not article_url.startswith("http") or article_url.lower().endswith(".pdf"):
        return DEFAULT_IMG_IN

    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=5, verify=False)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if any(k in src.lower() for k in ["static.pib.gov.in", "writereaddata", "pressrelease", "imgrelease", "wp-content/uploads"]):
                    return urllib.parse.urljoin(article_url, src.strip())
            og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og and og.get("content"):
                cand = og.get("content").strip()
                if cand.startswith("http") and not any(bad in cand.lower() for bad in ["logo", "icon", "default"]):
                    return cand
    except Exception:
        pass

    return DEFAULT_IMG_IN

def search_nested_pdf_link(article_url, soup_obj=None):
    if not article_url or not article_url.startswith("http"):
        return None

    if any(bad in article_url.lower() for bad in ["adda247.com", "testbook.com"]):
        return None

    if article_url.lower().endswith(".pdf") or ".pdf?" in article_url.lower():
        return article_url

    try:
        if not soup_obj:
            resp = requests.get(article_url, headers=HEADERS, timeout=6, verify=False)
            if resp.status_code == 200:
                soup_obj = BeautifulSoup(resp.text, "html.parser")

        if soup_obj:
            for a in soup_obj.find_all("a", href=True):
                href = a["href"].strip()
                text = a.get_text(separator=" ").strip().lower()
                full_link = urllib.parse.urljoin(article_url, href)

                if full_link.lower().endswith(".pdf") or ".pdf?" in full_link.lower():
                    return full_link

                if any(k in text for k in ["gazette", "circular", "order copy", "संलग्नक", "परिपत्र डाउनलोड"]):
                    if full_link.lower().endswith(".pdf"):
                        return full_link
    except Exception:
        pass

    return None

def send_telegram_official_pdf(target_chat_id, pdf_url, title, caption):
    if not TELEGRAM_BOT_TOKEN or not target_chat_id or not pdf_url:
        return False
    token = TELEGRAM_BOT_TOKEN
    try:
        pdf_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/octet-stream,*/*",
            "Referer": pdf_url
        }
        with requests.get(pdf_url, headers=pdf_headers, timeout=40, stream=True, verify=False, allow_redirects=True) as resp:
            if resp.status_code == 200:
                content = resp.content
                if not content.startswith(b"%PDF"):
                    logger.error("Corrupt file detected (Not genuine PDF).")
                    return False

                clean_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', title[:35]) + ".pdf"
                url = TG_BASE + token + "/sendDocument"
                files = {'document': (clean_filename, content, 'application/pdf')}
                data = {'chat_id': str(target_chat_id).strip(), 'caption': caption[:1024], 'parse_mode': 'HTML'}
                res = requests.post(url, data=data, files=files, timeout=60).json()
                return res.get("ok", False)
    except Exception as e:
        logger.error(f"PDF download or upload failed: {e}")
    return False

def send_telegram_photo(target_chat_id, caption, img_url):
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        return False
    token = TELEGRAM_BOT_TOKEN
    photo_url = TG_BASE + token + "/sendPhoto"
    payload = {"chat_id": str(target_chat_id).strip(), "photo": img_url, "caption": caption[:1024], "parse_mode": "HTML"}
    try:
        res = requests.post(photo_url, data=payload, timeout=12).json()
        if res.get("ok"):
            return True
        else:
            logger.error(f"Telegram Photo dispatch error: {res.get('description')}")
    except Exception:
        pass

    text_url = TG_BASE + token + "/sendMessage"
    try:
        res2 = requests.post(text_url, json={"chat_id": str(target_chat_id).strip(), "text": caption[:4000], "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=10).json()
        return res2.get("ok", False)
    except Exception:
        return False

def send_telegram_quiz_poll(target_chat_id, quiz_dict):
    if not TELEGRAM_BOT_TOKEN or not target_chat_id or not quiz_dict:
        return False
    token = TELEGRAM_BOT_TOKEN
    url = TG_BASE + token + "/sendPoll"
    q_text = f"🎯 {quiz_dict['question']}"[:300]
    opts = [str(o)[:100] for o in quiz_dict["options"][:4]]
    correct_id = int(quiz_dict.get("correct_option_id", 0))
    exp_text = str(quiz_dict.get("explanation", "परीक्षा उपयोगी तथ्य।"))[:190]

    payload = {
        "chat_id": str(target_chat_id).strip(),
        "question": q_text,
        "options": json.dumps(opts, ensure_ascii=False),
        "is_anonymous": False,
        "type": "quiz",
        "correct_option_id": correct_id,
        "explanation": exp_text
    }
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

def send_telegram_document(chat_id, file_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    token = TELEGRAM_BOT_TOKEN
    url = TG_BASE + token + "/sendDocument"
    try:
        with open(file_path, "rb") as f:
            r = requests.post(url, data={"chat_id": str(chat_id).strip(), "caption": caption[:1024]}, files={"document": f}, timeout=25)
            return r.status_code == 200
    except Exception:
        return False

def generate_and_dispatch_daily_digest(target_id=None):
    now_dt = get_current_ist_datetime()
    today_str = now_dt.strftime("%d-%m-%Y")
    display_date = now_dt.strftime("%d %B %Y")
    destination = target_id or SOURCE_CHANNEL

    if not destination:
        return False

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT category, title, facts FROM monthly_archive WHERE date_only = ? ORDER BY id ASC", (today_str,))
        rows = c.fetchall()

        if not rows:
            c.execute("SELECT category, title, facts FROM monthly_archive ORDER BY id DESC LIMIT 12")
            rows = c.fetchall()
        conn.close()

        if not rows:
            return False

        filename = f"Daily_Current_Affairs_{today_str}.doc"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"      DAILY CURRENT AFFAIRS EXAM DIGEST ({display_date})     \n")
            f.write("      राजस्थान और भारत समसामयिकी (विस्तृत परीक्षा सार)       \n")
            f.write("=" * 60 + "\n\n")

            for idx, r in enumerate(rows, 1):
                f.write(f"[{idx}] {r[1]}\n")
                f.write(f"🏷️ विषय/खंड: {r[0]}\n")
                f.write(f"📝 विस्तृत सार:\n{r[2]}\n")
                f.write("-" * 55 + "\n\n")

            f.write("\nनोट: यह दैनिक संकलन आधिकारिक सरकारी पोर्टलों पर आधारित है।\n")

        caption = (
            f"📚 *दैनिक करेंट अफेयर्स सम्पूर्ण संकलन (Daily Digest)*\n\n"
            f"📅 *दिनांक:* {display_date}\n"
            f"🎯 *कुल समसामयिक बिंदु:* {len(rows)} महत्वपूर्ण तथ्य\n\n"
            f"✅ आज दिन भर की समस्त विज्ञप्तियों एवं परीक्षा तथ्यों का संकलन संलग्न है।"
        )
        return send_telegram_document(destination, filename, caption)
    except Exception as e:
        logger.error(f"Daily digest generation error: {e}")
        return False

def daily_8pm_scheduler_worker():
    global last_pdf_sent_date, auto_daily_pdf_active
    while True:
        try:
            if auto_daily_pdf_active and is_bot_active and SOURCE_CHANNEL:
                now_ist = get_current_ist_datetime()
                today_str = now_ist.strftime("%d-%m-%Y")

                if now_ist.hour == 20 and now_ist.minute >= 0 and last_pdf_sent_date != today_str:
                    success = generate_and_dispatch_daily_digest(SOURCE_CHANNEL)
                    if success:
                        last_pdf_sent_date = today_str
                        if ADMIN_CHAT_ID:
                            generate_and_dispatch_daily_digest(ADMIN_CHAT_ID)
        except Exception:
            pass
        time.sleep(30)

def channel_forwarder_worker():
    global post_interval_seconds, SOURCE_CHANNEL, bot_mode
    while True:
        try:
            try:
                item = broadcast_queue.get(timeout=5)
            except queue.Empty:
                continue

            if is_bot_active and SOURCE_CHANNEL:
                dispatched_as_pdf = False

                if item.get("pdf_url"):
                    dispatched_as_pdf = send_telegram_official_pdf(SOURCE_CHANNEL, item["pdf_url"], item["title"], item["caption"])

                if not dispatched_as_pdf and bot_mode in ["both", "news_only"]:
                    send_telegram_photo(SOURCE_CHANNEL, item["caption"], item["img_url"])

                if bot_mode in ["both", "quiz_only"] and item.get("quiz"):
                    time.sleep(3)
                    send_telegram_quiz_poll(SOURCE_CHANNEL, item["quiz"])

                time.sleep(post_interval_seconds)
            broadcast_queue.task_done()
        except Exception as e:
            logger.error(f"Channel forwarder worker error: {e}")
            time.sleep(5)

def scrape_web_articles(page_url):
    articles = []
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=6, verify=False)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                title = a.get_text(separator=" ").strip()

                if is_garbage_title(title):
                    continue

                full_url = urllib.parse.urljoin(page_url, href)
                is_pdf = full_url.lower().endswith(".pdf") or "pdf" in href.lower()

                if is_pdf or len(title) > 15:
                    if not any(art["link"] == full_url for art in articles):
                        articles.append({
                            "title": title,
                            "link": full_url,
                            "is_pdf": is_pdf,
                            "pdf_url": full_url if is_pdf else None,
                            "summary": title
                        })
                if len(articles) >= 8:
                    break
    except Exception as e:
        logger.error(f"Web scraper error on {page_url}: {e}")
    return articles

def extract_gov_facts(article_url, summary_raw, title, default_cat, is_pdf=False):
    raw_text = summary_raw or title
    detected_nested_pdf = None

    if not is_pdf and article_url and article_url.startswith("http"):
        try:
            resp = requests.get(article_url, headers=HEADERS, timeout=6, allow_redirects=True, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                detected_nested_pdf = search_nested_pdf_link(article_url, soup)

                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "li", "td"]) if len(p.get_text().strip()) > 25]
                if paragraphs:
                    raw_text = " ".join(paragraphs[:15])
        except Exception:
            pass

    full_context = f"विभाग सूचना: {title}. विवरण: {raw_text}"
    topic, detailed_summary, quiz = generate_short_facts_and_quiz(title, full_context, default_cat)

    if not detailed_summary or len(detailed_summary) < 20:
        detailed_summary = f"आधिकारिक पोर्टल पर जारी नवीनतम विज्ञप्ति: '{title}'। यह सूचना प्रतियोगी परीक्षाओं एवं विभागीय अपडेट के दृष्टिकोण से महत्वपूर्ण है।"

    if not quiz:
        quiz = {
            "question": f"हाल ही में चर्चा में रहा '{title[:55]}...' किस विषय से संबंधित है?",
            "options": [f"{default_cat}", "राष्ट्रीय सुरक्षा", "पर्यावरण संरक्षण", "अन्य"],
            "correct_option_id": 0,
            "explanation": f"यह आधिकारिक अपडेट {default_cat} के अंतर्गत जारी किया गया है।"
        }

    final_pdf_url = detected_nested_pdf if detected_nested_pdf else (article_url if is_pdf else None)
    return topic or default_cat, detailed_summary, quiz, final_pdf_url

def scrape_all_sources():
    global current_scan_progress, last_active_portal_name, live_scan_count
    if not is_bot_active:
        return 0

    sources = get_all_db_sources()
    total_sources = len(sources)
    
    shuffled_sources = list(sources)
    random.shuffle(shuffled_sources)

    dept_buckets = {}
    total_found = 0

    for idx, s in enumerate(shuffled_sources, 1):
        last_active_portal_name = s["name"]
        current_scan_progress = int((idx / max(1, total_sources)) * 100)

        if ADMIN_CHAT_ID:
            update_or_create_pinned_counter(ADMIN_CHAT_ID)

        try:
            items_to_process = []
            feed_success = False

            try:
                resp = requests.get(s["url"], headers=HEADERS, timeout=5, verify=False)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    if feed.entries:
                        feed_success = True
                        for entry in feed.entries[:5]:
                            link = getattr(entry, "link", "") or getattr(entry, "id", "")
                            items_to_process.append({
                                "title": entry.title.strip(),
                                "link": link,
                                "is_pdf": link.lower().endswith(".pdf"),
                                "pdf_url": link if link.lower().endswith(".pdf") else None,
                                "summary": getattr(entry, "summary", "") or getattr(entry, "description", "")
                            })
            except Exception:
                pass

            if not feed_success:
                for a in scrape_web_articles(s["url"]):
                    items_to_process.append(a)

            current_dept_items = []
            for item in items_to_process:
                clean_title = item["title"].split(" - ")[0].strip()
                if is_garbage_title(clean_title) or is_news_already_sent(clean_title):
                    continue

                topic, detailed_summary, quiz, detected_pdf = extract_gov_facts(
                    item["link"], item["summary"], clean_title, s["category"], item.get("is_pdf", False)
                )

                if not topic or not detailed_summary:
                    continue

                has_pdf = bool(detected_pdf)
                caption = build_post_caption(s["name"], clean_title, topic, detailed_summary, item["link"], has_pdf=has_pdf)
                record_news_as_sent(clean_title, topic, detailed_summary)

                gov_photo = get_verified_gov_photo(item["link"])

                current_dept_items.append({
                    "caption": caption,
                    "img_url": gov_photo,
                    "title": clean_title,
                    "quiz": quiz,
                    "pdf_url": detected_pdf,
                    "dept_name": s["name"]
                })
                total_found += 1
                time.sleep(0.5)

            if current_dept_items:
                dept_buckets[s["name"]] = current_dept_items

        except Exception as e:
            logger.error(f"Scrape loop error on {s['name']}: {e}")

    mixed_queue_items = []
    has_items = True
    while has_items:
        has_items = False
        dept_names = list(dept_buckets.keys())
        random.shuffle(dept_names)

        for d_name in dept_names:
            if dept_buckets[d_name]:
                mixed_queue_items.append(dept_buckets[d_name].pop(0))
                has_items = True

    for post in mixed_queue_items:
        broadcast_queue.put(post)

    live_scan_count += 1
    current_scan_progress = 100
    last_active_portal_name = "Scan Finished"
    if ADMIN_CHAT_ID:
        update_or_create_pinned_counter(ADMIN_CHAT_ID)

    return total_found

def master_auto_scout_loop():
    time.sleep(5)
    while True:
        try:
            if is_bot_active:
                found = scrape_all_sources()

                if found == 0 and broadcast_queue.empty():
                    logger.info("Bot is Free/Idle. Triggering Detailed Department Scheme via Gemini...")
                    dispatch_auto_department_scheme()

        except Exception as e:
            logger.error(f"Master scout loop error: {e}")
        time.sleep(180)

def anti_sleep_ping_worker():
    time.sleep(20)
    while True:
        try:
            url_to_ping = RENDER_EXTERNAL_URL
            if url_to_ping:
                if not url_to_ping.startswith("http"):
                    url_to_ping = "https://" + url_to_ping
                requests.get(url_to_ping, timeout=6)
        except Exception:
            pass
        time.sleep(240)

def get_admin_reply_keyboard():
    status_label = "🔔 Auto PDF: ON" if auto_daily_pdf_active else "🔕 Auto PDF: OFF"
    return {
        "keyboard": [
            [{"text": "⚡ Force Fetch News"}, {"text": "📊 Pro Status"}],
            [{"text": "🏛️ योजनाएं (All Dept Schemes)"}, {"text": "📌 Pin Live Counter"}],
            [{"text": "🛠️ Code Update Help"}, {"text": "📄 Send Daily Digest Now"}],
            [{"text": "🌐 View Sources"}, {"text": status_label}],
            [{"text": "➕ Add Website Help"}, {"text": "📢 Change Channel"}],
            [{"text": "🔀 Mode: Both"}, {"text": "📰 Mode: News Only"}, {"text": "❓ Mode: Quiz Only"}],
            [{"text": "🔄 Reset Memory"}, {"text": "🗑️ Clear Queue"}],
            [{"text": "⏱️ Set 30 Sec"}, {"text": "⏱️ Set 60 Sec"}],
            [{"text": "🛑 Stop Engine"}, {"text": "▶️ Start Engine"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }

def send_admin_panel(text, chat_id=None):
    if not TELEGRAM_BOT_TOKEN:
        return
    target = chat_id or ADMIN_CHAT_ID
    if not target:
        return
    token = TELEGRAM_BOT_TOKEN
    url = TG_BASE + token + "/sendMessage"
    payload = {
        "chat_id": str(target).strip(),
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": get_admin_reply_keyboard()
    }
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception as e:
        logger.error(f"Error sending admin panel: {e}")

def telegram_command_listener():
    global is_bot_active, post_interval_seconds, SOURCE_CHANNEL, ADMIN_CHAT_ID, bot_mode, auto_daily_pdf_active
    last_update_id = 0
    time.sleep(2)

    token = TELEGRAM_BOT_TOKEN

    if token:
        try:
            requests.get(TG_BASE + token + "/deleteWebhook?drop_pending_updates=true", timeout=8)
        except Exception:
            pass

    while True:
        if not token:
            time.sleep(5)
            continue

        try:
            url = TG_BASE + token + "/getUpdates?offset=" + str(last_update_id + 1) + "&timeout=10"
            resp = requests.get(url, timeout=15).json()
            if resp.get("ok"):
                for upd in resp.get("result", []):
                    last_update_id = upd["update_id"]
                    msg = upd.get("message", {})
                    sender = str(msg.get("chat", {}).get("id", "")).strip()
                    text = msg.get("text", "").strip()

                    if not sender:
                        continue

                    if not ADMIN_CHAT_ID:
                        ADMIN_CHAT_ID = sender

                    if text.startswith("/modify_code") or text.startswith("/update_code"):
                        instruction = text.replace("/modify_code", "").replace("/update_code", "").strip()
                        if not instruction:
                            send_admin_panel(
                                "🛠️ <b>Autonomous Code Update Help:</b>\n\n"
                                "Aap bot ke Python code me jo bhi badlaav chahte hain, aise bhejein:\n\n"
                                "<code>/modify_code Har news caption me footer me helpline jod do</code>",
                                sender
                            )
                        else:
                            send_admin_panel("🤖 <b>Self-Code Modification Started...</b>\nGemini 1.5 Pro code likh raha hai...", sender)
                            
                            def run_auto_update(inst, snd):
                                success, res_msg = execute_self_code_modification(inst)
                                send_admin_panel(res_msg, snd)

                            threading.Thread(target=run_auto_update, args=(instruction, sender)).start()

                    elif text in ["🛠️ Code Update Help"]:
                        send_admin_panel(
                            "🛠️ <b>Autonomous Code Update Engine:</b>\n\n"
                            "Telegram se hi code modify karne ke liye command bhejein:\n"
                            "<code>/modify_code Aapka instruction</code>",
                            sender
                        )

                    elif text in ["🏛️ योजनाएं (All Dept Schemes)", "/yojna", "/schemes", "योजनाएं"]:
                        send_admin_panel("⏳ <b>सभी विभागों की योजनाओं की सूची एवं आधिकारिक पोर्टल लिंक्स तैयार हो रहे हैं...</b>", sender)
                        
                        directory_msg = "🏛️ <b>प्रमुख सरकारी विभाग एवं योजना पोर्टल डायरेक्टरी:</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        for d in DEPARTMENT_SCHEME_DIRECTORY:
                            directory_msg += f"🏢 <b>{d['dept']}</b>\n"
                            directory_msg += f"🔗 <a href='{d['portal']}'>👉 आधिकारिक योजना पोर्टल लिंक</a>\n"
                            directory_msg += f"📌 <i>प्रमुख योजनाएं:</i> {', '.join(d['schemes'][:3])} आदि।\n\n"

                        send_admin_panel(directory_msg, sender)

                        threading.Thread(target=lambda: (
                            dispatch_auto_department_scheme(),
                            send_admin_panel("✅ <b>अगले विभाग की योजना विस्तार से चैनल पर Broadcast Queue में भेज दी गई है!</b>", sender)
                        )).start()

                    elif text in ["📌 Pin Live Counter", "/counter"]:
                        update_or_create_pinned_counter(sender)
                        send_admin_panel("✅ <b>Live Pinned Counter Activated!</b>", sender)

                    elif text in ["📢 Change Channel", "/channel"]:
                        send_admin_panel(
                            f"📢 <b>Target Channel Configuration:</b>\n\n"
                            f"Abhi ka channel: <code>{SOURCE_CHANNEL}</code>\n\n"
                            f"Naya channel set karne ke liye aise bhejein:\n"
                            f"<code>/channel @AapkaChannelUsername</code>",
                            sender
                        )

                    elif text.startswith("/channel") or (text.startswith("@") and "bot" not in text.lower()):
                        parts = text.split()
                        cand = parts[1].strip() if len(parts) >= 2 else text.strip()
                        if cand.startswith("@") or cand.startswith("-100"):
                            SOURCE_CHANNEL = cand
                            save_bot_settings()
                            send_admin_panel(f"✅ <b>Target Channel Set:</b> <code>{SOURCE_CHANNEL}</code>", sender)

                    elif text in ["/sources", "🌐 View Sources"]:
                        all_s = get_all_db_sources()
                        send_admin_panel(f"🌐 <b>Total Portals Monitored: {len(all_s)} Departments</b>", sender)
                        chunk_msg = ""
                        for s in all_s:
                            line = f"• <b>[ID: {s['id']}]</b> {s['name']}\n  <code>{s['category']}</code>\n  URL: <code>{s['url'][:40]}...</code>\n\n"
                            if len(chunk_msg) + len(line) > 3000:
                                send_admin_panel(chunk_msg, sender)
                                chunk_msg = ""
                            chunk_msg += line
                        if chunk_msg:
                            send_admin_panel(chunk_msg, sender)

                    elif text in ["➕ Add Website Help"]:
                        send_admin_panel(
                            "🌐 <b>Naya Vibhag Jodne Ka Format:</b>\n\n"
                            "<code>/add [https://website.com/news](https://website.com/news) | Vibhag Ka Naam | Category Name</code>",
                            sender
                        )

                    elif text.startswith("/add") or (text.startswith("http") and "telegram.org" not in text):
                        raw_inp = text.replace("/add", "").strip()
                        parts = [p.strip() for p in raw_inp.split("|")]
                        target_url = parts[0]
                        vibhag_naam = parts[1] if len(parts) > 1 else urllib.parse.urlparse(target_url).netloc
                        category = parts[2] if len(parts) > 2 else "सामाजिक और आर्थिक संकेतक"

                        if not target_url.startswith("http"):
                            target_url = "https://" + target_url

                        if add_source_to_db(vibhag_naam, target_url, category, "rss"):
                            send_admin_panel(f"🎯 <b>Department Added:</b>\n<code>{vibhag_naam}</code>", sender)
                            threading.Thread(target=scrape_all_sources).start()

                    elif text.startswith("/del_") or text.startswith("/del"):
                        try:
                            s_id = int(text.replace("/del_", "").replace("/del", "").strip())
                            if delete_source_from_db(s_id):
                                send_admin_panel(f"🗑️ <b>Department [ID: {s_id}] Deleted!</b>", sender)
                        except Exception:
                            pass

                    elif text in ["📄 Send Daily Digest Now", "/daily_pdf"]:
                        send_admin_panel("⏳ <b>Compiling Detailed Daily Digest...</b>", sender)
                        ok = generate_and_dispatch_daily_digest(SOURCE_CHANNEL)
                        if ok:
                            generate_and_dispatch_daily_digest(sender)
                            send_admin_panel("✅ <b>Daily Current Affairs Digest Sent!</b>", sender)
                        else:
                            send_admin_panel("⚠️ Database me abhi koi news saved nahi hai.", sender)

                    elif text in ["🔔 Auto PDF: ON", "🔕 Auto PDF: OFF", "/toggle_pdf"]:
                        auto_daily_pdf_active = not auto_daily_pdf_active
                        save_bot_settings()
                        st_text = "ENABLED ✅ (Roz raat 8:00 baje aayegi)" if auto_daily_pdf_active else "DISABLED ❌"
                        send_admin_panel(f"⚙️ <b>Auto Daily PDF Status:</b> <code>{st_text}</code>", sender)

                    elif text in ["🔀 Mode: Both", "/mode_both"]:
                        bot_mode = "both"
                        save_bot_settings()
                        send_admin_panel("✅ <b>Mode Changed:</b> <code>News + Quiz (Both)</code>", sender)

                    elif text in ["📰 Mode: News Only", "/mode_news"]:
                        bot_mode = "news_only"
                        save_bot_settings()
                        send_admin_panel("✅ <b>Mode Changed:</b> <code>News Only</code>", sender)

                    elif text in ["❓ Mode: Quiz Only", "/mode_quiz"]:
                        bot_mode = "quiz_only"
                        save_bot_settings()
                        send_admin_panel("✅ <b>Mode Changed:</b> <code>Quiz Only</code>", sender)

                    elif text in ["/force", "⚡ Force Fetch News"]:
                        send_admin_panel("⚡ <b>Scanning for Detailed Current Affairs & Official PDFs...</b>", sender)
                        threading.Thread(target=lambda: send_admin_panel(f"✅ <code>{scrape_all_sources()}</code> releases queue me load ho gayi hain!", sender)).start()

                    elif text in ["/reset", "🔄 Reset Memory"]:
                        sent_hashes.clear()
                        try:
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            c.execute("DELETE FROM sent_news")
                            conn.commit()
                            conn.close()
                        except Exception:
                            pass
                        send_admin_panel("🔄 <b>Memory Reset Done! Naya Scan Shuru...</b>", sender)
                        threading.Thread(target=scrape_all_sources).start()

                    elif text in ["/status", "📊 Pro Status"]:
                        all_s = get_all_db_sources()
                        pdf_st = "ON (Daily 8:00 PM) ⏰" if auto_daily_pdf_active else "OFF 🔕"
                        send_admin_panel(
                            f"🏛️ <b>Current Affairs Pro Dashboard:</b>\n\n"
                            f"• Engine State: <code>{'ACTIVE ✅' if is_bot_active else 'STOPPED 🛑'}</code>\n"
                            f"• Self-Code Modifier: <b>ONLINE 🤖</b>\n"
                            f"• Auto 8:00 PM PDF: <b>{pdf_st}</b>\n"
                            f"• Total Portals: <b>{len(all_s)} Departments</b>\n"
                            f"• Direct PDF Uploader: <b>Active (Verified Only)</b>\n"
                            f"• Queue Pending: <code>{broadcast_queue.qsize()} Items</code>\n"
                            f"• Channel: <code>{SOURCE_CHANNEL}</code>",
                            sender
                        )

                    elif text == "⏱️ Set 30 Sec":
                        post_interval_seconds = 30
                        save_bot_settings()
                        send_admin_panel("⏱️ Gap: <b>30 Seconds</b>", sender)

                    elif text == "⏱️ Set 60 Sec":
                        post_interval_seconds = 60
                        save_bot_settings()
                        send_admin_panel("⏱️ Gap: <b>60 Seconds</b>", sender)

                    elif text in ["/stop", "🛑 Stop Engine"]:
                        is_bot_active = False
                        send_admin_panel("🛑 <b>Engine STOPPED!</b>", sender)

                    elif text in ["/start", "▶️ Start Engine"]:
                        is_bot_active = True
                        update_or_create_pinned_counter(sender)
                        send_admin_panel("🏛️ <b>Engine Active!</b> Ready to fetch.", sender)

                    elif text in ["/clear", "🗑️ Clear Queue"]:
                        while not broadcast_queue.empty():
                            broadcast_queue.get_nowait()
                        send_admin_panel("🗑️ <b>Queue Cleared!</b>", sender)
        except Exception as e:
            logger.error(f"Telegram polling loop error: {e}")
        time.sleep(2)

@app.route("/")
@app.route("/status")
def home():
    all_s = get_all_db_sources()
    return jsonify({
        "status": "Online",
        "engine": "Current Affairs Master Bot - Self Modifying Autonomous Engine",
        "mode": bot_mode,
        "scans_completed": live_scan_count,
        "active_portal": last_active_portal_name,
        "scan_progress": f"{current_scan_progress}%",
        "auto_8pm_pdf": auto_daily_pdf_active,
        "saved_departments": len(all_s),
        "target_channel": SOURCE_CHANNEL,
        "pending_queue": broadcast_queue.qsize(),
        "time": get_current_time()
    }), 200

threading.Thread(target=master_auto_scout_loop, daemon=True).start()
threading.Thread(target=channel_forwarder_worker, daemon=True).start()
threading.Thread(target=daily_8pm_scheduler_worker, daemon=True).start()
threading.Thread(target=telegram_command_listener, daemon=True).start()
threading.Thread(target=anti_sleep_ping_worker, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
