import os
import re
import fitz  # PyMuPDF

# 关键词定义
PPD_KEYWORDS = [
    r'ppd', r'p[\s-]*phenylenediamine', r'paraphenylenediamine', 
    r'1[\s,]*4[\s-]*diaminobenzene', r'1[\s,]*4[\s-]*benzenediamine',
    r'parafenilendiamina', r'对苯二胺'
]

SEDIMENT_KEYWORDS = [
    r'sediment', r'deposit', r'sludge', r'bottom material', r'沉积物', r'底泥'
]

WATER_KEYWORDS = [
    r'water', r'aqueous', r'hydro', r'aquatic', r'水体', r'水样', r'水相'
]

BIO_KEYWORDS = [
    r'bio', r'biota', r'organism', r'fish', r'algae', r'daphnia', 
    r'ecotoxicology', r'生物', r'生物体', r'生物群'
]

CONCENTRATION_PATTERNS = [
    r'concentration', r'content', r'level', r'amount', 
    r'ppm', r'ppb', r'μg/L', r'mg/kg', r'μg/kg', r'浓度', r'含量'
]

def extract_text_with_mupdf(pdf_path):
    """使用MuPDF提取PDF文本内容"""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text("text")
        return text.lower()  # 转换为小写方便匹配
    except Exception as e:
        print(f"处理文件 {pdf_path} 时出错: {e}")
        return ""

def contains_patterns(text, patterns):
    """检查文本是否包含任意正则表达式模式"""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def check_concentration(text, context_words):
    """检查特定上下文中的浓度关键词"""
    # 构建组合正则表达式
    patterns = []
    for word in context_words:
        for conc in CONCENTRATION_PATTERNS:
            # 创建更灵活的匹配模式，允许中间有少量字符
            pattern = fr"{word}[\s\w,.-]*{conc}"
            patterns.append(pattern)
    
    return contains_patterns(text, patterns)

def analyze_pdf(file_path):
    """分析单个PDF文件"""
    filename = os.path.basename(file_path)
    text = extract_text_with_mupdf(file_path)
    
    # 检测PPD
    has_ppd = contains_patterns(text, PPD_KEYWORDS)
    
    # 检测沉积物浓度
    has_sediment = check_concentration(text, SEDIMENT_KEYWORDS)
    
    # 检测水体浓度
    has_water = check_concentration(text, WATER_KEYWORDS)
    
    # 检测生物浓度
    has_bio = check_concentration(text, BIO_KEYWORDS)
    
    return {
        "filename": filename,
        "PPD": has_ppd,
        "Sediment": has_sediment,
        "Water": has_water,
        "Biological": has_bio
    }

def process_pdf_folder(folder_path):
    """处理文件夹中的所有PDF文件"""
    results = []
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    total = len(pdf_files)
    
    print(f"开始处理文件夹: {folder_path}")
    print(f"找到 {total} 个PDF文件\n")
    
    for i, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(folder_path, filename)
        print(f"处理文件 ({i}/{total}): {filename}")
        results.append(analyze_pdf(file_path))
    
    # 打印结果表格
    print("\n" + "="*70)
    print("检测结果:")
    print("-"*70)
    print(f"{'文献名称':<40} | PPD | 沉积物 | 水体 | 生物")
    print("-"*70)
    
    for res in results:
        filename = res['filename'][:35] + (res['filename'][35:] and '..')
        status = [
            " √ " if res["PPD"] else " × ",
            "  √  " if res["Sediment"] else "  ×  ",
            " √ " if res["Water"] else " × ",
            "  √  " if res["Biological"] else "  ×  "
        ]
        print(f"{filename:<40} | {status[0]} | {status[1]} | {status[2]} | {status[3]}")
    
    # 统计摘要
    print("\n" + "="*70)
    print("检测摘要:")
    print(f"包含PPD的文件: {sum(1 for r in results if r['PPD'])}/{total}")
    print(f"包含沉积物浓度的文件: {sum(1 for r in results if r['Sediment'])}/{total}")
    print(f"包含水体浓度的文件: {sum(1 for r in results if r['Water'])}/{total}")
    print(f"包含生物浓度的文件: {sum(1 for r in results if r['Biological'])}/{total}")
    print("="*70)

if __name__ == "__main__":
    # 设置PDF文件夹路径
    pdf_folder = input("请输入包含PDF文件的文件夹路径: ").strip()
    
    # 验证路径
    if not os.path.isdir(pdf_folder):
        print(f"错误: 路径 '{pdf_folder}' 不是有效的文件夹")
    else:
        process_pdf_folder(pdf_folder)