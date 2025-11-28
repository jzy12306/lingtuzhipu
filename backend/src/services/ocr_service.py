import logging
import sys
import uuid
import requests
import base64
import hashlib
import time
from typing import Dict, Any, Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    有道智云OCR服务封装
    支持图片和扫描件PDF的OCR识别
    """
    
    def __init__(self):
        """
        初始化OCR服务
        """
        self.youdao_url = "https://openapi.youdao.com/ocrapi"
        self.app_key = "635ca85171ddd9b1"
        self.app_secret = "uP1V8rD9MBdp75SktmwIRlbuicG2Qg6z"
        self.logger = logger.getChild("OCRService")
        
        self.logger.info("OCR服务初始化完成")
    
    def truncate(self, q: str) -> str:
        """
        截断字符串，用于生成签名
        
        Args:
            q: 要截断的字符串
            
        Returns:
            截断后的字符串
        """
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]
    
    def encrypt(self, sign_str: str) -> str:
        """
        生成签名
        
        Args:
            sign_str: 签名字符串
            
        Returns:
            加密后的签名
        """
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(sign_str.encode('utf-8'))
        return hash_algorithm.hexdigest()
    
    def do_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            data: 请求数据
            
        Returns:
            API响应结果
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            response = requests.post(self.youdao_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OCR API请求失败: {str(e)}")
            raise
    
    async def recognize_image(self, image_path: str, detect_type: str = "Accurate", lang_type: str = "zh-CHS") -> Dict[str, Any]:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片路径
            detect_type: 识别类型，默认为"Accurate"
            lang_type: 语言类型，默认为"zh-CHS"
            
        Returns:
            OCR识别结果
        """
        try:
            self.logger.info(f"开始识别图片: {image_path}")
            
            # 读取图片文件并编码为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                q = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求数据
            data = {
                'detectType': detect_type,
                'imageType': '1',
                'langType': lang_type,
                'img': q,
                'docType': 'json',
                'signType': 'v3',
                'curtime': str(int(time.time())),
                'salt': str(uuid.uuid1())
            }
            
            # 生成签名
            sign_str = self.app_key + self.truncate(q) + data['salt'] + data['curtime'] + self.app_secret
            data['sign'] = self.encrypt(sign_str)
            data['appKey'] = self.app_key
            
            # 发送请求
            response = self.do_request(data)
            self.logger.info(f"图片识别完成: {image_path}")
            
            return response
        except Exception as e:
            self.logger.error(f"图片识别失败: {image_path}, 错误: {str(e)}")
            raise
    
    async def recognize_pdf(self, pdf_path: str, detect_type: str = "Accurate", lang_type: str = "zh-CHS") -> Dict[str, Any]:
        """
        识别PDF扫描件中的文字
        
        Args:
            pdf_path: PDF文件路径
            detect_type: 识别类型，默认为"Accurate"
            lang_type: 语言类型，默认为"zh-CHS"
            
        Returns:
            OCR识别结果
        """
        try:
            self.logger.info(f"开始识别PDF扫描件: {pdf_path}")
            
            # 读取PDF文件并编码为base64
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
                q = base64.b64encode(pdf_data).decode('utf-8')
            
            # 构建请求数据
            data = {
                'detectType': detect_type,
                'imageType': '1',
                'langType': lang_type,
                'img': q,
                'docType': 'json',
                'signType': 'v3',
                'curtime': str(int(time.time())),
                'salt': str(uuid.uuid1())
            }
            
            # 生成签名
            sign_str = self.app_key + self.truncate(q) + data['salt'] + data['curtime'] + self.app_secret
            data['sign'] = self.encrypt(sign_str)
            data['appKey'] = self.app_key
            
            # 发送请求
            response = self.do_request(data)
            self.logger.info(f"PDF扫描件识别完成: {pdf_path}")
            
            return response
        except Exception as e:
            self.logger.error(f"PDF扫描件识别失败: {pdf_path}, 错误: {str(e)}")
            raise
    
    async def recognize_image_stream(self, image_stream, detect_type: str = "Accurate", lang_type: str = "zh-CHS") -> Dict[str, Any]:
        """
        识别图片流或字符串中的文字
        
        Args:
            image_stream: 图片流或字符串内容
            detect_type: 识别类型，默认为"Accurate"
            lang_type: 语言类型，默认为"zh-CHS"
            
        Returns:
            OCR识别结果
        """
        try:
            self.logger.info("开始识别图片内容")
            
            # 处理不同类型的输入
            image_data = None
            if hasattr(image_stream, 'read'):
                # 如果是文件流对象，直接读取
                image_data = image_stream.read()
            else:
                # 如果是字符串，直接使用
                if isinstance(image_stream, str):
                    # 对于字符串，假设是已经提取的文本，直接返回
                    self.logger.info("图片内容为字符串，直接返回")
                    return {"regions": [{"lines": [{"words": [{"text": image_stream}]}]}], "content": image_stream}
                else:
                    # 其他类型，转换为bytes
                    image_data = image_stream
            
            # 编码为base64
            q = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求数据
            data = {
                'detectType': detect_type,
                'imageType': '1',
                'langType': lang_type,
                'img': q,
                'docType': 'json',
                'signType': 'v3',
                'curtime': str(int(time.time())),
                'salt': str(uuid.uuid1())
            }
            
            # 生成签名
            sign_str = self.app_key + self.truncate(q) + data['salt'] + data['curtime'] + self.app_secret
            data['sign'] = self.encrypt(sign_str)
            data['appKey'] = self.app_key
            
            # 发送请求
            response = self.do_request(data)
            self.logger.info("图片内容识别完成")
            
            return response
        except Exception as e:
            self.logger.error(f"图片内容识别失败: {str(e)}")
            raise
    
    async def recognize_pdf_stream(self, pdf_stream, detect_type: str = "Accurate", lang_type: str = "zh-CHS") -> Dict[str, Any]:
        """
        识别PDF文件流或字符串中的文字
        
        Args:
            pdf_stream: PDF文件流或字符串内容
            detect_type: 识别类型，默认为"Accurate"
            lang_type: 语言类型，默认为"zh-CHS"
            
        Returns:
            OCR识别结果
        """
        try:
            self.logger.info("开始识别PDF内容")
            
            # 处理不同类型的输入
            pdf_data = None
            if hasattr(pdf_stream, 'read'):
                # 如果是文件流对象，直接读取
                pdf_data = pdf_stream.read()
            else:
                # 如果是字符串，直接使用
                if isinstance(pdf_stream, str):
                    # 对于字符串，假设是已经提取的文本，直接返回
                    self.logger.info("PDF内容为字符串，直接返回")
                    return {"regions": [{"lines": [{"words": [{"text": pdf_stream}]}]}], "content": pdf_stream}
                else:
                    # 其他类型，转换为bytes
                    pdf_data = pdf_stream
            
            # 编码为base64
            q = base64.b64encode(pdf_data).decode('utf-8')
            
            # 构建请求数据
            data = {
                'detectType': detect_type,
                'imageType': '1',
                'langType': lang_type,
                'img': q,
                'docType': 'json',
                'signType': 'v3',
                'curtime': str(int(time.time())),
                'salt': str(uuid.uuid1())
            }
            
            # 生成签名
            sign_str = self.app_key + self.truncate(q) + data['salt'] + data['curtime'] + self.app_secret
            data['sign'] = self.encrypt(sign_str)
            data['appKey'] = self.app_key
            
            # 发送请求
            response = self.do_request(data)
            self.logger.info("PDF内容识别完成")
            
            return response
        except Exception as e:
            self.logger.error(f"PDF内容识别失败: {str(e)}")
            raise
    
    async def initialize(self) -> bool:
        """
        初始化OCR服务
        
        Returns:
            初始化是否成功
        """
        try:
            self.logger.info("正在初始化OCR服务...")
            # 可以添加一些初始化检查，例如测试API连接
            return True
        except Exception as e:
            self.logger.error(f"OCR服务初始化失败: {str(e)}")
            return False
    
    async def shutdown(self):
        """
        关闭OCR服务
        """
        self.logger.info("OCR服务已关闭")


# 创建全局OCR服务实例
ocr_service = OCRService()
