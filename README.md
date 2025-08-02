## 项目背景
本工具集由暨南大学环境学院广东省环境污染与健康重点实验室、水生态风险管理与评价课题组张耀霖开发，用于从Web of Science(WOS)数据库导出的文献数据中提取DOI、下载文献全文及分析文献摘要中的关键词信息。
Reference: Y.L ZHANG.2025. Brianzhang-ARTI [Repository]. GitHub. https://github.com/renarddsfsdfdsfsefadfsdfd/Brianzhang-ARTI

## 数据准备
1. **获取WOS文献数据**：
   - 通过WOS的`Advanced Search`功能检索目标文献
   - 检索完成后，使用`Export`功能导出文献关键信息
   - 选择导出格式为`Printable`（HTML形式），保存至电脑桌面

## 文件准备
将所有`.py`后缀文件（包括`DOIE.py`、`DOID.py`、`NERRE.py`、`OCRIII.py`等）下载并统一保存到电脑桌面。

## 环境要求
- 推荐Python版本：3.10及以下
  - `OCRIII.py`作为低阶版本，更适合未安装较多依赖库的用户
  - `NERRE.py`功能更强大，推荐在满足环境要求时使用
- 需提前安装Python环境（确保`python`命令可在CMD中正常运行）
- 可能需要的依赖库（根据提示安装）：
  ```
  pip install requests beautifulsoup4 numpy pandas matplotlib
  ```

## 使用步骤

### 第一部分：提取DOI（使用DOIE.py）
1. **打开命令行工具**：
   - 按下`Win + R`，输入`cmd`，按`Enter`打开命令提示符
   
2. **切换到桌面目录**：
   - 在CMD中输入以下命令并按`Enter`（自动适配当前用户）：
     ```
     cd %USERPROFILE%\Desktop
     ```

3. **运行DOI提取工具**：
   - 输入命令并按`Enter`：
     ```
     python DOIE.py
     ```
   - 工具将自动处理桌面的WOS Printable HTML文件
   - 提取的DOI将保存为`dois.txt`文件到桌面

### 第二部分：下载文献（使用DOID.py）
1. **继续在CMD中操作**（确保仍处于桌面目录）：
   - 输入命令并按`Enter`：
     ```
     python DOID.py
     ```

2. **自动下载过程**：
   - 工具将自动读取桌面的`dois.txt`文件
   - 根据DOI信息反推文献名称及下载链接
   - 下载的文献将保存到桌面

### 第三部分：摘要关键词分析
根据你的Python版本和库安装情况选择合适的工具：

#### 高级版本（NERRE.py）
1. **运行关键词分析工具**：
   - 在CMD中输入命令并按`Enter`：
     ```
     python NERRE.py
     ```

2. **分析操作**：
   - 选择之前下载的带有`Abstract`（摘要）的WOS Printable HTML文件
   - 工具将自动读取HTML中各文献的摘要和关键词
   - 输出结果包括：
     - 检出信号图
     - 统计数据
     - 联合统计数据

#### 低阶版本（OCRIII.py）
1. **运行低阶版本工具**：
   - 在CMD中输入命令并按`Enter`：
     ```
     python OCRIII.py
     ```

2. **分析操作**：
   - 操作步骤与NERRE.py类似
   - 适合Python版本低于3.10或未安装完整依赖库的用户

## 注意事项
- 确保网络连接正常，特别是在使用DOID.py下载文献时
- 请遵守学术规范和版权要求，下载的文献仅用于研究目的
- 如遇运行错误，建议检查：
  - Python版本是否符合要求
  - 必要的依赖库是否已安装
  - 输入文件是否存在且格式正确
  - 命令行是否已正确切换到桌面目录

## 联系信息
项目负责人：张耀霖（暨南大学环境学院）
所属机构：广东省环境污染与健康重点实验室
![image](https://github.com/renarddsfsdfdsfefadfsdfd/Brianzhang-ARTI/blob/main/%E6%B5%81%E7%A8%8B%E5%9B%BE%E7%A4%BA%E6%84%8F.jpg)
# 项目流程与原理说明  

本项目围绕特定文档（以含 p-phenylenediamine 等信息的数据处理为背景）的识别、分类与校验展开，核心流程及数学逻辑如下：  


## 1. 数据筛选与基础统计（以 WOS 数据为例）  
### 筛选逻辑  
针对标识为 `WOS (TS=p-phenylenediamine)` 的数据集（总样本量 \( n = 6360 \) ），通过 `DOIE` 工具，依据 `RegExp` 规则筛选出**可打印（`printable`）**且符合 `Html` 格式的数据。  


### 提取率计算  
有效提取率通过以下公式计算：  
$$
\pi_f^p = \frac{N_T - N_t^+}{N_T} \times 100\%
$$  
其中：  
- \( N_T \)：初始总样本量（本项目中 \( N_T = 6360 \) ）  
- \( N_t^+ \)：未通过提取规则的样本量  

经计算，最终筛选出可提取数据 \( n = 5338 \)，提取率为：  
$$
\pi_f^p \approx \frac{6360 - (6360 - 5338)}{6360} \times 100\% \approx 16.1\%
$$  

筛选后的数据进入**归档（`Archive`）**环节。  


## 2. 内部标签校验（Information internal label check）  
### 校验逻辑Ⅰ  
对归档数据，首先通过以下步骤计算与校验：  

#### 1. 均值排序公式  
按文档列统计均值并排序，公式表示为：  
$$
\pi_i^a = \text{sort}\left\{ \bar{d}_i \right\}, \quad \text{其中} \quad \bar{d}_i = \frac{m(\text{col}, \text{doc})}{N}
$$  
- \( \bar{d}_i \)：某列（`col`）在文档（`doc`）中的均值，\( m(\text{col}, \text{doc}) \) 为列数据总和，\( N \) 为样本量  
- \( \text{sort}\{ \bar{d}_i \} \)：对所有列的均值结果排序  


#### 2. 多轮校验与残余误差  
结合**可视化工具（`visuaklzMy`）**与**人工校验（分 \( \pi_s^a、\pi_s^b、\pi_s^c \) 多轮）**，总校验指标为：  
$$
\sum \pi_i^a = \pi_s^a + \pi_s^b + \pi_s^c
$$  

通过以下公式计算**残余误差**，验证数据一致性：  
$$
\pi_r^a = \frac{\pi_f^p - \sum \pi_i^a}{\pi_f^p}
$$  

本项目中计算得 \( \pi_r^a \approx 0.004 \)（即 \( 0.4\% \) ），满足 \( 0.004 < 0.005 \)（基础误差阈值 5‰ 内）。  


## 3. 文档处理与结果校验（以 PDF 处理为例）  
### 流程说明  
通过 `NERRE.py` 输出多维度结论（如 `PPD - o(\ln)、wost - a(\ln_2)` 等 ），再经：  
- `OCR11.py`（非摘要渲染器，处理文本识别 ）  
- `Find.py`（提取工具，定位关键内容 ）  

对全量 PDF 执行处理。  


### 结果校验公式  
利用以下公式对比**机器识别结果（`Mresult`）**与**标准结果（`Mposuit`）**的差异：  
$$
\pi_i^b = \frac{|\text{Mresult} - \text{Mposuit}|}{\min(n)}
$$  

最终校验后的数据（含 `PPD*、Scat*` 等类型 ），支持通过 `Nona Power` 下载，用于**精度（`Correc (Accuracy)`）验证**。  


## 核心逻辑总结  
项目通过 **“数据筛选 → 多轮校验 → 公式化误差控制”** 流程，实现文档从原始数据到可用结果的流转。核心公式（如提取率 \( \pi_f^p \)、残余误差 \( \pi_r^a \)、结果校验 \( \pi_i^b \) ）保障了：  
- 提取环节的量化统计  
- 校验环节的误差管控  
- 结果环节的精度验证  

为数据质量与处理逻辑提供**数学可追溯性**与**量化支撑**。  
