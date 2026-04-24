import os
import re
import csv
import warnings
warnings.filterwarnings("ignore")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ====================== 生物关键词 正则 ======================
KEYWORD_PATTERNS = [
    r'bio',
    r'biota',
    r'organism',
    r'fish',
    r'algae',
    r'daphnia',
    r'zebrafish',
    r'plankton',
    r'invertebrate',
    r'mussel',
    r'shrimp',
    r'bioaccumulation',
    r'bioconcentration',
    r'biomagnification',
    r'bioavailability',
    r'ecotoxicology',
    r'toxicity',
    r'tissue',
    r'organ',
    r'gill',
    r'liver',
    r'muscle'
]

# ====================== 生物关键词 列表头 ======================
KEYWORD_LABELS = [
    'Bio',
    'Biota',
    'Organism',
    'Fish',
    'Algae',
    'Daphnia',
    'Zebrafish',
    'Plankton',
    'Invertebrate',
    'Mussel',
    'Shrimp',
    'Bioaccumulation',
    'Bioconcentration',
    'Biomagnification',
    'Bioavailability',
    'Ecotoxicology',
    'Toxicity',
    'Tissue',
    'Organ',
    'Gill',
    'Liver',
    'Muscle'
]

def extract_articles(html_content):
    articles = []
    record_pattern = r'Record \d+ of \d+'
    records = re.split(record_pattern, html_content)
    records = records[1:]

    for i, record in enumerate(records):
        article = {'index': i + 1}
        
        title_match = re.search(r'Title:\s*(.+?)\s*Source:', record, re.DOTALL)
        if not title_match:
            title_match = re.search(r'Title:\s*(.+?)\s*Author\s+Identifiers:', record, re.DOTALL)
        article['title'] = title_match.group(1).strip() if title_match else f"Doc #{i+1}"

        abstract_match = re.search(r'Abstract:\s*(.+?)\s*(?:Conference Title:|Times Cited in|$)', record, re.DOTALL)
        abstract = abstract_match.group(1).strip() if abstract_match else ""
        article['abstract'] = ' '.join(abstract.lower().split())
        article['full_text'] = (article['title'] + " " + article['abstract']).lower()
        
        articles.append(article)
    return articles

def count_all_keywords(text):
    counts = []
    for pat in KEYWORD_PATTERNS:
        try:
            cnt = len(re.findall(pat, text, re.IGNORECASE))
        except:
            cnt = 0
        counts.append(cnt)
    return counts

def analyze_to_target_table(articles):
    rows = []
    for art in articles:
        text = art['full_text']
        counts = count_all_keywords(text)
        total = sum(counts)
        types = sum(1 for c in counts if c > 0)
        abundance = total / types if types != 0 else 0.0
        density = types
        row = counts + [round(abundance, 4), density]
        rows.append(row)
    return rows

def save_target_table(rows, path="keyword_abundance_density_table.csv"):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        header = KEYWORD_LABELS + ['关键词丰度', '关键词密度']
        w.writerow(header)
        w.writerows(rows)

class PPDGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("生物关键词丰度密度分析")
        self.root.geometry("650x300")
        self.file_path = ""

        ttk.Label(root, text="Biology Literature HTML Analyzer", font=("Arial",14,"bold")).pack(pady=12)

        file_frame = ttk.Frame(root)
        file_frame.pack(pady=5, fill='x', padx=25)
        ttk.Label(file_frame, text="HTML File:").grid(row=0, column=0, padx=5)
        self.path_entry = ttk.Entry(file_frame, width=50)
        self.path_entry.grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse).grid(row=0, column=2, padx=5)

        self.status = ttk.Label(root, text="Status: Ready", foreground="green")
        self.status.pack(pady=5)

        ttk.Button(root, text="Generate Keyword Table", command=self.generate, width=30).pack(pady=20)

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("HTML Files","*.html;*.htm")])
        if path:
            self.file_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.status.config(text="File loaded")

    def generate(self):
        if not self.file_path:
            messagebox.showwarning("Warning","Select file first")
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html = f.read()
            articles = extract_articles(html)
            rows = analyze_to_target_table(articles)
            save_target_table(rows)
            self.status.config(text="✅ Success: keyword_abundance_density_table.csv")
            messagebox.showinfo("Done","导出成功！")
        except Exception as e:
            self.status.config(text=f"完成（已忽略异常）", foreground="blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = PPDGUI(root)
    root.mainloop()
