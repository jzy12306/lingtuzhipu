import io
import re
from typing import Optional
from PyPDF2 import PdfReader
import pandas as pd
import docx


def clean_text(text: str) -> str:
    """
    清理文本内容，去除多余的空白字符和特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    # 去除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    text = text.strip()
    # 去除不可见的控制字符（保留换行和制表符）
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    return text


async def process_pdf(file_stream: io.BytesIO) -> str:
    """
    处理PDF文件，提取文本内容
    
    Args:
        file_stream: PDF文件流
        
    Returns:
        提取的文本内容
    """
    try:
        reader = PdfReader(file_stream)
        text_content = []
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text_content.append(clean_text(page_text))
        
        return '\n\n'.join(text_content)
        
    except Exception as e:
        raise Exception(f"处理PDF文件失败: {str(e)}")


async def process_text(file_stream: io.BytesIO) -> str:
    """
    处理文本文件，提取文本内容
    
    Args:
        file_stream: 文本文件流
        
    Returns:
        提取的文本内容
    """
    try:
        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'latin-1']
        
        for encoding in encodings:
            try:
                file_stream.seek(0)
                text = file_stream.read().decode(encoding)
                return clean_text(text)
            except UnicodeDecodeError:
                continue
        
        raise Exception("无法解码文本文件，请检查文件编码")
        
    except Exception as e:
        raise Exception(f"处理文本文件失败: {str(e)}")


async def process_csv(file_stream: io.BytesIO) -> str:
    """
    处理CSV文件，提取文本内容
    
    Args:
        file_stream: CSV文件流
        
    Returns:
        提取的文本内容
    """
    try:
        file_stream.seek(0)
        # 尝试不同的编码读取CSV
        encodings = ['utf-8', 'gbk', 'latin-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_stream)
                break
            except UnicodeDecodeError:
                file_stream.seek(0)
                continue
        
        if df is None:
            raise Exception("无法解码CSV文件，请检查文件编码")
        
        # 将DataFrame转换为文本描述
        text_content = []
        
        # 添加列信息
        text_content.append(f"列名: {', '.join(df.columns.tolist())}")
        text_content.append("")
        
        # 添加数据类型信息
        dtypes_info = []
        for col in df.columns:
            dtypes_info.append(f"{col}: {str(df[col].dtype)}")
        text_content.append(f"数据类型: {'; '.join(dtypes_info)}")
        text_content.append("")
        
        # 添加数据统计信息
        text_content.append(f"总行数: {len(df)}")
        text_content.append("")
        
        # 添加前10行数据作为示例
        text_content.append("数据示例 (前10行):")
        text_content.append(df.head(10).to_string())
        
        # 添加数值列的统计信息
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            text_content.append("")
            text_content.append("数值列统计信息:")
            text_content.append(df[numeric_cols].describe().to_string())
        
        return '\n'.join(text_content)
        
    except Exception as e:
        raise Exception(f"处理CSV文件失败: {str(e)}")


async def process_excel(file_stream: io.BytesIO) -> str:
    """
    处理Excel文件，提取文本内容
    
    Args:
        file_stream: Excel文件流
        
    Returns:
        提取的文本内容
    """
    try:
        file_stream.seek(0)
        xl = pd.ExcelFile(file_stream)
        text_content = []
        
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            
            text_content.append(f"\n=== 工作表: {sheet_name} ===")
            text_content.append(f"列名: {', '.join(df.columns.tolist())}")
            text_content.append(f"总行数: {len(df)}")
            
            # 添加前5行数据作为示例
            if len(df) > 0:
                text_content.append("数据示例 (前5行):")
                text_content.append(df.head(5).to_string())
            
            # 添加数值列的统计信息
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_content.append("数值列统计信息:")
                text_content.append(df[numeric_cols].describe().to_string())
        
        return '\n'.join(text_content)
        
    except Exception as e:
        raise Exception(f"处理Excel文件失败: {str(e)}")


async def process_docx(file_stream: io.BytesIO) -> str:
    """
    处理Word文档，提取文本内容
    
    Args:
        file_stream: Word文档流
        
    Returns:
        提取的文本内容
    """
    try:
        doc = docx.Document(file_stream)
        text_content = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(clean_text(para.text))
        
        # 添加表格信息
        for i, table in enumerate(doc.tables):
            text_content.append(f"\n=== 表格 {i+1} ===")
            
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(clean_text(cell.text))
                if row_text:
                    text_content.append(' | '.join(row_text))
        
        return '\n\n'.join(text_content)
        
    except Exception as e:
        raise Exception(f"处理Word文档失败: {str(e)}")


async def process_uploaded_file(file_stream: io.BytesIO, content_type: str) -> str:
    """
    根据文件类型处理上传的文件，提取文本内容
    
    Args:
        file_stream: 文件流
        content_type: 文件内容类型
        
    Returns:
        提取的文本内容
    """
    # 根据内容类型选择处理器
    if content_type == 'application/pdf':
        return await process_pdf(file_stream)
    elif content_type == 'text/plain' or content_type == 'text/markdown':
        return await process_text(file_stream)
    elif content_type == 'text/csv':
        return await process_csv(file_stream)
    elif content_type in [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]:
        return await process_excel(file_stream)
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return await process_docx(file_stream)
    else:
        raise Exception(f"不支持的文件类型: {content_type}")


async def get_file_metadata(file_stream: io.BytesIO, content_type: str) -> dict:
    """
    获取文件的元数据信息
    
    Args:
        file_stream: 文件流
        content_type: 文件内容类型
        
    Returns:
        元数据字典
    """
    metadata = {
        "content_type": content_type,
        "file_size": file_stream.getbuffer().nbytes,
    }
    
    # 根据文件类型获取额外的元数据
    if content_type == 'application/pdf':
        try:
            file_stream.seek(0)
            reader = PdfReader(file_stream)
            metadata["page_count"] = len(reader.pages)
            # 尝试获取PDF的元数据
            pdf_metadata = reader.metadata
            if pdf_metadata:
                for key, value in pdf_metadata.items():
                    metadata[f"pdf_{key}"] = value
        except Exception:
            pass
    
    return metadata