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

def generate_peak_plot(results, output_dir):
    """生成峰值柱状图"""
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
    
    print(f"已生成信号图: {plot_path}")
    
    # 生成浓度组合信号图
    if any(r['Sediment_Conc'] for r in results) or any(r['Water_Conc'] for r in results) or any(r['Biological_Conc'] for r in results):
        plt.figure(figsize=(15, 6))
        
        # 创建组合信号数组
        sediment_conc = [int(r['Sediment_Conc']) for r in results]
        water_conc = [int(r['Water_Conc']) for r in results]
        bio_conc = [int(r['Biological_Conc']) for r in results]
        
        # 绘制浓度信号
        plt.bar(indices, sediment_conc, width=1.0, color='#ff7f0e', alpha=0.5, label='Sediment Concentration')
        plt.bar(indices, water_conc, width=1.0, color='#2ca02c', alpha=0.5, label='Water Concentration')
        plt.bar(indices, bio_conc, width=1.0, color='#d62728', alpha=0.5, label='Biological Concentration')
        
        plt.ylabel('Concentration Signal', fontsize=12)
        plt.xlabel('Literature Index', fontsize=12)
        plt.ylim(0, 1.1)
        plt.yticks([0, 1], ['0', '1'])
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(loc='upper right')
        plt.title('Concentration Keyword Detection Signals', fontsize=14)
        
        conc_plot_path = os.path.join(output_dir, "concentration_signals.png")
        plt.savefig(conc_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"已生成浓度信号图: {conc_plot_path}")

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
    
    # 生成信号图
    generate_peak_plot(results, output_dir)
    
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
    
    return results

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
        
        print("\n分析完成！所有结果已保存到指定目录。")