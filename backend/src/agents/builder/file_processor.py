import os
import logging
import mimetypes
from typing import Dict, Optional, Tuple
from abc import ABC, abstractmethod

import PyPDF2
import docx
import csv

# 条件导入 markdown
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from utils.config import settings

logger = logging.getLogger(__name__)


class FileProcessor(ABC):
    """文件处理器基类"""
    
    @abstractmethod
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """
        处理文件并提取内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            (提取的文本内容, 文件元数据)
        """
        pass
    
    @staticmethod
    def get_processor(file_path: str) -> Optional['FileProcessor']:
        """
        根据文件扩展名获取对应的处理器
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应的文件处理器实例，如果不支持则返回None
        """
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.txt':
            return TextFileProcessor()
        elif extension == '.pdf':
            return PDFProcessor()
        elif extension in ['.doc', '.docx']:
            return WordProcessor()
        elif extension == '.md':
            return MarkdownProcessor()
        elif extension == '.csv':
            return CSVProcessor()
        elif extension in ['.json', '.xml']:
            return DataFileProcessor()
        else:
            logger.warning(f"不支持的文件类型: {extension}")
            return None
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否有效, 错误消息)
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"文件大小超过限制: {file_size} > {settings.MAX_FILE_SIZE} bytes"
        
        # 检查文件扩展名
        extension = os.path.splitext(file_path)[1].lower()
        if extension not in settings.allowed_extensions_list:
            return False, f"不支持的文件类型: {extension}"
        
        return True, None


class TextFileProcessor(FileProcessor):
    """文本文件处理器"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理文本文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            # 尝试不同的编码读取文件
            encodings = ['utf-8', 'utf-16', 'latin-1', 'gbk', 'gb2312']
            content = ""
            detected_encoding = 'unknown'
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    detected_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                raise Exception("无法解码文件内容")
            
            metadata = {
                'file_type': 'text',
                'encoding': detected_encoding,
                'line_count': len(content.split('\n')),
                'char_count': len(content)
            }
            
            logger.info(f"成功处理文本文件: {file_path}, 字符数: {len(content)}")
            return content, metadata
            
        except Exception as e:
            logger.error(f"处理文本文件失败: {file_path}, 错误: {str(e)}")
            raise


class PDFProcessor(FileProcessor):
    """PDF文件处理器"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理PDF文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            content = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
                
                for page_num in range(page_count):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + '\n\n'
            
            metadata = {
                'file_type': 'pdf',
                'page_count': page_count,
                'char_count': len(content)
            }
            
            logger.info(f"成功处理PDF文件: {file_path}, 页数: {page_count}")
            return content.strip(), metadata
            
        except Exception as e:
            logger.error(f"处理PDF文件失败: {file_path}, 错误: {str(e)}")
            raise


class WordProcessor(FileProcessor):
    """Word文件处理器"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理Word文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension == '.docx':
                doc = docx.Document(file_path)
                paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                content = '\n\n'.join(paragraphs)
                
                metadata = {
                    'file_type': 'docx',
                    'paragraph_count': len(paragraphs),
                    'char_count': len(content)
                }
            else:
                # .doc格式需要其他库支持，这里简化处理
                raise Exception("不支持的Word格式，仅支持.docx")
            
            logger.info(f"成功处理Word文件: {file_path}, 段落数: {len(paragraphs)}")
            return content, metadata
            
        except Exception as e:
            logger.error(f"处理Word文件失败: {file_path}, 错误: {str(e)}")
            raise


class MarkdownProcessor(FileProcessor):
    """Markdown文件处理器"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理Markdown文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            # 读取Markdown内容
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            if MARKDOWN_AVAILABLE:
                # 转换为纯文本
                html = markdown.markdown(md_content)
                # 简单的HTML转纯文本
                import re
                content = re.sub('<[^<]+?>', '', html)
            else:
                # 如果没有markdown模块，直接使用原始内容
                content = md_content
            
            # 计算Markdown元素数量
            import re
            heading_count = len(re.findall(r'^#+ ', md_content, re.MULTILINE))
            list_count = len(re.findall(r'^[*+-] ', md_content, re.MULTILINE)) + \
                        len(re.findall(r'^\d+\. ', md_content, re.MULTILINE))
            
            metadata = {
                'file_type': 'markdown',
                'heading_count': heading_count,
                'list_count': list_count,
                'char_count': len(content),
                'markdown_available': MARKDOWN_AVAILABLE
            }
            
            logger.info(f"成功处理Markdown文件: {file_path}, 标题数: {heading_count}")
            return content, metadata
            
        except Exception as e:
            logger.error(f"处理Markdown文件失败: {file_path}, 错误: {str(e)}")
            raise


class CSVProcessor(FileProcessor):
    """CSV文件处理器"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理CSV文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            rows = []
            headers = []
            
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, newline='') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    break
                except (UnicodeDecodeError, csv.Error):
                    continue
            
            if not rows:
                raise Exception("无法读取CSV文件内容")
            
            headers = rows[0] if rows else []
            
            # 将CSV转换为可读文本
            content_lines = []
            content_lines.append(f"CSV文件包含 {len(headers)} 列: {', '.join(headers)}")
            content_lines.append(f"总共 {len(rows) - 1} 行数据")
            content_lines.append("")
            content_lines.append("数据预览:")
            
            # 添加一些示例数据行
            for i, row in enumerate(rows[:11]):  # 显示前10行
                if i == 0:
                    content_lines.append(f"标题行: {', '.join(row)}")
                else:
                    content_lines.append(f"数据行 {i}: {', '.join(row)}")
            
            if len(rows) > 11:
                content_lines.append(f"... 还有 {len(rows) - 11} 行未显示")
            
            content = '\n'.join(content_lines)
            
            metadata = {
                'file_type': 'csv',
                'columns': headers,
                'row_count': len(rows),
                'encoding': encoding
            }
            
            logger.info(f"成功处理CSV文件: {file_path}, 行数: {len(rows)}")
            return content, metadata
            
        except Exception as e:
            logger.error(f"处理CSV文件失败: {file_path}, 错误: {str(e)}")
            raise


class DataFileProcessor(FileProcessor):
    """数据文件处理器（JSON/XML）"""
    
    def process(self, file_path: str) -> Tuple[str, Dict]:
        """处理JSON或XML文件"""
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                raise Exception(error_msg)
            
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension == '.json':
                return self._process_json(file_path)
            elif extension == '.xml':
                return self._process_xml(file_path)
            else:
                raise Exception("不支持的数据文件格式")
                
        except Exception as e:
            logger.error(f"处理数据文件失败: {file_path}, 错误: {str(e)}")
            raise
    
    def _process_json(self, file_path: str) -> Tuple[str, Dict]:
        """处理JSON文件"""
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 将JSON数据转换为可读文本
            content_lines = []
            content_lines.append("JSON数据概览:")
            
            if isinstance(data, dict):
                content_lines.append(f"包含 {len(data)} 个键值对")
                content_lines.append(f"键列表: {', '.join(list(data.keys())[:20])}")
                if len(data) > 20:
                    content_lines.append(f"... 还有 {len(data) - 20} 个键未显示")
            elif isinstance(data, list):
                content_lines.append(f"包含 {len(data)} 个元素")
            
            content_lines.append("")
            content_lines.append("数据预览:")
            
            # 显示前几个元素
            preview = json.dumps(data, ensure_ascii=False, indent=2)[:2000]
            content_lines.append(preview)
            if len(preview) == 2000:
                content_lines.append("... 数据过大，已截断")
            
            content = '\n'.join(content_lines)
            
            metadata = {
                'file_type': 'json',
                'structure_type': 'object' if isinstance(data, dict) else 'array',
                'size': len(json.dumps(data))
            }
            
            return content, metadata
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析错误: {str(e)}")
    
    def _process_xml(self, file_path: str) -> Tuple[str, Dict]:
        """处理XML文件"""
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 分析XML结构
            content_lines = []
            content_lines.append("XML数据概览:")
            content_lines.append(f"根元素: {root.tag}")
            content_lines.append(f"子元素数量: {len(list(root))}")
            
            # 统计不同类型的子元素
            child_tags = {}
            for child in root:
                child_tags[child.tag] = child_tags.get(child.tag, 0) + 1
            
            content_lines.append(f"子元素类型数量: {len(child_tags)}")
            content_lines.append("子元素类型:")
            for tag, count in list(child_tags.items())[:10]:
                content_lines.append(f"  - {tag}: {count}个")
            if len(child_tags) > 10:
                content_lines.append(f"  ... 还有 {len(child_tags) - 10} 种类型")
            
            # 简单的XML转文本
            import xml.dom.minidom as md
            dom = md.parse(file_path)
            pretty_xml = dom.toprettyxml(indent="  ")[:2000]
            
            content_lines.append("")
            content_lines.append("XML预览:")
            content_lines.append(pretty_xml)
            if len(pretty_xml) == 2000:
                content_lines.append("... 数据过大，已截断")
            
            content = '\n'.join(content_lines)
            
            metadata = {
                'file_type': 'xml',
                'root_tag': root.tag,
                'child_count': len(list(root))
            }
            
            return content, metadata
            
        except ET.ParseError as e:
            raise Exception(f"XML解析错误: {str(e)}")


# 工厂函数
def create_file_processor(file_path: str) -> FileProcessor:
    """
    创建文件处理器实例
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件处理器实例
    
    Raises:
        ValueError: 如果文件类型不支持
    """
    processor = FileProcessor.get_processor(file_path)
    if not processor:
        raise ValueError(f"不支持的文件类型: {os.path.splitext(file_path)[1]}")
    return processor
