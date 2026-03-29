import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import pandas as pd
from pathlib import Path
import json

# Import table extraction libraries
try:
    import camelot
    import tabula
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class TableExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Literature Table Batch Extractor")
        self.root.geometry("1200x800")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.file_list = []
        self.extracted_tables = []
        self.current_file_index = 0
        self.is_processing = False
        
        self.create_widgets()
        self.check_dependencies()
    
    def check_dependencies(self):
        missing_libs = []
        if not CAMELOT_AVAILABLE:
            missing_libs.append("camelot/tabula")
        if not DOCX_AVAILABLE:
            missing_libs.append("python-docx")
        
        if missing_libs:
            messagebox.showwarning("Missing Dependencies", 
                f"The following libraries are not installed: {', '.join(missing_libs)}\n"
                "Please install them using pip install")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(file_frame, text="Select Files", command=self.select_files).grid(row=0, column=0, padx=5)
        ttk.Button(file_frame, text="Clear List", command=self.clear_files).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Start Extraction", command=self.start_extraction).grid(row=0, column=2, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Files to Process", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.file_listbox = tk.Listbox(list_frame, height=8)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        progress_frame = ttk.LabelFrame(main_frame, text="Processing Progress", padding="10")
        progress_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, pady=5)
        
        self.progress_text = tk.Text(progress_frame, height=6, width=40)
        self.progress_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(2, weight=1)
        
        result_frame = ttk.LabelFrame(main_frame, text="Extraction Results", padding="10")
        result_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        export_frame = ttk.Frame(result_frame)
        export_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(export_frame, text="Export to Excel", command=lambda: self.export_results('excel')).grid(row=0, column=0, padx=5)
        ttk.Button(export_frame, text="Export to CSV", command=lambda: self.export_results('csv')).grid(row=0, column=1, padx=5)
        ttk.Button(export_frame, text="Export to JSON", command=lambda: self.export_results('json')).grid(row=0, column=2, padx=5)
        
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def select_files(self):
        file_types = [
            ("Supported Files", "*.pdf *.docx *.xlsx *.xls"),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Excel Files", "*.xlsx *.xls"),
            ("All Files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select files to extract tables from",
            filetypes=file_types
        )
        
        if files:
            self.file_list.extend(files)
            for file in files:
                self.file_listbox.insert(tk.END, os.path.basename(file))
    
    def clear_files(self):
        self.file_list.clear()
        self.file_listbox.delete(0, tk.END)
        self.extracted_tables.clear()
        self.clear_results()
    
    def clear_results(self):
        for tab in self.result_notebook.tabs():
            self.result_notebook.forget(tab)
    
    def start_extraction(self):
        if not self.file_list:
            messagebox.showwarning("Warning", "Please select files first")
            return
        
        if self.is_processing:
            messagebox.showinfo("Info", "Processing in progress, please wait")
            return
        
        self.is_processing = True
        self.clear_results()
        self.extracted_tables.clear()
        
        thread = threading.Thread(target=self.extract_tables_thread)
        thread.daemon = True
        thread.start()
    
    def extract_tables_thread(self):
        try:
            total_files = len(self.file_list)
            
            for i, file_path in enumerate(self.file_list):
                self.current_file_index = i
                file_name = os.path.basename(file_path)
                
                self.root.after(0, lambda fn=file_name: self.update_status(f"Processing: {fn}"))
                self.root.after(0, lambda: self.update_progress((i / total_files) * 100))
                
                tables = self.extract_tables_from_file(file_path)
                
                if tables:
                    self.extracted_tables.extend([(file_name, table) for table in tables])
                    self.root.after(0, lambda fn=file_name, tbls=tables: self.display_tables(fn, tbls))
                
                progress_msg = f"Completed: {i+1}/{total_files} files\n"
                progress_msg += f"Current file: {file_name}\n"
                progress_msg += f"Tables extracted: {len(tables)}\n"
                progress_msg += f"Total tables: {len(self.extracted_tables)}"
                
                self.root.after(0, lambda msg=progress_msg: self.update_progress_text(msg))
            
            self.root.after(0, lambda: self.update_status("Extraction completed"))
            self.root.after(0, lambda: self.update_progress(100))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error during extraction: {str(e)}"))
        finally:
            self.is_processing = False
    
    def extract_tables_from_file(self, file_path):
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self.extract_from_pdf(file_path)
            elif file_ext in ['.docx']:
                return self.extract_from_docx(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self.extract_from_excel(file_path)
            else:
                print(f"Unsupported file type: {file_ext}")
                return []
        except Exception as e:
            print(f"Error extracting file {file_path}: {str(e)}")
            return []
    
    # ====================== 【已优化：支持三线表 / 学术表格】 ======================
    def extract_from_pdf(self, file_path):
        tables = []
        
        if not CAMELOT_AVAILABLE:
            return tables
        
        try:
            # First try: STREAM mode (best for three-line tables / academic papers)
            tables_list = camelot.read_pdf(
                file_path,
                pages='all',
                flavor='stream',
                split_text=True,
                row_tol=15,
                column_tol=15
            )
            
            for table in tables_list:
                df = table.df
                if not df.empty and len(df.columns) > 1:
                    df = self.clean_dataframe(df)
                    tables.append(df)
            
            # If no tables found, try LATTICE mode (for bordered tables)
            if len(tables) == 0:
                tables_list = camelot.read_pdf(
                    file_path,
                    pages='all',
                    flavor='lattice'
                )
                for table in tables_list:
                    df = table.df
                    if not df.empty and len(df.columns) > 1:
                        df = self.clean_dataframe(df)
                        tables.append(df)
        
        except Exception as e:
            print(f"Camelot failed, using Tabula: {str(e)}")
            try:
                dfs = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                for df in dfs:
                    if not df.empty and len(df.columns) > 1:
                        df = self.clean_dataframe(df)
                        tables.append(df)
            except Exception as e2:
                print(f"Tabula failed: {str(e2)}")
        
        return tables
    # ============================================================================
    
    def extract_from_docx(self, file_path):
        tables = []
        
        if not DOCX_AVAILABLE:
            return tables
        
        try:
            doc = Document(file_path)
            
            for table in doc.tables:
                data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        text = cell.text.strip()
                        row_data.append(text)
                    data.append(row_data)
                
                if data and len(data) > 1:
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df = self.clean_dataframe(df)
                    tables.append(df)
        
        except Exception as e:
            print(f"Word extraction failed: {str(e)}")
        
        return tables
    
    def extract_from_excel(self, file_path):
        tables = []
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if not df.empty and len(df.columns) > 1:
                    df = self.clean_dataframe(df)
                    tables.append(df)
        
        except Exception as e:
            print(f"Excel extraction failed: {str(e)}")
        
        return tables
    
    def clean_dataframe(self, df):
        df = df.dropna(how='all', axis=0)
        df = df.dropna(how='all', axis=1)
        df = df.reset_index(drop=True)
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
        
        return df
    
    def display_tables(self, file_name, tables):
        for i, table in enumerate(tables):
            tab_frame = ttk.Frame(self.result_notebook)
            tab_name = f"{file_name}_Table{i+1}"
            self.result_notebook.add(tab_frame, text=tab_name)
            self.create_table_display(tab_frame, table)
    
    def create_table_display(self, parent, dataframe):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(tree_frame)
        columns = list(dataframe.columns)
        tree["columns"] = columns
        tree["show"] = "headings"
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.W)
        
        for _, row in dataframe.iterrows():
            values = [str(val) if pd.notna(val) else "" for val in row]
            tree.insert("", tk.END, values=values)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        info_text = f"Rows: {len(dataframe)} | Columns: {len(dataframe.columns)}"
        ttk.Label(info_frame, text=info_text).pack(side=tk.LEFT)
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def update_progress_text(self, text):
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.insert(1.0, text)
        self.root.update_idletasks()
    
    def export_results(self, format_type):
        if not self.extracted_tables:
            messagebox.showwarning("Warning", "No data available for export")
            return
        
        if format_type == 'excel':
            self.export_to_excel()
        elif format_type == 'csv':
            self.export_to_csv()
        elif format_type == 'json':
            self.export_to_json()
    
    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for i, (file_name, table) in enumerate(self.extracted_tables):
                        sheet_name = f"{Path(file_name).stem}_Table{i+1}"[:31]
                        table.to_excel(writer, sheet_name=sheet_name, index=False)
                
                messagebox.showinfo("Success", f"Data exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def export_to_csv(self):
        folder_path = filedialog.askdirectory()
        
        if folder_path:
            try:
                for i, (file_name, table) in enumerate(self.extracted_tables):
                    csv_name = f"{Path(file_name).stem}_Table{i+1}.csv"
                    csv_path = os.path.join(folder_path, csv_name)
                    table.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("Success", f"Data exported to: {folder_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def export_to_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                data = {}
                for i, (file_name, table) in enumerate(self.extracted_tables):
                    key = f"{Path(file_name).stem}_Table{i+1}"
                    data[key] = table.to_dict('records')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Success", f"Data exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def main():
    root = tk.Tk()
    app = TableExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
