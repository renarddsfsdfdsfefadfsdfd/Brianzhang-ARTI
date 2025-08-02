import os
import re
import csv
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
from matplotlib.ticker import MaxNLocator

# 扩展关键词定义
PPD_KEYWORDS = [
    # 化学名称
    r'ppd', r'p[\s-]*phenylenediamine', r'paraphenylenediamine', 
    r'1[\s,]*4[\s-]*diaminobenzene', r'1[\s,]*4[\s-]*benzenediamine',
    r'parafenilendiamina', r'对苯二胺', r'对苯二胺类', r'毛发染料',
    r'toluene[\s-]*2,4[\s-]*diamine', r'2,5[\s-]*diaminotoluene',
    
    # 常见衍生物
    r'ppda', r'ppdo', r'ppd[\s-]*derivatives?',
    r'n[\s-]*methyl[\s-]*p[\s-]*phenylenediamine',
    r'n[\s-]*ethyl[\s-]*n[\s-]*hydroxyethyl[\s-]*p[\s-]*phenylenediamine',
    r'n,n[\s-]*dimethyl[\s-]*p[\s-]*phenylenediamine',
    
    # 产品相关
    r'permanent[\s-]*hair[\s-]*dye', r'oxidative[\s-]*hair[\s-]*dye',
    r'染发剂', r'氧化型染发剂', r'持久性染发剂'
]

SEDIMENT_KEYWORDS = [
    # 沉积物类型
    r'sediment', r'deposit', r'sludge', r'bottom material', 
    r'bed load', r'suspended solid', r'bed sediment', r'riverbed',
    r'沉积物', r'底泥', r'底质', r'泥沙', r'河床沉积物', r'湖底沉积物',
    r'海底沉积物', r'沉积层',
    
    # 相关过程
    r'sedimentation', r'deposition', r'settling',
    r'沉积作用', r'沉降作用', r'沉淀过程',
    
    # 相关测量
    r'sediment[\s-]*core', r'sediment[\s-]*sample', r'sediment[\s-]*profile',
    r'沉积物柱样', r'底泥样品'
]

WATER_KEYWORDS = [
    # 水体类型
    r'water', r'aqueous', r'hydro', r'aquatic', r'wastewater', 
    r'effluent', r'surface water', r'groundwater', r'river water', r'lake water',
    r'seawater', r'rainwater', r'drinking water', r'pore water',
    r'水体', r'水样', r'水相', r'水质', r'水域', r'地表水', r'地下水',
    r'河水', r'湖水', r'海水', r'孔隙水',
    
    # 水处理
    r'water[\s-]*treatment', r'wastewater[\s-]*plant',
    r'水处理', r'污水处理厂'
]

BIO_KEYWORDS = [
    # 生物类型
    r'bio', r'biota', r'organism', r'fish', r'algae', r'daphnia', 
    r'zebrafish', r'plankton', r'invertebrate', r'mussel', r'shrimp',
    r'生物', r'生物体', r'生物群', r'鱼类', r'藻类', r'浮游生物',
    r'无脊椎动物', r'贻贝', r'虾类',
    
    # 生物过程
    r'bioaccumulation', r'bioconcentration', r'biomagnification',
    r'bioavailability', r'ecotoxicology', r'toxicity',
    r'生物富集', r'生物浓缩', r'生物放大', r'生物可利用性', r'生态毒理', r'毒性',
    
    # 生物组织
    r'tissue', r'organ', r'gill', r'liver', r'muscle',
    r'组织', r'器官', r'鳃', r'肝脏', r'肌肉'
]

CONCENTRATION_PATTERNS = [
    # 浓度单位
    r'concentration', r'content', r'level', r'amount', r'value',
    r'ppm', r'ppb', r'μg/L', r'mg/L', r'μg/kg', r'mg/kg', r'ng/g',
    r'ng/L', r'pg/g', r'μg/m³', r'ng/m³',
    r'浓度', r'含量', r'水平', r'值',
    
    # 测量方法
    r'detect', r'measure', r'quantify', r'analysis',
    r'检测', r'测定', r'定量', r'分析',
    
    # 相关术语
    r'exposure', r'contamination', r'pollution', r'load',
    r'暴露', r'污染', r'负荷'
]

def extract_articles(html_content):
    """从WOS HTML内容中提取所有文献记录"""
    articles = []
    
    # 使用正则表达式分割记录
    record_pattern = r'Record \d+ of \d+'
    records = re.split(record_pattern, html_content)
    
    # 第一个元素是空或页眉，跳过
    records = records[1:]
    
    print(f"找到 {len(records)} 篇文献记录")
    
    for i, record in enumerate(records):
        article = {'index': i + 1}
        
        # 提取标题 (绿色框)
        title_match = re.search(r'Title:\s*(.+?)\s*Source:', record, re.DOTALL)
        if title_match:
            article['title'] = title_match.group(1).strip()
        else:
            # 尝试备选模式
            title_match = re.search(r'Title:\s*(.+?)\s*Author\s+Identifiers:', record, re.DOTALL)
            article['title'] = title_match.group(1).strip() if title_match else f"文献 #{i+1}"
        
        # 提取摘要 (红色框)
        abstract_match = re.search(r'Abstract:\s*(.+?)\s*(?:Conference Title:|Times Cited in|$)', record, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
        else:
            abstract = ""
        
        # 标准化摘要文本
        article['abstract'] = ' '.join(abstract.lower().split())
        
        # 提取年份
        year_match = re.search(r'Published:\s*([A-Z]{3,4}\s+(\d{4}))', record)
        if year_match:
            article['year'] = year_match.group(2)
        else:
            article['year'] = "N/A"
        
        # 提取作者
        authors_match = re.search(r'By:\s*(.+?)\s*Author\s+Identifiers:', record, re.DOTALL)
        if authors_match:
            authors = authors_match.group(1).strip()
            # 清理作者格式
            authors = re.sub(r'\([^)]*\)', '', authors)  # 移除括号内的内容
            authors = re.sub(r'\s+', ' ', authors)  # 移除多余空格
            article['authors'] = authors
        else:
            article['authors'] = ""
        
        articles.append(article)
    
    return articles

def contains_patterns(text, patterns):
    """检查文本是否包含任意正则表达式模式"""
    if not text:
        return False
        
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def check_category(text, context_words):
    """检查特定类别的关键词"""
    if not text:
        return False
        
    # 检查类别关键词
    return contains_patterns(text, context_words)

def check_concentration(text, context_words):
    """检查特定上下文中的浓度关键词"""
    if not text:
        return False
        
    # 构建组合正则表达式
    combined_patterns = []
    for word in context_words:
        for conc in CONCENTRATION_PATTERNS:
            # 创建灵活的匹配模式，允许中间有0-5个单词
            pattern = fr"\b{word}\W+(?:\w+\W+){{0,5}}?{conc}\b"
            combined_patterns.append(pattern)
    
    return contains_patterns(text, combined_patterns)

def analyze_articles(articles):
    """分析所有文献摘要"""
    results = []
    
    for article in articles:
        abstract = article['abstract']
        
        # 检测关键词 - 只要匹配类别关键词就认为存在
        has_ppd = check_category(abstract, PPD_KEYWORDS)
        has_sediment = check_category(abstract, SEDIMENT_KEYWORDS)
        has_water = check_category(abstract, WATER_KEYWORDS)
        has_bio = check_category(abstract, BIO_KEYWORDS)
        
        # 检测浓度关键词组合
        has_sediment_conc = check_concentration(abstract, SEDIMENT_KEYWORDS) if has_sediment else False
        has_water_conc = check_concentration(abstract, WATER_KEYWORDS) if has_water else False
        has_bio_conc = check_concentration(abstract, BIO_KEYWORDS) if has_bio else False
        
        result = {
            "index": article['index'],
            "title": article['title'],
            "authors": article.get('authors', ''),
            "year": article.get('year', ''),
            "PPD": has_ppd,
            "Sediment": has_sediment,
            "Water": has_water,
            "Biological": has_bio,
            "Sediment_Conc": has_sediment_conc,
            "Water_Conc": has_water_conc,
            "Biological_Conc": has_bio_conc,
            "abstract": article['abstract'][:300] + "..." if len(article['abstract']) > 300 else article['abstract']
        }
        
        results.append(result)
    
    return results

def generate_signal_plot(results, output_dir):
    """生成信号峰图"""
    if not results:
        return
        
    # 提取检测结果
    indices = [r['index'] for r in results]
    ppd = [int(r['PPD']) for r in results]
    sediment = [int(r['Sediment']) for r in results]
    water = [int(r['Water']) for r in results]
    bio = [int(r['Biological']) for r in results]
    
    # 创建子图
    fig, axes = plt.subplots(4, 1, figsize=(15, 10), sharex=True)
    plt.subplots_adjust(hspace=0.1)  # 减少子图间距
    
    # 绘制PPD信号
    axes[0].bar(indices, ppd, width=1.0, color='#1f77b4', alpha=0.7)
    axes[0].set_ylabel('PPD', fontsize=12)
    axes[0].set_ylim(0, 1.1)
    axes[0].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 绘制沉积物信号
    axes[1].bar(indices, sediment, width=1.0, color='#ff7f0e', alpha=0.7)
    axes[1].set_ylabel('Sediment', fontsize=12)
    axes[1].set_ylim(0, 1.1)
    axes[1].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[1].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 绘制水体信号
    axes[2].bar(indices, water, width=1.0, color='#2ca02c', alpha=0.7)
    axes[2].set_ylabel('Water', fontsize=12)
    axes[2].set_ylim(0, 1.1)
    axes[2].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[2].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 绘制生物信号
    axes[3].bar(indices, bio, width=1.0, color='#d62728', alpha=0.7)
    axes[3].set_ylabel('Biological', fontsize=12)
    axes[3].set_ylim(0, 1.1)
    axes[3].set_xlabel('Literature Index', fontsize=12)
    axes[3].yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[3].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 设置整体标题
    fig.suptitle('Literature Keyword Detection Signals', fontsize=16, y=0.95)
    
    # 保存图像
    plot_path = os.path.join(output_dir, "keyword_signals.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已生成信号峰图: {plot_path}")
    return plot_path

def generate_summary_plot(results, output_dir):
    """生成关键词出现次数统计图"""
    if not results:
        return
        
    # 计算每个关键词的出现次数
    ppd_count = sum(1 for r in results if r['PPD'])
    sediment_count = sum(1 for r in results if r['Sediment'])
    water_count = sum(1 for r in results if r['Water'])
    bio_count = sum(1 for r in results if r['Biological'])
    
    # 计算浓度关键词出现次数
    sediment_conc_count = sum(1 for r in results if r['Sediment_Conc'])
    water_conc_count = sum(1 for r in results if r['Water_Conc'])
    bio_conc_count = sum(1 for r in results if r['Biological_Conc'])
    
    # 创建图形
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # 第一图：关键词出现次数
    categories = ['PPD', 'Sediment', 'Water', 'Biological']
    counts = [ppd_count, sediment_count, water_count, bio_count]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    axes[0].bar(categories, counts, color=colors, alpha=0.7)
    axes[0].set_title('Keyword Occurrence Counts', fontsize=14)
    axes[0].set_ylabel('Number of Papers', fontsize=12)
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 添加数值标签
    for i, count in enumerate(counts):
        axes[0].text(i, count + 5, str(count), ha='center', va='bottom', fontsize=10)
    
    # 第二图：浓度关键词出现次数
    conc_categories = ['Sediment\nConcentration', 'Water\nConcentration', 'Biological\nConcentration']
    conc_counts = [sediment_conc_count, water_conc_count, bio_conc_count]
    conc_colors = ['#ff7f0e', '#2ca02c', '#d62728']
    
    axes[1].bar(conc_categories, conc_counts, color=conc_colors, alpha=0.7)
    axes[1].set_title('Concentration Keyword Occurrence Counts', fontsize=14)
    axes[1].set_ylabel('Number of Papers', fontsize=12)
    axes[1].grid(axis='y', linestyle='--', alpha=0.7)
    
    # 添加数值标签
    for i, count in enumerate(conc_counts):
        axes[1].text(i, count + 2, str(count), ha='center', va='bottom', fontsize=10)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图像
    summary_path = os.path.join(output_dir, "keyword_summary.png")
    plt.savefig(summary_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已生成关键词统计图: {summary_path}")
    return summary_path

def process_html_file(html_file_path, output_dir):
    """处理包含多篇文献的HTML文件"""
    print(f"开始处理文件: {html_file_path}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(html_file_path, 'r', encoding='latin-1') as f:
                html_content = f.read()
        except Exception as e:
            print(f"解码错误: {e}")
            return []
    
    # 提取所有文献记录
    articles = extract_articles(html_content)
    
    if not articles:
        print("未找到文献记录，请检查文件格式")
        return []
    
    print(f"成功提取 {len(articles)} 篇文献")
    print("开始分析摘要中的关键词...")
    
    # 分析每篇文献
    results = analyze_articles(articles)
    
    # 生成带时间戳的输出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = os.path.join(output_dir, f"literature_analysis_{timestamp}.csv")
    
    # 保存完整结果到CSV文件
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Index', 'Year', 'Title', 'Authors', 
            'PPD', 'Sediment', 'Water', 'Biological',
            'Sediment_Concentration', 'Water_Concentration', 'Biological_Concentration',
            'Abstract'
        ])
        
        for res in results:
            writer.writerow([
                res['index'],
                res['year'],
                res['title'],
                res.get('authors', ''),
                int(res['PPD']),
                int(res['Sediment']),
                int(res['Water']),
                int(res['Biological']),
                int(res['Sediment_Conc']),
                int(res['Water_Conc']),
                int(res['Biological_Conc']),
                res['abstract']
            ])
    
    print(f"\n完整结果已保存到: {output_csv}")
    
    # 生成信号峰图
    signal_path = generate_signal_plot(results, output_dir)
    
    # 生成关键词统计图
    summary_path = generate_summary_plot(results, output_dir)
    
    # 统计摘要
    print("\n" + "="*120)
    print("关键词检测统计:")
    print(f"包含PPD的文献: {sum(1 for r in results if r['PPD'])}/{len(results)}")
    print(f"包含沉积物的文献: {sum(1 for r in results if r['Sediment'])}/{len(results)}")
    print(f"包含水体的文献: {sum(1 for r in results if r['Water'])}/{len(results)}")
    print(f"包含生物的文献: {sum(1 for r in results if r['Biological'])}/{len(results)}")
    
    # 浓度统计
    print("\n浓度关键词统计:")
    print(f"包含沉积物浓度的文献: {sum(1 for r in results if r['Sediment_Conc'])}/{len(results)}")
    print(f"包含水体浓度的文献: {sum(1 for r in results if r['Water_Conc'])}/{len(results)}")
    print(f"包含生物浓度的文献: {sum(1 for r in results if r['Biological_Conc'])}/{len(results)}")
    
    # 关键词组合统计
    print("\n关键词组合统计:")
    print(f"同时包含PPD和沉积物: {sum(1 for r in results if r['PPD'] and r['Sediment'])}")
    print(f"同时包含PPD和水体: {sum(1 for r in results if r['PPD'] and r['Water'])}")
    print(f"同时包含PPD和生物: {sum(1 for r in results if r['PPD'] and r['Biological'])}")
    print(f"同时包含所有环境介质: {sum(1 for r in results if r['Sediment'] and r['Water'] and r['Biological'])}")
    print("="*120)
    
    return {
        "csv_path": output_csv,
        "signal_plot": signal_path,
        "summary_plot": summary_path,
        "results": results
    }

def generate_html_report(output_dir, results):
    """生成HTML报告"""
    # 获取结果文件路径
    csv_path = results["csv_path"]
    signal_plot = results["signal_plot"]
    summary_plot = results["summary_plot"]
    
    # 创建HTML文件路径
    report_path = os.path.join(output_dir, "analysis_report.html")
    
    # 提取统计数据
    total_papers = len(results["results"])
    ppd_count = sum(1 for r in results["results"] if r['PPD'])
    sediment_count = sum(1 for r in results["results"] if r['Sediment'])
    water_count = sum(1 for r in results["results"] if r['Water'])
    bio_count = sum(1 for r in results["results"] if r['Biological'])
    
    # 生成HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>文献关键词分析报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; padding: 20px; background-color: #f0f8ff; }}
            .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .section-title {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background-color: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
            .stat-label {{ font-size: 14px; color: #7f8c8d; }}
            .image-grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
            .image-container {{ text-align: center; }}
            .image-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
            .download-links {{ margin: 20px 0; }}
            .download-links a {{ display: inline-block; margin-right: 15px; padding: 10px 15px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>文献关键词分析报告</h1>
                <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="section">
                <h2 class="section-title">分析概览</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{total_papers}</div>
                        <div class="stat-label">总文献数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{ppd_count}</div>
                        <div class="stat-label">包含PPD的文献</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sediment_count}</div>
                        <div class="stat-label">包含沉积物的文献</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{water_count}</div>
                        <div class="stat-label">包含水体的文献</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">关键词信号分布</h2>
                <div class="image-grid">
                    <div class="image-container">
                        <img src="{os.path.basename(signal_plot)}" alt="关键词信号分布图">
                        <p>图1: 文献关键词信号分布图</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">关键词出现次数统计</h2>
                <div class="image-grid">
                    <div class="image-container">
                        <img src="{os.path.basename(summary_plot)}" alt="关键词出现次数统计图">
                        <p>图2: 关键词出现次数统计图</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">下载结果</h2>
                <div class="download-links">
                    <a href="{os.path.basename(csv_path)}">下载CSV数据</a>
                    <a href="{os.path.basename(signal_plot)}">下载信号分布图</a>
                    <a href="{os.path.basename(summary_plot)}">下载统计图</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 写入HTML文件
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"已生成HTML报告: {report_path}")
    return report_path

if __name__ == "__main__":
    # 设置HTML文件路径
    html_file = input("请输入包含多篇文献的HTML文件路径: ").strip()
    
    # 设置输出目录
    output_dir = input("请输入结果保存目录: ").strip() or "./results"
    
    # 验证路径
    if not os.path.isfile(html_file):
        print(f"错误: 文件 '{html_file}' 不存在")
    else:
        # 处理文件
        results = process_html_file(html_file, output_dir)
        
        # 生成HTML报告
        if results:
            generate_html_report(output_dir, results)
        
        print("\n分析完成！所有结果已保存到指定目录。")