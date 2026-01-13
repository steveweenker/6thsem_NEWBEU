import asyncio
import os
import time
import aiohttp
import zipfile
import pytz
import urllib.parse
from io import BytesIO
from datetime import datetime
from typing import Optional, List, Tuple
from playwright.async_api import async_playwright

# --- CONFIGURATION START ---

# SECURE: Get these from Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Safety Check
if not BOT_TOKEN or not CHAT_ID:
    print("CRITICAL ERROR: BOT_TOKEN or CHAT_ID is missing from Environment Variables.")
    # We don't exit immediately to avoid crashing the container loop, 
    # but the bot won't be able to send messages.

EXAM_CONFIG = {
    "ordinal_sem": "6th",
    "roman_sem": "VI",
    "session": "2025",
    "held_month": "November",
    "held_year": "2025"
}

# The Canary (First ID) determines if the site is UP
REG_LIST = [
    "22156148040", "22156148042", "22156148018", "22156148051", "22156148012",
    "22156148001", "22156148002", "22156148003", "22156148004", "22156148005",
    "22156148006", "22156148007", "22156148008", "22156148009", "22156148011",
    "22156148013", "22156148014", "22156148015", "22156148016", "22156148017",
    "22156148019", "22156148020", "22156148021", "22156148022", "22156148023",
    "22156148024", "22156148026", "22156148027", "22156148028", "22156148029",
    "22156148030", "22156148031", "22156148032", "22156148033", "22156148034",
    "22156148035", "22156148036", "22156148037", "22156148038", "22156148039",
    "22156148041", "22156148044", "22156148045", "22156148046", "22156148047",
    "22156148048", "22156148050", "22156148052", "22156148053", "23156148901",
    "23156148902", "23156148903", "23156148904", "22101148001", "22101148002",
    "22101148003", "22101148004", "22101148005", "22101148006", "22101148007",
    "22101148008", "22101148009", "22101148010", "22101148011", "22101148012",
    "22101148013", "22101148014", "22101148015", "22101148016", "22101148019",
    "22101148021", "22101148023", "22101148024", "22101148025", "22101148026",
    "22101148027", "22101148028", "22101148029", "22101148030", "22101148031",
    "22101148033", "22101148034", "22101148035", "22101148036", "22101148038",
    "22101148039", "22101148040", "22101148041", "22101148042", "23101148901",
    "23101148902", "23101148903", "23101148904", "23101148905", "23101148906",
    "23101148908", "23101148909", "23101148910", "23101148911", "23101148913",
    "23101148914", "23101148915", "23101148916", "23101148918", "23101148919",
    "22103148001", "22103148004", "22103148006", "22103148007", "22103148008",
    "23103148901", "23103148902", "23103148903", "23103148904", "23103148905",
    "23103148906", "23103148907", "23103148908", "23103148909", "23103148910",
    "23103148911", "23103148912", "23103148913", "23103148914", "23103148916",
    "23103148917", "23103148918", "23103148920", "23103148921", "23103148922",
    "23103148923", "23103148924", "23103148925", "23103148926", "23103148928",
    "23103148930", "23103148931", "23103148932", "23103148933", "23103148934",
    "22104148001", "22104148002", "22104148003", "22104148004", "22104148005",
    "22104148006", "22104148007", "22104148008", "22104148009", "22104148010",
    "22104148012", "22104148013", "22104148014", "22104148015", "23104148901",
    "23104148902", "23104148903", "23104148904", "23104148905", "23104148906",
    "23104148907", "23104148908", "23102148901", "23102148902", "23102148903",
    "23102148904", "23102148905"
]

# --- SPEED & NOTIFICATION SETTINGS ---
CHECK_INTERVAL = 5
CONCURRENCY_LIMIT = 6
SCHEDULED_INTERVAL = 600
DOWN_REMINDER_DELAY = 3600

# --- CONFIGURATION END ---

class TelegramMonitor:
    def __init__(self):
        self.last_status: Optional[str] = None
        self.last_scheduled_time: float = 0
        self.last_down_alert_time: float = 0
        self.ist_timezone = pytz.timezone('Asia/Kolkata')

    def get_indian_time(self) -> str:
        utc_now = datetime.now(pytz.utc)
        ist_now = utc_now.astimezone(self.ist_timezone)
        return ist_now.strftime("%d-%m-%Y %I:%M:%S %p IST")

    def construct_url(self, reg_no):
        name_param = f"B.Tech. {EXAM_CONFIG['ordinal_sem']} Semester Examination, {EXAM_CONFIG['session']}"
        held_param = f"{EXAM_CONFIG['held_month']}/{EXAM_CONFIG['held_year']}"
        params = {
            'name': name_param,
            'semester': EXAM_CONFIG['roman_sem'],
            'session': EXAM_CONFIG['session'],
            'regNo': str(reg_no),
            'exam_held': held_param
        }
        return f"https://beu-bih.ac.in/result-three?{urllib.parse.urlencode(params)}"

    async def send_telegram_message(self, text: str) -> bool:
        if not BOT_TOKEN or not CHAT_ID: return False
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as resp:
                    return resp.status == 200
        except:
            return False

    async def send_telegram_file(self, filename: str, data: BytesIO, caption: str) -> bool:
        if not BOT_TOKEN or not CHAT_ID: return False
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        try:
            data.seek(0)
            form_data = aiohttp.FormData()
            form_data.add_field('chat_id', CHAT_ID)
            form_data.add_field('document', data, filename=filename)
            form_data.add_field('caption', caption)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form_data, timeout=600) as resp:
                    return resp.status == 200
        except:
            return False

    async def check_connection(self) -> str:
        canary_url = self.construct_url(REG_LIST[0])
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(canary_url, timeout=15) as resp:
                    return "UP" if resp.status == 200 else "DOWN"
        except:
            return "DOWN"

    async def verify_site_functional(self) -> bool:
        canary_reg = REG_LIST[0]
        url = self.construct_url(canary_reg)
        print(f"[*] Verifying Canary ID: {canary_reg}...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_selector(f"text={canary_reg}", timeout=15000)
                print("[*] Canary Verification Passed! DB is live.")
                await browser.close()
                return True
            except Exception as e:
                print(f"[*] Canary Failed: {e}")
                await browser.close()
                return False

    async def fetch_single_student(self, context, reg_no, semaphore) -> Tuple[str, Optional[bytes]]:
        target_url = self.construct_url(reg_no)
        async with semaphore:
            page = await context.new_page()
            try:
                await page.goto(target_url, timeout=25000)
                await page.wait_for_selector(f"text={reg_no}", timeout=10000)
                pdf_bytes = await page.pdf(format="A4", print_background=True)
                print(f"    [+] Fetched {reg_no}")
                await page.close()
                return (reg_no, pdf_bytes)
            except Exception as e:
                print(f"    [-] Failed {reg_no}: {e}")
                await page.close()
                return (reg_no, None)

    async def download_results_to_zip(self) -> BytesIO:
        buffer = BytesIO()
        print(f"[*] Starting Parallel Download (Threads: {CONCURRENCY_LIMIT})...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
            tasks = [self.fetch_single_student(context, reg, sem) for reg in REG_LIST]
            results = await asyncio.gather(*tasks)
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                success_count = 0
                for reg_no, pdf_data in results:
                    if pdf_data:
                        zf.writestr(f"Result_{reg_no}.pdf", pdf_data)
                        success_count += 1
                    else:
                        zf.writestr(f"MISSING_{reg_no}.txt", "Failed to download.")
            print(f"[*] ZIP created with {success_count}/{len(REG_LIST)} successful results.")
            await browser.close()
        buffer.seek(0)
        return buffer

    async def run(self):
        start_time = self.get_indian_time()
        await self.send_telegram_message(f"🔍 <b>Monitor Started</b>\nTime: {start_time}")

        while True:
            connection_status = await self.check_connection()
            effective_status = "DOWN"

            if connection_status == "UP":
                if self.last_status != "LIVE":
                    print("Server UP. Checking Canary...")
                    
                    is_functional = await self.verify_site_functional()
                    if is_functional:
                        effective_status = "LIVE"
                    else:
                        effective_status = "DOWN"
                else:
                    effective_status = "LIVE"

            now = time.time()
            current_time = self.get_indian_time()

            if effective_status == "LIVE":
                if self.last_status != "LIVE":
                    await self.send_telegram_message(f"🚨 <b>SITE FULLY LIVE!</b>\nStarting High-Speed Download...")
                    zip_data = await self.download_results_to_zip()
                    zip_size_mb = zip_data.getbuffer().nbytes / (1024 * 1024)
                    await self.send_telegram_message(f"📤 <b>Fetching Complete!</b>\nGenerated ZIP: {zip_size_mb:.2f} MB\n<i>Uploading to Telegram...</i>")
                    filename = f"Results_{int(time.time())}.zip"
                    success = await self.send_telegram_file(filename, zip_data, "✅ <b>Bulk Download Complete</b>")
                    if success:
                        print("Upload successful.")
                    else:
                        await self.send_telegram_message("❌ Upload failed. Please check server logs.")
                    await asyncio.sleep(600)

            elif effective_status == "DOWN":
                if self.last_status == "LIVE" or self.last_status == "UP":
                    await self.send_telegram_message(f"🔴 <b>Website went DOWN</b> - {current_time}")
                    self.last_down_alert_time = now
                elif self.last_status is None:
                    await self.send_telegram_message(f"🔴 <b>Monitor Started: Website is DOWN</b> - {current_time}")
                    self.last_down_alert_time = now
                elif DOWN_REMINDER_DELAY > 0 and (now - self.last_down_alert_time > DOWN_REMINDER_DELAY):
                    await self.send_telegram_message(f"🔴 <b>Reminder:</b> Website is still DOWN - {current_time}")
                    self.last_down_alert_time = now

            self.last_status = effective_status
            if time.time() - self.last_scheduled_time > SCHEDULED_INTERVAL:
                status_emoji = "✅" if effective_status == "LIVE" else "🔴"
                await self.send_telegram_message(f"ℹ️ Monitor Active: Status {status_emoji} - {current_time}")
                self.last_scheduled_time = time.time()
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(TelegramMonitor().run())
