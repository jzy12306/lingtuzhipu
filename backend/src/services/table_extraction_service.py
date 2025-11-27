import logging
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import fitz  # PyMuPDF
from io import BytesIO

logger = logging.getLogger(__name__)


class TableExtractionService:
    """
    表格提取服务，用于从文档中提取表格数据并结构化
    支持PDF、Excel、CSV等格式的表格提取
    """
    
    def __init__(self):
        self.logger = logger.getChild("TableExtractionService")
        self.initialized = False
    
    async def initialize(self):
        """
        初始化表格提取服务
        """
        try:
            self.logger.info("表格提取服务初始化")
            self.initialized = True
            return self
        except Exception as e:
            self.logger.error(f"表格提取服务初始化失败: {str(e)}")
            self.initialized = False
            raise
    
    async def shutdown(self):
        """
        关闭表格提取服务
        """
        try:
            self.logger.info("表格提取服务已关闭")
        except Exception as e:
            self.logger.warning(f"表格提取服务关闭发生错误: {str(e)}")
    
    async def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        从PDF文件中提取表格
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的表格数据列表，每个表格包含表格内容、位置等信息
        """
        try:
            self.logger.info(f"从PDF文件提取表格: {pdf_path}")
            tables = []
            
            # 使用PyMuPDF打开PDF文件
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 获取页面中的所有表格
                # 这里使用PyMuPDF的表格提取功能
                # 注意：PyMuPDF的表格提取功能需要PDF具有结构化的表格
                page_tables = page.find_tables()
                
                for table_idx, table in enumerate(page_tables.tables):
                    # 提取表格内容
                    table_data = table.extract()
                    
                    if not table_data:
                        continue
                    
                    # 转换为DataFrame进行结构化处理
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    
                    # 构建表格信息
                    table_info = {
                        "page_num": page_num + 1,
                        "table_idx": table_idx + 1,
                        "num_rows": len(df),
                        "num_cols": len(df.columns),
                        "columns": list(df.columns),
                        "data": df.to_dict(orient="records"),
                        "raw_data": table_data,
                        "table_bbox": table.bbox
                    }
                    
                    tables.append(table_info)
            
            doc.close()
            self.logger.info(f"从PDF文件提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            self.logger.error(f"从PDF提取表格失败: {str(e)}", exc_info=True)
            return []
    
    async def extract_tables_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """
        从Excel文件中提取表格
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            提取的表格数据列表
        """
        try:
            self.logger.info(f"从Excel文件提取表格: {excel_path}")
            tables = []
            
            # 使用pandas读取Excel文件
            excel_file = pd.ExcelFile(excel_path)
            
            for sheet_name in excel_file.sheet_names:
                # 读取工作表数据
                df = excel_file.parse(sheet_name)
                
                # 清理数据
                df = df.dropna(how='all')  # 删除全为空的行
                df = df.dropna(axis=1, how='all')  # 删除全为空的列
                
                if df.empty:
                    continue
                
                # 构建表格信息
                table_info = {
                    "sheet_name": sheet_name,
                    "num_rows": len(df),
                    "num_cols": len(df.columns),
                    "columns": list(df.columns),
                    "data": df.to_dict(orient="records"),
                    "raw_data": df.values.tolist()
                }
                
                tables.append(table_info)
            
            self.logger.info(f"从Excel文件提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            self.logger.error(f"从Excel提取表格失败: {str(e)}", exc_info=True)
            return []
    
    async def extract_tables_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        从CSV文件中提取表格
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            提取的表格数据列表
        """
        try:
            self.logger.info(f"从CSV文件提取表格: {csv_path}")
            tables = []
            
            # 使用pandas读取CSV文件
            df = pd.read_csv(csv_path)
            
            # 清理数据
            df = df.dropna(how='all')  # 删除全为空的行
            df = df.dropna(axis=1, how='all')  # 删除全为空的列
            
            if df.empty:
                return tables
            
            # 构建表格信息
            table_info = {
                "num_rows": len(df),
                "num_cols": len(df.columns),
                "columns": list(df.columns),
                "data": df.to_dict(orient="records"),
                "raw_data": df.values.tolist()
            }
            
            tables.append(table_info)
            self.logger.info(f"从CSV文件提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            self.logger.error(f"从CSV提取表格失败: {str(e)}", exc_info=True)
            return []
    
    async def extract_tables_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取表格（简单实现）
        
        Args:
            text: 包含表格的文本
            
        Returns:
            提取的表格数据列表
        """
        try:
            self.logger.info("从文本提取表格")
            tables = []
            
            # 这里实现简单的文本表格提取
            # 适用于使用分隔符（如逗号、制表符）的简单表格
            
            lines = text.strip().split('\n')
            if not lines:
                return tables
            
            # 尝试检测分隔符
            # 检查第一行可能的分隔符
            first_line = lines[0]
            
            # 常见分隔符
            separators = [',', '\t', '|', ';']
            best_sep = None
            max_sep_count = 0
            
            for sep in separators:
                sep_count = first_line.count(sep)
                if sep_count > max_sep_count:
                    max_sep_count = sep_count
                    best_sep = sep
            
            if best_sep and max_sep_count > 0:
                # 尝试解析为表格
                table_data = []
                for line in lines:
                    # 跳过空行
                    if not line.strip():
                        continue
                    
                    # 分割行
                    row = [cell.strip() for cell in line.split(best_sep)]
                    table_data.append(row)
                
                if len(table_data) >= 2:  # 至少需要表头和一行数据
                    # 转换为DataFrame
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    
                    # 构建表格信息
                    table_info = {
                        "num_rows": len(df),
                        "num_cols": len(df.columns),
                        "columns": list(df.columns),
                        "data": df.to_dict(orient="records"),
                        "raw_data": table_data,
                        "separator": best_sep
                    }
                    
                    tables.append(table_info)
            
            self.logger.info(f"从文本提取到 {len(tables)} 个表格")
            return tables
            
        except Exception as e:
            self.logger.error(f"从文本提取表格失败: {str(e)}", exc_info=True)
            return []
    
    async def extract_tables_from_document(self, document_id: str, document_type: str, content: str, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从文档中提取表格
        
        Args:
            document_id: 文档ID
            document_type: 文档类型
            content: 文档内容
            file_path: 文档文件路径（可选）
            
        Returns:
            提取的表格数据列表
        """
        try:
            self.logger.info(f"从文档提取表格: {document_id}, 类型: {document_type}")
            
            tables = []
            
            # 根据文档类型选择提取方法
            if document_type == "pdf" and file_path:
                # 从PDF文件提取表格
                tables = await self.extract_tables_from_pdf(file_path)
            elif document_type == "excel" and file_path:
                # 从Excel文件提取表格
                tables = await self.extract_tables_from_excel(file_path)
            elif document_type == "csv" and file_path:
                # 从CSV文件提取表格
                tables = await self.extract_tables_from_csv(file_path)
            else:
                # 从文本中提取表格
                tables = await self.extract_tables_from_text(content)
            
            # 为每个表格添加文档ID
            for table in tables:
                table["document_id"] = document_id
            
            return tables
            
        except Exception as e:
            self.logger.error(f"从文档提取表格失败: {str(e)}", exc_info=True)
            return []
    
    async def convert_table_to_knowledge(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将表格数据转换为知识图谱可用的格式
        
        Args:
            table_data: 表格数据
            
        Returns:
            转换后的知识图谱数据，包含实体和关系
        """
        try:
            self.logger.info("将表格数据转换为知识图谱格式")
            
            knowledge = {
                "entities": [],
                "relations": [],
                "table_info": table_data
            }
            
            # 简单实现：将表格的每一行转换为一个实体
            # 表格的列作为实体属性
            columns = table_data.get("columns", [])
            data = table_data.get("data", [])
            
            if not columns or not data:
                return knowledge
            
            # 提取实体和关系
            for row_idx, row_data in enumerate(data):
                # 构建实体
                entity = {
                    "name": f"{table_data.get('sheet_name', 'Table')}_{table_data.get('table_idx', 1)}_{row_idx + 1}",
                    "type": "TableEntity",
                    "description": f"表格行数据",
                    "properties": {
                        **row_data,
                        "table_row_idx": row_idx + 1,
                        "table_page": table_data.get("page_num", 1),
                        "table_idx": table_data.get("table_idx", 1)
                    }
                }
                
                knowledge["entities"].append(entity)
            
            # 可以添加更多的关系提取逻辑
            # 例如：根据表格内容提取实体间的关系
            
            return knowledge
            
        except Exception as e:
            self.logger.error(f"将表格数据转换为知识图谱失败: {str(e)}", exc_info=True)
            return {
                "entities": [],
                "relations": [],
                "table_info": table_data
            }


# 创建全局表格提取服务实例
table_extraction_service = TableExtractionService()
