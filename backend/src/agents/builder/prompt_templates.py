"""提示词模板管理模块"""

from typing import Dict, List, Optional


class PromptTemplateManager:
    """提示词模板管理器"""
    
    def __init__(self):
        self._templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """初始化提示词模板"""
        return {
            "通用": {
            "entity_extraction": """
你是一个专业的知识图谱构建助手，请从以下markdown文本中提取所有可能的实体。每个实体应该包含名称、类型和简要描述。

支持的实体类型包括但不限于：
{entity_types}

文本内容:
{content}

请仔细分析markdown文本，特别关注以下内容：
1. 标题（如## 公司实体）中的实体
2. 二级标题（如### 灵图智谱科技有限公司）中的实体
3. 列表项（如- 创始人：马云）中的实体
4. 关系列表项（如- 张明 创立 灵图智谱科技有限公司）中的实体
5. 段落中的实体
6. 表格中的实体

提取所有有意义的实体，包括但不限于：
1. 人物、组织、地点、事件
2. 概念、产品、服务、时间
3. 数值、日期、货币、计量单位
4. 文档、媒体、奖项、理论
5. 行业特定的实体

请特别注意处理以下格式：
- 对于二级标题（如### 灵图智谱科技有限公司），将其作为实体名称
- 对于列表项（如- 创始人：马云），提取值（马云）作为实体
- 对于关系列表项（如- 张明 创立 灵图智谱科技有限公司），提取所有相关实体

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "name": "实体名称",
        "type": "实体类型",
        "description": "实体的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

示例输出：
[
    {{
        "name": "灵图智谱科技有限公司",
        "type": "Organization",
        "description": "一家科技公司",
        "properties": {{
            "成立时间": "2023年",
            "创始人": "张明"
        }}
    }},
    {{
        "name": "张明",
        "type": "Person",
        "description": "灵图智谱科技有限公司创始人",
        "properties": {{
            "职位": "CEO",
            "学历": "清华大学计算机博士"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。如果没有找到实体，请返回空数组[]。
""",
            "relation_extraction": """
你是一个专业的知识图谱构建助手，请从以下markdown文本中提取实体之间的所有可能关系。每个关系应该包含源实体、目标实体、关系类型和简要描述。

已知实体列表:
{entities}

文本内容:
{content}

支持的关系类型包括但不限于：
{relation_types}

请仔细分析markdown文本，特别关注以下内容：
1. 列表项（如- 张明 创立 灵图智谱科技有限公司）中的关系
2. 标题中的关系
3. 段落中的关系
4. 表格中的关系

提取所有实体之间的关系，包括但不限于：
1. 包含关系、属于关系、关联关系
2. 因果关系、时间关系、创建关系
3. 拥有关系、位置关系、相似关系
4. 层次关系、使用关系、产生关系
5. 消耗关系、影响关系、依赖关系
6. 合作关系、竞争关系、继承关系
7. 扩展关系、实现关系
8. 创立关系、开发关系、合作关系、基于关系、毕业关系

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型",
        "description": "关系的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

示例输出：
[
    {{
        "source": "张明",
        "target": "灵图智谱科技有限公司",
        "type": "创立",
        "description": "张明创立了灵图智谱科技有限公司",
        "properties": {{
            "成立时间": "2023年"
        }}
    }},
    {{
        "source": "灵图智谱科技有限公司",
        "target": "灵图知识图谱平台",
        "type": "开发",
        "description": "灵图智谱科技有限公司开发了灵图知识图谱平台",
        "properties": {{
            "发布时间": "2024年3月"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。如果没有找到关系，请返回空数组[]。
""",
                "entity_enrichment": """
请为以下实体提供更详细的类型、描述和相关属性。

实体名称: {entity_name}
当前类型: {entity_type}
当前描述: {entity_description}
所属行业: {industry}

请根据实体类型和所属行业提供尽可能多的相关属性，建议包含：{properties_suggestions}

请以以下JSON格式输出，确保是有效的JSON：
{{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {{
        "属性1": "值1",
        "属性2": "值2"
    }}
}}

请只返回JSON，不要包含其他说明文字。
"""
            },
            "金融": {
                "entity_extraction": """
请从以下金融文本中提取所有金融相关实体。请特别关注金融产品、金融机构、金融指标等实体。

支持的实体类型包括但不限于：
{entity_types}

文本内容:
{content}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "name": "实体名称",
        "type": "实体类型",
        "description": "实体的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "relation_extraction": """
请从以下金融文本中提取实体之间的金融关系。请特别关注投资、持有、交易、监管等金融关系。

已知实体列表:
{entities}

文本内容:
{content}

支持的关系类型包括但不限于：
{relation_types}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型",
        "description": "关系的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "entity_enrichment": """
请为以下金融实体提供更详细的类型、描述和相关金融属性。

实体名称: {entity_name}
当前类型: {entity_type}
当前描述: {entity_description}
所属行业: 金融

请根据实体类型提供尽可能多的相关金融属性，建议包含：{properties_suggestions}

请以以下JSON格式输出，确保是有效的JSON：
{{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {{
        "属性1": "值1",
        "属性2": "值2"
    }}
}}

请只返回JSON，不要包含其他说明文字。
"""
            },
            "医疗": {
                "entity_extraction": """
请从以下医疗文本中提取所有医疗相关实体。请特别关注疾病、药物、症状、治疗方法等实体。

支持的实体类型包括但不限于：
{entity_types}

文本内容:
{content}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "name": "实体名称",
        "type": "实体类型",
        "description": "实体的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "relation_extraction": """
请从以下医疗文本中提取实体之间的医疗关系。请特别关注诊断、治疗、导致、症状等医疗关系。

已知实体列表:
{entities}

文本内容:
{content}

支持的关系类型包括但不限于：
{relation_types}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型",
        "description": "关系的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "entity_enrichment": """
请为以下医疗实体提供更详细的类型、描述和相关医疗属性。

实体名称: {entity_name}
当前类型: {entity_type}
当前描述: {entity_description}
所属行业: 医疗

请根据实体类型提供尽可能多的相关医疗属性，建议包含：{properties_suggestions}

请以以下JSON格式输出，确保是有效的JSON：
{{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {{
        "属性1": "值1",
        "属性2": "值2"
    }}
}}

请只返回JSON，不要包含其他说明文字。
"""
            },
            "法律": {
                "entity_extraction": """
请从以下法律文本中提取所有法律相关实体。请特别关注法律条款、案例、法规、法律程序等实体。

支持的实体类型包括但不限于：
{entity_types}

文本内容:
{content}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "name": "实体名称",
        "type": "实体类型",
        "description": "实体的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "relation_extraction": """
请从以下法律文本中提取实体之间的法律关系。请特别关注适用、违反、遵循、引用等法律关系。

已知实体列表:
{entities}

文本内容:
{content}

支持的关系类型包括但不限于：
{relation_types}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型",
        "description": "关系的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "entity_enrichment": """
请为以下法律实体提供更详细的类型、描述和相关法律属性。

实体名称: {entity_name}
当前类型: {entity_type}
当前描述: {entity_description}
所属行业: 法律

请根据实体类型提供尽可能多的相关法律属性，建议包含：{properties_suggestions}

请以以下JSON格式输出，确保是有效的JSON：
{{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {{
        "属性1": "值1",
        "属性2": "值2"
    }}
}}

请只返回JSON，不要包含其他说明文字。
"""
            },
            "技术": {
                "entity_extraction": """
请从以下技术文本中提取所有技术相关实体。请特别关注编程语言、框架、库、算法等实体。

支持的实体类型包括但不限于：
{entity_types}

文本内容:
{content}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "name": "实体名称",
        "type": "实体类型",
        "description": "实体的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "relation_extraction": """
请从以下技术文本中提取实体之间的技术关系。请特别关注依赖、实现、使用、基于等技术关系。

已知实体列表:
{entities}

文本内容:
{content}

支持的关系类型包括但不限于：
{relation_types}

请以以下JSON格式输出，确保是有效的JSON：
[
    {{
        "source": "源实体名称",
        "target": "目标实体名称",
        "type": "关系类型",
        "description": "关系的简要描述",
        "properties": {{
            "属性名1": "属性值1",
            "属性名2": "属性值2"
        }}
    }}
]

请只返回JSON，不要包含其他说明文字。
""",
                "entity_enrichment": """
请为以下技术实体提供更详细的类型、描述和相关技术属性。

实体名称: {entity_name}
当前类型: {entity_type}
当前描述: {entity_description}
所属行业: 技术

请根据实体类型提供尽可能多的相关技术属性，建议包含：{properties_suggestions}

请以以下JSON格式输出，确保是有效的JSON：
{{
    "type": "更具体的实体类型",
    "description": "详细描述",
    "properties": {{
        "属性1": "值1",
        "属性2": "值2"
    }}
}}

请只返回JSON，不要包含其他说明文字。
"""
            }
        }
    
    def get_template(self, industry: str, template_type: str) -> str:
        """获取指定行业和类型的提示词模板"""
        # 首先尝试获取行业特定模板
        if industry in self._templates and template_type in self._templates[industry]:
            return self._templates[industry][template_type]
        # 如果没有找到，返回通用模板
        elif "通用" in self._templates and template_type in self._templates["通用"]:
            return self._templates["通用"][template_type]
        else:
            raise ValueError(f"未找到行业 '{industry}' 的模板类型 '{template_type}'")
    
    def add_template(self, industry: str, template_type: str, template_content: str) -> None:
        """添加新的提示词模板"""
        if industry not in self._templates:
            self._templates[industry] = {}
        self._templates[industry][template_type] = template_content
    
    def update_template(self, industry: str, template_type: str, template_content: str) -> None:
        """更新现有提示词模板"""
        if industry not in self._templates or template_type not in self._templates[industry]:
            raise ValueError(f"未找到行业 '{industry}' 的模板类型 '{template_type}'")
        self._templates[industry][template_type] = template_content
    
    def get_available_industries(self) -> List[str]:
        """获取所有可用的行业"""
        return list(self._templates.keys())
    
    def get_available_template_types(self, industry: str) -> List[str]:
        """获取指定行业的所有可用模板类型"""
        if industry in self._templates:
            return list(self._templates[industry].keys())
        else:
            return []


# 创建全局提示词模板管理器实例
prompt_template_manager = PromptTemplateManager()
