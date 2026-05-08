import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

# --- CONFIGURATION ---
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # App Password
EMAIL_RECEIVER = "khayalethu.w.myeni@gmail.com"
STATE_FILE = "seen_links.txt"

# Hardcoded Eswatini Targets (Direct URL monitoring)
TARGET_URLS = [
    "https://www.mtn.co.sz/about-mtn/careers/",
    "https://www.eswatinibank.co.sz/careers",
    "https://www.standardbank.com/sbg/main/careers",
    "https://www.fnb.co.za/about-fnb/careers/index.html", # Often covers SZ
    "https://www.ers.org.sz/careers/",
    "https://www.eec.co.sz/careers/",
    "https://www.swsc.co.sz/vacancies/",
    "https://www.centralbank.org.sz/careers/",
    "https://www.res.co.sz/careers",
    "https://www.bothouniversity.com/careers/",
    "https://www.eswatinimobile.az.sz/", # Career section varies
    "https://www.illovosugarafrica.com/Careers",
]

KEYWORDS = [
    "GIT", "graduate in training", "IT", "Security", "Compliance", 
    "Governance", "Cybersecurity", "Security+", "Network+", "CCNA", 
    "SOC", "Forensics", "Junior Analyst", "Information Security",
    "Systems Administrator", "Vulnerability", "Intern", "Trainee"
]

def load_seen_links():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_new_links(links):
    with open(STATE_FILE, "a") as f:
        for link in links:
            f.write(link + "\n")

def scan_site(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()
        
        matches = [kw for kw in KEYWORDS if kw.lower() in text]
        return matches if matches else None
    except Exception as e:
        print(f"Failed to scan {url}: {e}")
        return None

def send_email(new_matches):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🚨 {len(new_matches)} New Job Opportunities in Eswatini"

    body = "The following NEW opportunities were detected:\n\n"
    for url, kws in new_matches.items():
        body += f"📍 Organization: {url}\n🔍 Keywords: {', '.join(kws)}\n\n"

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    seen_links = load_seen_links()
    new_matches = {}
    links_to_save = []

    for url in TARGET_URLS:
        print(f"Checking: {url}")
        found_keywords = scan_site(url)
        
        # If keywords found and we haven't alerted for this URL today
        # Note: In a real-world scenario, you might want to hash the page content 
        # if the URL stays the same but content changes.
        if found_keywords and url not in seen_links:
            new_matches[url] = found_keywords
            links_to_save.append(url)
        
        time.sleep(1) # Rate limiting

    if new_matches:
        send_email(new_matches)
        save_new_links(links_to_save)
        print(f"Sent email for {len(new_matches)} new matches.")
    else:
        print("No new updates found.")

if __name__ == "__main__":
    main()
