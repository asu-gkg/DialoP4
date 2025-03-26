import os
import uuid
import fitz  # PyMuPDF
from pathlib import Path
import re

class PDFProcessor:
    """PDF处理工具类，用于解析和处理学术论文PDF"""
    
    def __init__(self, config):
        """
        初始化PDF处理器
        
        Args:
            config (dict): 配置字典
        """
        self.document_store_path = config['storage']['document_store_path']
        self.vector_db_path = config['storage']['vector_db_path']
    
    def save_pdf(self, file, conversation_id=''):
        """
        保存上传的PDF文件
        
        Args:
            file: 上传的文件对象
            conversation_id (str): 会话ID
            
        Returns:
            str: 保存的文件路径
        """
        # 生成唯一文件名
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # 创建会话目录
        conversation_dir = Path(self.document_store_path) / conversation_id
        conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        safe_filename = self._sanitize_filename(file.filename)
        file_path = conversation_dir / safe_filename
        file.save(str(file_path))
        
        return str(file_path)
    
    def parse_pdf(self, pdf_path):
        """
        解析PDF文件内容
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            dict: 包含论文结构化内容的字典
        """
        doc = fitz.open(pdf_path)
        
        # 提取基本信息
        title = self._extract_title(doc)
        authors = self._extract_authors(doc)
        abstract = self._extract_abstract(doc)
        
        # 提取正文内容
        sections = self._extract_sections(doc)
        
        # 提取图表
        figures = self._extract_figures(doc)
        
        # 提取参考文献
        references = self._extract_references(doc)
        
        # 关闭文档
        doc.close()
        
        return {
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'sections': sections,
            'figures': figures,
            'references': references,
            'pdf_path': pdf_path
        }
    
    def _sanitize_filename(self, filename):
        """安全化文件名，去除不安全字符"""
        # 移除危险字符
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # 确保文件名不为空
        if not filename:
            filename = f"document_{uuid.uuid4()}.pdf"
        # 确保有.pdf后缀
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        return filename
    
    def _extract_title(self, doc):
        """从PDF中提取论文标题"""
        # 简单实现：假设第一页前几行中字体最大的是标题
        title = ""
        max_font_size = 0
        
        # 检查第一页
        page = doc[0]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks[:5]:  # 只检查前5个文本块
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # 找到字体最大的文本
                        if span["size"] > max_font_size and len(span["text"].strip()) > 10:
                            max_font_size = span["size"]
                            title = span["text"].strip()
        
        # 如果未能提取到标题，使用文件名
        if not title:
            title = os.path.basename(doc.name).replace(".pdf", "")
        
        return title
    
    def _extract_authors(self, doc):
        """从PDF中提取作者信息"""
        authors = []
        
        # 检查第一页
        page = doc[0]
        text = page.get_text("text")
        
        # 简单实现：尝试通过模式匹配找到作者行
        # 在大多数学术论文中，作者位于标题下方
        lines = text.split('\n')
        
        # 尝试寻找可能的作者行（通常包含多个名字，没有长句子）
        for i, line in enumerate(lines[:15]):  # 只检查前15行
            line = line.strip()
            if line and len(line) > 5 and "," in line and len(line.split()) < 15:
                if any(x.lower() in line.lower() for x in ["university", "institute", "lab"]):
                    continue  # 跳过机构行
                
                # 假设这是作者行
                authors = [author.strip() for author in line.split(",")]
                break
        
        return authors
    
    def _extract_abstract(self, doc):
        """从PDF中提取摘要"""
        abstract = ""
        
        # 检查前两页
        for page_num in range(min(2, len(doc))):
            page = doc[page_num]
            text = page.get_text("text")
            
            # 尝试找到"Abstract"标题
            abstract_match = re.search(r'(?i)abstract\s*\n\s*(.*?)(?:\n\s*\n|\n\s*introduction)', text, re.DOTALL)
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                break
        
        return abstract
    
    def _extract_sections(self, doc):
        """从PDF中提取章节内容"""
        sections = []
        current_section = None
        
        # 遍历所有页面
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text("text") + "\n"
        
        # 使用正则表达式找出可能的章节标题
        # 通常章节标题是单独的一行，可能有数字前缀，后面紧跟内容
        section_pattern = r'(?:\n|\r\n)(\d+(?:\.\d+)*\s+[A-Z][^.\n]{3,50}|[A-Z][^.\n]{3,50})\s*(?:\n|\r\n)'
        
        # 找出所有可能的章节
        matches = re.finditer(section_pattern, full_text)
        section_positions = []
        
        for match in matches:
            section_title = match.group(1).strip()
            start_pos = match.start()
            section_positions.append((start_pos, section_title))
        
        # 按位置排序章节
        section_positions.sort()
        
        # 提取章节内容
        for i, (start_pos, title) in enumerate(section_positions):
            # 确定章节结束位置
            if i < len(section_positions) - 1:
                end_pos = section_positions[i+1][0]
            else:
                end_pos = len(full_text)
            
            # 提取章节内容
            content = full_text[start_pos:end_pos].strip()
            
            # 去掉标题本身
            content = content.replace(title, "", 1).strip()
            
            sections.append({
                "title": title,
                "content": content
            })
        
        return sections
    
    def _extract_figures(self, doc):
        """从PDF中提取图表信息"""
        figures = []
        
        # 遍历所有页面
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 提取图像
            images = page.get_images(full=True)
            
            for img_index, img in enumerate(images):
                # 尝试找到图表标题
                text = page.get_text("text")
                fig_captions = re.findall(r'(?i)(?:figure|fig)\.?\s*\d+[.:]\s*([^\n.]+)', text)
                
                caption = f"图表 {img_index + 1}" 
                if img_index < len(fig_captions):
                    caption = fig_captions[img_index]
                
                figures.append({
                    "page": page_num + 1,
                    "caption": caption.strip() if caption else f"图表 {len(figures) + 1}"
                })
        
        return figures
    
    def _extract_references(self, doc):
        """从PDF中提取参考文献"""
        references = []
        
        # 获取全文
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text("text") + "\n"
        
        # 尝试找到参考文献部分
        ref_section_match = re.search(r'(?i)(?:references|bibliography)\s*\n(.*?)(?:\n\s*(?:appendix|appendices)|$)', full_text, re.DOTALL)
        
        if ref_section_match:
            ref_text = ref_section_match.group(1).strip()
            
            # 分割单独的引用
            # 通常引用以编号或作者开头
            ref_entries = re.split(r'\n\s*(?:\[\d+\]|\d+\.|\[\w+\d+\])', ref_text)
            
            for entry in ref_entries:
                entry = entry.strip()
                if entry:
                    references.append(entry)
        
        return references 