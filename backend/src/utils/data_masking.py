import re
from typing import Any, Optional


class DataMasking:
    """敏感数据脱敏工具类"""
    
    @staticmethod
    def mask_email(email: str, show_prefix: int = 2, show_suffix: int = 2) -> str:
        """
        脱敏邮箱地址
        
        Args:
            email: 邮箱地址
            show_prefix: 显示前缀字符数
            show_suffix: 显示后缀字符数
            
        Returns:
            str: 脱敏后的邮箱地址
        """
        if not email or '@' not in email:
            return email
        
        username, domain = email.split('@', 1)
        domain_parts = domain.split('.')
        
        # 处理用户名
        if len(username) <= show_prefix + show_suffix:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1] if len(username) > 2 else username
        else:
            masked_username = username[:show_prefix] + '*' * (len(username) - show_prefix - show_suffix) + username[-show_suffix:]
        
        # 处理域名
        if len(domain_parts) < 2:
            return f"{masked_username}@{domain}"
        
        domain_name = domain_parts[0]
        tld = '.'.join(domain_parts[1:])
        
        if len(domain_name) <= 2:
            masked_domain = domain_name[0] + '*' * (len(domain_name) - 1) if len(domain_name) > 1 else domain_name
        else:
            masked_domain = domain_name[0] + '*' * (len(domain_name) - 2) + domain_name[-1]
        
        return f"{masked_username}@{masked_domain}.{tld}"
    
    @staticmethod
    def mask_phone(phone: str, show_prefix: int = 3, show_suffix: int = 4) -> str:
        """
        脱敏手机号码
        
        Args:
            phone: 手机号码
            show_prefix: 显示前缀字符数
            show_suffix: 显示后缀字符数
            
        Returns:
            str: 脱敏后的手机号码
        """
        if not phone:
            return phone
        
        # 移除非数字字符
        phone = re.sub(r'\D', '', phone)
        
        if len(phone) <= show_prefix + show_suffix:
            return phone
        
        return phone[:show_prefix] + '*' * (len(phone) - show_prefix - show_suffix) + phone[-show_suffix:]
    
    @staticmethod
    def mask_id_card(id_card: str, show_prefix: int = 6, show_suffix: int = 4) -> str:
        """
        脱敏身份证号码
        
        Args:
            id_card: 身份证号码
            show_prefix: 显示前缀字符数
            show_suffix: 显示后缀字符数
            
        Returns:
            str: 脱敏后的身份证号码
        """
        if not id_card:
            return id_card
        
        if len(id_card) <= show_prefix + show_suffix:
            return id_card
        
        return id_card[:show_prefix] + '*' * (len(id_card) - show_prefix - show_suffix) + id_card[-show_suffix:]
    
    @staticmethod
    def mask_bank_card(bank_card: str, show_prefix: int = 4, show_suffix: int = 4) -> str:
        """
        脱敏银行卡号
        
        Args:
            bank_card: 银行卡号
            show_prefix: 显示前缀字符数
            show_suffix: 显示后缀字符数
            
        Returns:
            str: 脱敏后的银行卡号
        """
        if not bank_card:
            return bank_card
        
        # 移除非数字字符
        bank_card = re.sub(r'\D', '', bank_card)
        
        if len(bank_card) <= show_prefix + show_suffix:
            return bank_card
        
        return bank_card[:show_prefix] + '*' * (len(bank_card) - show_prefix - show_suffix) + bank_card[-show_suffix:]
    
    @staticmethod
    def mask_password(password: str) -> str:
        """
        脱敏密码
        
        Args:
            password: 密码
            
        Returns:
            str: 脱敏后的密码
        """
        if not password:
            return password
        
        return '*' * len(password)
    
    @staticmethod
    def mask_name(name: str, show_first: bool = True) -> str:
        """
        脱敏姓名
        
        Args:
            name: 姓名
            show_first: 是否显示第一个字符
            
        Returns:
            str: 脱敏后的姓名
        """
        if not name:
            return name
        
        if len(name) == 1:
            return name
        elif len(name) == 2:
            return name[0] + '*'
        else:
            if show_first:
                return name[0] + '*' * (len(name) - 1)
            else:
                return '*' * (len(name) - 1) + name[-1]
    
    @staticmethod
    def mask_ip(ip: str, show_prefix: int = 2) -> str:
        """
        脱敏IP地址
        
        Args:
            ip: IP地址
            show_prefix: 显示前缀段数
            
        Returns:
            str: 脱敏后的IP地址
        """
        if not ip:
            return ip
        
        # 支持IPv4和IPv6
        if '.' in ip:  # IPv4
            parts = ip.split('.')
            if len(parts) != 4:
                return ip
            
            if show_prefix < 1:
                return '*.*.*.*'
            elif show_prefix >= 4:
                return ip
            
            masked_parts = parts[:show_prefix] + ['*'] * (4 - show_prefix)
            return '.'.join(masked_parts)
        elif ':' in ip:  # IPv6
            # 简化处理，只显示前两段
            parts = ip.split(':')
            if len(parts) < 2:
                return ip
            
            return f"{parts[0]}:{parts[1]}:*:*:*:*:*:*"
        
        return ip
    
    @staticmethod
    def mask_general(data: Any, show_prefix: int = 2, show_suffix: int = 2) -> Any:
        """
        通用脱敏方法
        
        Args:
            data: 待脱敏数据
            show_prefix: 显示前缀字符数
            show_suffix: 显示后缀字符数
            
        Returns:
            Any: 脱敏后的数据
        """
        if not isinstance(data, str):
            return data
        
        if len(data) <= show_prefix + show_suffix:
            return data
        
        return data[:show_prefix] + '*' * (len(data) - show_prefix - show_suffix) + data[-show_suffix:]
    
    @staticmethod
    def auto_mask(data: Any, data_type: Optional[str] = None) -> Any:
        """
        自动根据数据类型进行脱敏
        
        Args:
            data: 待脱敏数据
            data_type: 数据类型，可选值：email, phone, id_card, bank_card, password, name, ip
            
        Returns:
            Any: 脱敏后的数据
        """
        if not isinstance(data, str):
            return data
        
        if data_type:
            # 根据指定类型脱敏
            if data_type == 'email':
                return DataMasking.mask_email(data)
            elif data_type == 'phone':
                return DataMasking.mask_phone(data)
            elif data_type == 'id_card':
                return DataMasking.mask_id_card(data)
            elif data_type == 'bank_card':
                return DataMasking.mask_bank_card(data)
            elif data_type == 'password':
                return DataMasking.mask_password(data)
            elif data_type == 'name':
                return DataMasking.mask_name(data)
            elif data_type == 'ip':
                return DataMasking.mask_ip(data)
            else:
                return DataMasking.mask_general(data)
        else:
            # 自动识别类型并脱敏
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data):
                return DataMasking.mask_email(data)
            elif re.match(r'^1[3-9]\d{9}$', data):
                return DataMasking.mask_phone(data)
            elif re.match(r'^\d{15}$|^\d{17}[\dXx]$', data):
                return DataMasking.mask_id_card(data)
            elif re.match(r'^\d{16,19}$', data):
                return DataMasking.mask_bank_card(data)
            elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', data):
                return DataMasking.mask_ip(data)
            else:
                return data
    
    @staticmethod
    def mask_dict(data: dict, mask_fields: list, auto_detect: bool = True) -> dict:
        """
        脱敏字典中的敏感字段
        
        Args:
            data: 待脱敏字典
            mask_fields: 需要脱敏的字段列表，支持格式：field_name 或 field_name:type
            auto_detect: 是否自动检测字段类型
            
        Returns:
            dict: 脱敏后的字典
        """
        if not isinstance(data, dict):
            return data
        
        result = data.copy()
        
        for field in mask_fields:
            field_info = field.split(':', 1)
            field_name = field_info[0]
            field_type = field_info[1] if len(field_info) > 1 else None
            
            if field_name in result:
                if auto_detect and not field_type:
                    result[field_name] = DataMasking.auto_mask(result[field_name])
                else:
                    result[field_name] = DataMasking.auto_mask(result[field_name], field_type)
        
        return result
    
    @staticmethod
    def mask_list(data: list, mask_fields: list, auto_detect: bool = True) -> list:
        """
        脱敏列表中的敏感字段
        
        Args:
            data: 待脱敏列表
            mask_fields: 需要脱敏的字段列表
            auto_detect: 是否自动检测字段类型
            
        Returns:
            list: 脱敏后的列表
        """
        if not isinstance(data, list):
            return data
        
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(DataMasking.mask_dict(item, mask_fields, auto_detect))
            else:
                result.append(item)
        
        return result


# 创建全局脱敏工具实例
data_masking = DataMasking()
