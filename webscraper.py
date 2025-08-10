import customtkinter as ctk
from bs4 import BeautifulSoup
import requests
import random
import time
import csv
import os
import webbrowser
from tkinter import filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# ---------------------------
# SETTINGS
# ---------------------------
HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
]

# ---------------------------
# SCRAPING FUNCTION
# ---------------------------
def scrape_jobs(url, use_selenium=False):
    try:
        headers = random.choice(HEADERS_LIST)
        time.sleep(random.uniform(1, 2))  # Anti-bot delay

        if use_selenium:
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            time.sleep(4)
            page_source = driver.page_source
            driver.quit()
        else:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            page_source = response.text

        soup = BeautifulSoup(page_source, 'html.parser')

        possible_classes = ['job-bx', 'job-listing', 'job-card', 'job-result']
        jobs = None
        for class_name in possible_classes:
            jobs = soup.find_all(class_=[class_name])
            if jobs:
                break

        if not jobs:
            return {"error": "No jobs found. Try enabling JavaScript Mode."}

        scraped_jobs = []
        for job in jobs:
            company_name = job.find('h3') or job.find('div', class_='company')
            skills = job.find('span', class_='skills') or job.find('div', class_='job-skills')
            more_info = job.find('a', href=True)

            job_data = {
                "Company Name": company_name.text.strip() if company_name else "N/A",
                "Required Skills": skills.text.strip() if skills else "N/A",
                "More Info": more_info['href'] if more_info else "No Link"
            }
            scraped_jobs.append(job_data)

        return {"jobs": scraped_jobs}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected Error: {str(e)}"}

# ---------------------------
# SAVE TO CSV
# ---------------------------
def save_to_csv(jobs):
    if not jobs:
        messagebox.showerror("Error", "No jobs to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Save CSV File")
    if file_path:
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Company Name", "Required Skills", "More Info"])
            writer.writeheader()
            writer.writerows(jobs)
        messagebox.showinfo("Success", f"Data saved to {file_path}")

# ---------------------------
# GUI FUNCTIONS
# ---------------------------
def start_scraping():
    url = url_entry.get().strip()
    use_selenium = selenium_var.get()

    if not url:
        update_output("❌ Please enter a valid job website URL.")
        return

    result = scrape_jobs(url, use_selenium)
    if "error" in result:
        update_output(f"⚠️ {result['error']}")
        global last_scraped_jobs
        last_scraped_jobs = []
    else:
        display_results(result["jobs"])
        last_scraped_jobs = result["jobs"]

def update_output(text):
    output_textbox.configure(state="normal")
    output_textbox.delete("1.0", "end")
    output_textbox.insert("end", text)
    output_textbox.configure(state="disabled")

def display_results(jobs):
    output_textbox.configure(state="normal")
    output_textbox.delete("1.0", "end")
    for idx, job in enumerate(jobs, start=1):
        output_textbox.insert("end", f"#{idx} 📌 {job['Company Name']}\n")
        output_textbox.insert("end", f"   🛠 Skills: {job['Required Skills']}\n")
        output_textbox.insert("end", f"   🔗 Link: {job['More Info']}\n")
        output_textbox.insert("end", "-"*60 + "\n")
    output_textbox.configure(state="disabled")

def open_in_browser():
    if not last_scraped_jobs:
        messagebox.showerror("Error", "No job links to open.")
        return
    for job in last_scraped_jobs:
        if job["More Info"].startswith("http"):
            webbrowser.open(job["More Info"])

# ---------------------------
# GUI SETUP
# ---------------------------
last_scraped_jobs = []

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1000x700")
app.title("Advanced Job Web Scraper")
app.resizable(False, False)

frame = ctk.CTkFrame(app)
frame.pack(pady=20, padx=20, fill="both", expand=True)

ctk.CTkLabel(frame, text="🔍 Advanced Job Web Scraper", font=("Arial", 22, "bold")).pack(pady=10)

ctk.CTkLabel(frame, text="🌐 Enter Job Website URL:", font=("Arial", 14)).pack()
url_entry = ctk.CTkEntry(frame, width=500)
url_entry.pack(pady=5)

selenium_var = ctk.BooleanVar()
ctk.CTkCheckBox(frame, text="Use JavaScript Mode (Selenium)", variable=selenium_var).pack(pady=5)

button_frame = ctk.CTkFrame(frame)
button_frame.pack(pady=10)

ctk.CTkButton(button_frame, text="🚀 Start Scraping", command=start_scraping, width=150).grid(row=0, column=0, padx=5)
ctk.CTkButton(button_frame, text="💾 Save as CSV", command=lambda: save_to_csv(last_scraped_jobs), width=150).grid(row=0, column=1, padx=5)
ctk.CTkButton(button_frame, text="🌐 Open Links", command=open_in_browser, width=150).grid(row=0, column=2, padx=5)

output_textbox = ctk.CTkTextbox(frame, height=350, width=850)
output_textbox.pack(padx=10, pady=10)
output_textbox.configure(state="disabled")

app.mainloop()
