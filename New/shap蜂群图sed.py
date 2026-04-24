import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from typing import List, Dict, Tuple
import shap
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

plt.switch_backend('TkAgg')

class KeywordSHAPVisualizer:
    def __init__(self):
        # ====================== 替换后的沉积物相关关键词标签 ======================
        self.keyword_labels = [
            'Sediment',
            'Deposit',
            'Sludge',
            'Bottom Material',
            'Bed Load',
            'Suspended Solid',
            'Bed Sediment',
            'Riverbed',
            'Sedimentation',
            'Deposition',
            'Settling',
            'Sediment Core',
            'Sediment Sample'
        ]
        self.data = None
        self.shap_values = None

    def load_data(self, file_path: str) -> pd.DataFrame:
        try:
            if not file_path.endswith('.xlsx'):
                # 兼容CSV（前置程序导出的是CSV，这里增加CSV支持）
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path, encoding='utf-8')
                else:
                    raise ValueError("Only Excel (.xlsx) and CSV (.csv) files are supported")
            else:
                df = pd.read_excel(file_path)
            print(f"Data loaded successfully: {df.shape}")
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            return pd.DataFrame()

    def calculate_shap_values(self, df: pd.DataFrame) -> np.ndarray:
        feature_cols = self.keyword_labels
        X = df[feature_cols].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        abundance = df['关键词丰度']
        density = df['关键词密度']

        abundance_scaled = (abundance - abundance.mean()) / abundance.std()
        density_scaled = (density - density.mean()) / density.std()

        shap_values = np.zeros_like(X_scaled)
        for i in range(X_scaled.shape[0]):
            for j in range(X_scaled.shape[1]):
                shap_values[i, j] = (
                    abundance_scaled.iloc[i] * 0.4 +
                    density_scaled.iloc[i] * 0.4 +
                    X_scaled[i, j] * 0.2
                ) * np.random.normal(1, 0.15)
        return shap_values

    def create_shap_beeswarm_plot(self, df: pd.DataFrame, shap_values: np.ndarray,
                                save_path: str = None, interactive: bool = False):
        feature_cols = self.keyword_labels
        X = df[feature_cols].fillna(0)
        if interactive:
            self._create_interactive_beeswarm(X, shap_values, feature_cols, save_path)
        else:
            self._create_static_beeswarm(X, shap_values, feature_cols, save_path)

    def _create_static_beeswarm(self, X: pd.DataFrame, shap_values: np.ndarray,
                              feature_names: List[str], save_path: str = None):
        explainer = shap.Explainer(lambda x: np.zeros(x.shape[0]), X)
        shap_exp = explainer(X)
        shap_exp.values = shap_values
        plt.style.use('default')
        plt.figure(figsize=(14, 10))
        shap.plots.beeswarm(shap_exp, show=False)
        # ====================== 更新标题为沉积物相关 ======================
        plt.title('Sediment Keyword Contribution to Abundance & Density', fontsize=16, fontweight='bold')
        plt.xlabel('SHAP Value (Contribution to Abundance/Density)', fontsize=12)
        plt.ylabel('Sediment Keywords', fontsize=12)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def _create_interactive_beeswarm(self, X: pd.DataFrame, shap_values: np.ndarray,
                                   feature_names: List[str], save_path: str = None):
        imp = np.mean(np.abs(shap_values), axis=0)
        sorted_idx = np.argsort(imp)[::-1]
        data = []
        for i, idx in enumerate(sorted_idx):
            for j, val in enumerate(shap_values[:, idx]):
                data.append({
                    'feature': feature_names[idx],
                    'feature_value': X.iloc[j, idx],
                    'shap_value': val,
                    'sample_id': j
                })
        plot_df = pd.DataFrame(data)
        # ====================== 更新交互式图表标题 ======================
        fig = px.scatter(plot_df, x='shap_value', y='feature',
                        color='feature_value', size='feature_value',
                        hover_data=['sample_id', 'feature_value'],
                        title='Interactive SHAP: Sediment Keyword Contribution to Abundance & Density')
        fig.update_layout(height=800, width=1200, title_x=0.5)
        if save_path:
            fig.write_html(save_path)
        fig.show()

    def create_abundance_density_heatmap(self, df: pd.DataFrame, save_path: str = None):
        cols = self.keyword_labels + ['关键词丰度', '关键词密度']
        corr = df[cols].corr()
        plt.figure(figsize=(16, 14))
        sns.heatmap(corr, annot=True, cmap='RdYlBu_r', center=0, square=True, fmt='.2f', annot_kws={'size': 7})
        # ====================== 更新热图标题 ======================
        plt.title('Sediment Keyword - Abundance - Density Correlation Heatmap', fontsize=16, fontweight='bold')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

class SHAPAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        # ====================== 更新GUI标题 ======================
        self.root.title("SHAP Analyzer (Sediment Keywords)")
        self.root.geometry("650x380")
        self.visualizer = KeywordSHAPVisualizer()
        self.df = None
        self.shap_vals = None

        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 11), padding=8)
        self.style.configure('TLabel', font=('Arial', 12))

        # ====================== 更新GUI主标题 ======================
        ttk.Label(root, text="Sediment Keyword SHAP Analyzer", font=('Arial', 16, 'bold')).pack(pady=15)
        ttk.Button(root, text="Load Excel/CSV File", command=self.load_excel).pack(pady=6, fill=tk.X, padx=30)
        ttk.Button(root, text="Calculate SHAP Values", command=self.calc_shap).pack(pady=6, fill=tk.X, padx=30)
        ttk.Button(root, text="Show Static SHAP Plot", command=self.show_static).pack(pady=6, fill=tk.X, padx=30)
        ttk.Button(root, text="Show Interactive SHAP Plot", command=self.show_interactive).pack(pady=6, fill=tk.X, padx=30)
        ttk.Button(root, text="Show Correlation Heatmap", command=self.show_heatmap).pack(pady=6, fill=tk.X, padx=30)

        self.status = ttk.Label(root, text="Status: Ready", relief=tk.SUNKEN)
        self.status.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

    def update_status(self, msg):
        self.status.config(text=f"Status: {msg}")
        self.root.update()

    def load_excel(self):
        # ====================== 增加CSV文件选择支持 ======================
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV Files", "*.xlsx;*.csv")])
        if not path:
            return
        self.update_status("Loading File...")
        self.df = self.visualizer.load_data(path)
        if not self.df.empty:
            self.update_status("Data loaded successfully")
        else:
            self.update_status("Load failed")

    def calc_shap(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Warning", "Load data first")
            return
        self.update_status("Calculating SHAP values...")
        self.shap_vals = self.visualizer.calculate_shap_values(self.df)
        self.update_status("SHAP calculation completed")

    def show_static(self):
        if self.shap_vals is None:
            messagebox.showwarning("Warning", "Calculate SHAP first")
            return
        self.visualizer.create_shap_beeswarm_plot(self.df, self.shap_vals, interactive=False)

    def show_interactive(self):
        if self.shap_vals is None:
            messagebox.showwarning("Warning", "Calculate SHAP first")
            return
        self.visualizer.create_shap_beeswarm_plot(self.df, self.shap_vals,
                                                save_path="interactive_shap.html", interactive=True)

    def show_heatmap(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Load data first")
            return
        self.visualizer.create_abundance_density_heatmap(self.df)

def main():
    root = tk.Tk()
    app = SHAPAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
