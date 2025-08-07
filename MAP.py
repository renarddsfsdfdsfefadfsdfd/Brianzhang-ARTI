import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

class ProvinceHeatmapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("省份数据热图可视化工具")
        self.root.geometry("1000x700")
        
        # 数据存储
        self.gdf = None  # 地理数据
        self.province_names = []  # 省份名称列表
        self.province_column = None  # 省份名称字段名
        self.shapefile_path = "province"  # 默认shapefile路径
        
        # 创建颜色映射
        self.colormap = self._create_custom_colormap()
        
        # 创建界面
        self._create_widgets()
        
        # 尝试加载地理数据
        self.load_geodata()
    
    def _create_custom_colormap(self):
        """创建自定义颜色映射"""
        colors = ['#f7fbff', '#ebf3fb', '#deebf7', '#c6dbef', '#9ecae1', 
                 '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']
        return LinearSegmentedColormap.from_list('custom_blue', colors, N=100)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮区域
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 加载数据按钮
        ttk.Button(button_frame, text="加载地理数据", command=self.select_shapefile).pack(side=tk.LEFT, padx=5)
        
        # 生成热图按钮
        ttk.Button(button_frame, text="生成热图", command=self.generate_heatmap).pack(side=tk.LEFT, padx=5)
        
        # 保存热图按钮
        ttk.Button(button_frame, text="保存热图", command=self.save_heatmap).pack(side=tk.LEFT, padx=5)
        
        # 表格和地图的分割面板
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 左侧表格区域
        table_frame = ttk.LabelFrame(paned_window, text="省份数据", padding="5")
        paned_window.add(table_frame, weight=1)
        
        # 创建表格 - 明确指定列索引
        self.columns = ("province", "value")  # 列名
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        
        # 设置列标题
        self.tree.heading("province", text="省份")
        self.tree.heading("value", text="数值")
        
        # 设置列宽
        self.tree.column("province", width=150)
        self.tree.column("value", width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 布局表格和滚动条
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 双击单元格可编辑
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # 右侧地图区域
        self.map_frame = ttk.LabelFrame(paned_window, text="热图预览", padding="5")
        paned_window.add(self.map_frame, weight=2)
        
        # 地图相关变量
        self.fig = None
        self.canvas = None
    
    def on_double_click(self, event):
        """处理单元格双击事件，允许编辑数值"""
        # 只允许编辑数值列
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            # 获取列名而非索引，更可靠
            column_id = self.tree.identify_column(event.x)
            column_name = self.tree.column(column_id, "id")
            
            # 检查是否是数值列
            if column_name == "value":
                item = self.tree.identify_row(event.y)
                if item:
                    # 获取当前值
                    current_value = self.tree.item(item, "values")[1]
                    
                    # 获取单元格位置用于定位编辑窗口
                    try:
                        x, y, width, height = self.tree.bbox(item, column_id)
                    except:
                        # 如果获取位置失败，使用默认位置
                        x, y = 100, 100
                        width, height = 100, 20
                    
                    # 创建编辑窗口
                    edit_window = tk.Toplevel(self.root)
                    edit_window.geometry(f"150x100+{self.root.winfo_rootx()+x}+{self.root.winfo_rooty()+y+height}")
                    edit_window.transient(self.root)
                    edit_window.resizable(False, False)
                    edit_window.title("编辑数值")
                    
                    # 创建输入框
                    ttk.Label(edit_window, text="请输入数值:").pack(pady=5, padx=5, anchor=tk.W)
                    value_entry = ttk.Entry(edit_window)
                    value_entry.pack(pady=5, padx=5, fill=tk.X)
                    value_entry.insert(0, current_value if current_value else "")
                    value_entry.focus()
                    
                    # 确认按钮
                    def save_edit():
                        try:
                            # 验证输入是否为数字
                            value = value_entry.get()
                            if value:
                                # 尝试转换为浮点数，验证是否为有效数字
                                float(value)
                                self.tree.set(item, column=column_name, value=value)
                            else:
                                self.tree.set(item, column=column_name, value="")
                            edit_window.destroy()
                        except ValueError:
                            messagebox.showerror("输入错误", "请输入有效的数字")
                    
                    btn_frame = ttk.Frame(edit_window)
                    btn_frame.pack(pady=5, fill=tk.X, padx=5)
                    ttk.Button(btn_frame, text="确认", command=save_edit).pack(side=tk.LEFT, padx=5)
                    ttk.Button(btn_frame, text="取消", command=edit_window.destroy).pack(side=tk.RIGHT, padx=5)
                    
                    # 按Enter键保存
                    value_entry.bind("<Return>", lambda e: save_edit())
                    # 按ESC键取消
                    value_entry.bind("<Escape>", lambda e: edit_window.destroy())
    
    def select_shapefile(self):
        """选择shapefile文件"""
        filename = filedialog.askopenfilename(
            title="选择shapefile文件",
            filetypes=[("Shapefile", "*.shp"), ("所有文件", "*.*")]
        )
        
        if filename:
            self.shapefile_path = os.path.splitext(filename)[0]
            self.load_geodata()
    
    def load_geodata(self):
        """加载地理数据并填充表格"""
        try:
            # 读取shapefile
            self.gdf = gpd.read_file(f"{self.shapefile_path}.shp")
            print(f"成功加载地理数据，包含 {len(self.gdf)} 个区域")
            print("地理数据中的字段：", self.gdf.columns.tolist())
            
            # 清空表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 自动检测省份名称字段
            name_candidates = ['pr_name', 'cn_name', 'NAME', 'name', 'province']
            self.province_column = None
            
            for candidate in name_candidates:
                if candidate in self.gdf.columns:
                    self.province_column = candidate
                    print(f"自动检测到省份名称字段: {self.province_column}")
                    break
            
            if self.province_column is None:
                messagebox.showerror("错误", "未找到省份名称字段，请检查数据文件")
                return
            
            # 获取省份名称列表
            self.province_names = self.gdf[self.province_column].tolist()
            
            # 填充表格
            for province in self.province_names:
                self.tree.insert("", tk.END, values=(province, ""))
            
            messagebox.showinfo("成功", f"已加载 {len(self.province_names)} 个省份数据")
            
        except Exception as e:
            print(f"加载地理数据失败：{e}")
            messagebox.showerror("错误", f"加载地理数据失败：{str(e)}")
    
    def get_table_data(self):
        """从表格获取数据"""
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) >= 2 and values[1]:  # 确保有数值
                try:
                    data.append({
                        "province": values[0],
                        "value": float(values[1])
                    })
                except ValueError:
                    messagebox.showerror("数据错误", f"省份 '{values[0]}' 的数值格式不正确")
                    return None
        return pd.DataFrame(data)
    
    def generate_heatmap(self):
        """生成热图"""
        if self.gdf is None or self.province_column is None:
            messagebox.showwarning("警告", "请先加载地理数据")
            return
        
        # 获取表格数据
        data = self.get_table_data()
        if data is None or len(data) == 0:
            messagebox.showwarning("警告", "请至少输入一个省份的数值")
            return
        
        # 合并数据
        merged_data = self.gdf.merge(
            data, 
            left_on=self.province_column, 
            right_on="province",
            how="left"
        )
        
        # 清除之前的图表
        for widget in self.map_frame.winfo_children():
            widget.destroy()
        
        # 创建新图表
        self.fig, ax = plt.subplots(figsize=(8, 6))
        
        # 绘制地图
        merged_data.plot(
            column="value", 
            cmap=self.colormap, 
            linewidth=0.8, 
            ax=ax, 
            edgecolor='0.8',
            missing_kwds={
                "color": "lightgrey",
                "edgecolor": "grey",
                "hatch": "///",
                "label": "无数据"
            }
        )
        
        # 添加颜色条（映射带）
        cbar = plt.colorbar(ax.collections[0], ax=ax)
        cbar.set_label("数值", fontsize=12)
        
        # 设置标题和去除坐标轴
        ax.set_title("中国各省数据热图", fontsize=16, pad=20)
        ax.axis('off')
        
        # 调整布局
        plt.tight_layout()
        
        # 在Tkinter窗口中显示图表
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def save_heatmap(self):
        """保存热图"""
        if self.fig is None:
            messagebox.showwarning("警告", "请先生成热图")
            return
        
        # 询问保存路径
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("JPEG图片", "*.jpg"), ("SVG图片", "*.svg"), ("PDF文档", "*.pdf")]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("成功", f"热图已保存至：{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProvinceHeatmapGUI(root)
    root.mainloop()
    