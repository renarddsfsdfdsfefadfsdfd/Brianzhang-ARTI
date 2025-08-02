import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import platform

class DOIExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DOI提取器")
        self.root.geometry("800x600")
        
        # 设置中文字体支持
        self.setup_fonts()
        
        # 存储提取到的DOI
        self.dois = []
        
        # 创建UI
        self.create_widgets()
    
    def setup_fonts(self):
        # 为不同操作系统设置合适的字体
        system = platform.system()
        if system == "Windows":
            font_family = "SimHei"
        elif system == "Darwin":  # macOS
            font_family = "Heiti TC"
        else:  # Linux等其他系统
            font_family = "WenQuanYi Micro Hei"
        
        self.default_font = (font_family, 10)
    
    def create_widgets(self):
        # 创建输入框和按钮
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="HTML文件路径:", font=self.default_font).pack(side=tk.LEFT, padx=5)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(input_frame, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(input_frame, text="浏览", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        extract_btn = ttk.Button(input_frame, text="提取DOI", command=self.extract_dois)
        extract_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建DOI列表区域
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(list_frame, text="提取到的DOI:", font=self.default_font).pack(anchor=tk.W)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建列表框
        self.doi_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, font=self.default_font)
        self.doi_listbox.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.doi_listbox.yview)
        
        # 创建选择数量和保存区域
        save_frame = ttk.Frame(self.root, padding="10")
        save_frame.pack(fill=tk.X)
        
        ttk.Label(save_frame, text="选择保存数量:", font=self.default_font).pack(side=tk.LEFT, padx=5)
        
        self.count_var = tk.StringVar(value="5")
        count_entry = ttk.Entry(save_frame, textvariable=self.count_var, width=5)
        count_entry.pack(side=tk.LEFT, padx=5)
        
        select_first_btn = ttk.Button(save_frame, text="选择前N个", command=self.select_first_n)
        select_first_btn.pack(side=tk.LEFT, padx=5)
        
        select_all_btn = ttk.Button(save_frame, text="全选", command=self.select_all)
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(save_frame, text="清空选择", command=self.clear_selection)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(save_frame, text="保存选中的DOI", command=self.save_selected_dois)
        save_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_file(self):
        """浏览并选择本地HTML文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("HTML文件", "*.html;*.htm"), ("所有文件", "*.*")],
            title="选择HTML文件"
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def extract_dois(self):
        """从本地HTML文件中提取DOI"""
        file_path = self.file_path_var.get().strip()
        if not file_path:
            messagebox.showerror("错误", "请选择HTML文件")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return
        
        try:
            # 读取HTML文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 提取DOI - DOI格式通常为10.xxxx/xxxx
            doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
            self.dois = re.findall(doi_pattern, html_content, re.IGNORECASE)
            
            # 去重
            self.dois = list(set(self.dois))
            self.dois.sort()  # 排序
            
            # 更新列表框
            self.doi_listbox.delete(0, tk.END)
            for doi in self.dois:
                self.doi_listbox.insert(tk.END, doi)
            
            messagebox.showinfo("成功", f"成功提取到 {len(self.dois)} 个DOI")
            
        except UnicodeDecodeError:
            # 尝试其他编码读取
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    html_content = f.read()
                
                doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
                self.dois = re.findall(doi_pattern, html_content, re.IGNORECASE)
                self.dois = list(set(self.dois))
                self.dois.sort()
                
                self.doi_listbox.delete(0, tk.END)
                for doi in self.dois:
                    self.doi_listbox.insert(tk.END, doi)
                
                messagebox.showinfo("成功", f"成功提取到 {len(self.dois)} 个DOI")
                
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: 编码问题 - {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"提取DOI失败: {str(e)}")
    
    def select_first_n(self):
        try:
            n = int(self.count_var.get())
            if n <= 0:
                messagebox.showerror("错误", "请输入正整数")
                return
            
            # 清空现有选择
            self.clear_selection()
            
            # 选择前n个
            count = min(n, len(self.dois))
            for i in range(count):
                self.doi_listbox.selection_set(i)
                
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def select_all(self):
        self.doi_listbox.select_set(0, tk.END)
    
    def clear_selection(self):
        self.doi_listbox.selection_clear(0, tk.END)
    
    def save_selected_dois(self):
        selected_indices = self.doi_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请先选择要保存的DOI")
            return
        
        selected_dois = [self.dois[i] for i in selected_indices]
        
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # 确保桌面目录存在
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)
        
        # 默认文件名设置为dois.txt
        default_filename = os.path.join(desktop_path, "dois.txt")
        
        # 让用户选择保存路径和文件名
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if not file_path:
            return  # 用户取消保存
        
        try:
            # 保存DOI到文件
            with open(file_path, "w", encoding="utf-8") as f:
                for doi in selected_dois:
                    f.write(doi + "\n")
            
            messagebox.showinfo("成功", f"已成功保存 {len(selected_dois)} 个DOI到:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DOIExtractorApp(root)
    root.mainloop()
