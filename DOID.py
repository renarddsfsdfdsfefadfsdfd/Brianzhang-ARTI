import requests
import re
import os
import time
from bs4 import BeautifulSoup
import urllib.parse
import platform

# 获取桌面路径（跨平台兼容）
def get_desktop_path():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    else:  # Linux及其他
        return os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')

def sanitize_filename(filename):
    """移除文件名中的非法字符并缩短长度"""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return cleaned[:150]  # 防止文件名过长

def get_article_info(doi):
    """通过Crossref API获取文章元数据"""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()["message"]
        
        # 优先从Crossref获取PDF链接
        pdf_url = None
        if "link" in data:
            for link in data["link"]:
                if link.get("content-type") == "application/pdf":
                    pdf_url = link["URL"]
                    break
        
        return {
            "title": data.get("title", ["Untitled"])[0],
            "doi": doi,
            "pdf_url": pdf_url,
            "publisher_url": data.get("URL")
        }
    except Exception as e:
        print(f"获取DOI信息失败: {doi} - {str(e)}")
        return None

def find_pdf_via_unpaywall(doi):
    """通过Unpaywall API查找PDF"""
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email=user@example.com"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            best_oa = data.get("best_oa_location", {})
            if best_oa.get("url_for_pdf"):
                return best_oa["url_for_pdf"]
            elif best_oa.get("url_for_landing_page"):
                return find_pdf_on_page(best_oa["url_for_landing_page"])
    except:
        pass
    return None

def find_pdf_on_page(url):
    """在网页上查找PDF链接"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找PDF链接的常见模式
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if href.endswith('.pdf'):
                return requests.compat.urljoin(url, link['href'])
        
        # 检查meta刷新重定向
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            url_part = content.split('url=')[-1]
            if url_part:
                return find_pdf_on_page(requests.compat.urljoin(url, url_part))
    except:
        pass
    return None

def download_pdf(url, save_path):
    """下载PDF文件"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf"
        }
        
        # 处理可能的重定向
        session = requests.Session()
        response = session.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # 检查内容类型
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type:
            return False
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 过滤keep-alive块
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败: {url} - {str(e)}")
        return False

def main():
    # 配置参数
    input_file = "dois.txt"      # 输入DOI文件
    output_dir = "articles"      # 输出目录名称（将创建在桌面）
    delay_seconds = 2            # 请求延迟
    max_retries = 2              # 最大重试次数
    
    # 获取桌面路径并创建articles文件夹
    desktop_path = get_desktop_path()
    output_path = os.path.join(desktop_path, output_dir)
    os.makedirs(output_path, exist_ok=True)
    
    print(f"下载的文献将保存到: {output_path}")
    
    # 读取DOI列表
    try:
        with open(input_file, 'r') as f:
            dois = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_file}")
        print(f"请在程序同一目录下创建 {input_file} 文件，每行一个DOI")
        return
    
    print(f"找到 {len(dois)} 个DOI，开始处理...")
    success_count = 0
    
    for i, doi in enumerate(dois):
        print(f"\n处理进度: {i+1}/{len(dois)}")
        print(f"当前DOI: {doi}")
        
        article = None
        for attempt in range(max_retries + 1):
            article = get_article_info(doi)
            if article:
                break
            if attempt < max_retries:
                print(f"重试 {attempt+1}/{max_retries}...")
                time.sleep(delay_seconds * 2)
        
        if not article:
            print(f"× 无法获取文章信息: {doi}")
            continue
        
        print(f"标题: {article['title']}")
        
        # 查找PDF链接（多种途径）
        pdf_url = article["pdf_url"]
        if not pdf_url and article.get("publisher_url"):
            pdf_url = find_pdf_on_page(article["publisher_url"])
        if not pdf_url:
            pdf_url = find_pdf_via_unpaywall(doi)
        
        if not pdf_url:
            print("× 未找到PDF链接")
            continue
        
        # 下载文件
        filename = sanitize_filename(f"{article['title']}_{doi.replace('/', '_')}.pdf")
        save_path = os.path.join(output_path, filename)
        
        # 检查文件是否已存在
        if os.path.exists(save_path):
            print(f"√ 文件已存在: {save_path}")
            success_count += 1
            continue
            
        print(f"尝试下载: {pdf_url}")
        downloaded = False
        for attempt in range(max_retries + 1):
            if download_pdf(pdf_url, save_path):
                downloaded = True
                break
            if attempt < max_retries:
                print(f"下载重试 {attempt+1}/{max_retries}...")
                time.sleep(delay_seconds * 3)
        
        if downloaded:
            print(f"√ 下载成功: {save_path}")
            success_count += 1
        else:
            print("× 下载失败")
            # 清理空文件
            if os.path.exists(save_path):
                os.remove(save_path)
        
        time.sleep(delay_seconds)
    
    print(f"\n处理完成！成功下载 {success_count}/{len(dois)} 篇文献")
    print(f"所有文献已保存到: {output_path}")

if __name__ == "__main__":
    main()