import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from src.agents.builder.builder_agent import BuilderAgent
from src.models.knowledge import Entity, Relation
from src.models.document import Document
from src.repositories.knowledge_repository import KnowledgeRepository
from src.config.settings import settings
from src.services.llm_service import llm_service
from src.agents.builder.prompt_templates import prompt_template_manager

logger = logging.getLogger(__name__)


class LLMBuilderAgent(BuilderAgent):
    """基于LLM的构建者智能体实现"""
    
    def __init__(self, knowledge_repository: KnowledgeRepository):
        super().__init__(knowledge_repository)
        logger.info("LLM构建者智能体初始化完成")
    
    async def process_document(self, document: Document) -> Dict:
        """处理文档并提取知识"""
        try:
            logger.info(f"开始处理文档: {document.title} (ID: {document.id})")
            
            # 从文档元数据获取行业信息，默认为"通用"
            industry = getattr(document, 'industry', '通用')
            
            # 记录文档处理的开始时间
            start_time = datetime.utcnow()
            
            # 步骤1: 提取实体
            entities = await self.extract_entities(
                content=document.content,
                document_id=document.id,
                user_id=document.user_id,
                industry=industry
            )
            logger.info(f"实体提取完成: {document.id}, 共提取 {len(entities)} 个实体")
            
            # 步骤2: 跳过实体丰富，减少API调用次数
            enriched_entities = entities.copy()
            logger.info(f"跳过实体丰富: {document.id}, 实体数: {len(entities)}, 内容长度: {len(document.content)}, 类型: {document.document_type}")
            
            # 步骤3: 提取关系
            relations = await self.extract_relations(
                content=document.content,
                entities=enriched_entities,
                document_id=document.id,
                user_id=document.user_id,
                industry=industry
            )
            logger.info(f"关系提取完成: {document.id}, 共提取 {len(relations)} 个关系")
            
            # 步骤4: 验证提取结果
            valid_entities, valid_relations, validation_errors = await self.validate_extractions(
                entities=enriched_entities,
                relations=relations
            )
            logger.info(f"验证结果: {document.id}, 有效实体: {len(valid_entities)}, 有效关系: {len(valid_relations)}, 错误数: {len(validation_errors)}")
            
            # 步骤5: 保存提取的知识
            save_result = await self.save_extracted_knowledge(
                entities=valid_entities,
                relations=valid_relations,
                document_id=document.id
            )
            logger.info(f"知识保存完成: {document.id}, 实体: {save_result.get('entities', 0)}, 关系: {save_result.get('relations', 0)}")
            
            # 计算处理时间
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                **save_result,
                "validation_errors": validation_errors,
                "processing_time": processing_time,
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"文档处理完成: {document.title}, 耗时: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.exception(f"处理文档失败: {document.title} (ID: {document.id}), 错误: {str(e)}")
            raise
    
    async def extract_entities(self, content: str, document_id: str, user_id: str, industry: str = "通用") -> List[Entity]:
        """从文本内容中提取实体"""
        try:
            # 准备提示词
            prompt = self._prepare_entity_extraction_prompt(content, industry)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析响应
            entities_data = self._parse_entities_from_response(response)
            
            # 转换为Entity对象
            entities = []
            for entity_data in entities_data:
                now = datetime.utcnow()
                entity = Entity(
                    id=self._generate_entity_id(entity_data["name"], document_id),
                    name=entity_data["name"],
                    type=entity_data.get("type", "Unknown"),
                    description=entity_data.get("description", ""),
                    properties=entity_data.get("properties", {}),
                    source_document_id=document_id,
                    document_id=document_id,
                    user_id=user_id,
                    confidence_score=1.0,
                    is_valid=True,
                    created_at=now,
                    updated_at=now
                )
                entities.append(entity)
            
            logger.info(f"从文档中提取到 {len(entities)} 个实体，行业: {industry}")
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {str(e)}")
            # 如果LLM调用失败，使用简单的回退方法
            return self._fallback_entity_extraction(content, document_id, user_id)
    
    async def extract_relations(self, content: str, entities: List[Entity], document_id: str, user_id: str, industry: str = "通用") -> List[Relation]:
        """从文本内容和实体列表中提取关系"""
        try:
            # 准备提示词
            prompt = self._prepare_relation_extraction_prompt(content, entities, industry)
            
            # 调用LLM
            response = await self._call_llm(prompt)
            
            # 解析响应
            relations_data = self._parse_relations_from_response(response)
            
            # 转换为Relation对象
            relations = []
            for relation_data in relations_data:
                # 查找源实体和目标实体
                source_entity = next(
                    (e for e in entities if e.name == relation_data["source"]),
                    None
                )
                target_entity = next(
                    (e for e in entities if e.name == relation_data["target"]),
                    None
                )
                
                if source_entity and target_entity:
                    now = datetime.utcnow()
                    relation = Relation(
                        id=self._generate_relation_id(source_entity.id, target_entity.id, relation_data["type"]),
                        type=relation_data["type"],
                        source_entity_id=source_entity.id,
                        target_entity_id=target_entity.id,
                        source_entity_name=source_entity.name,
                        target_entity_name=target_entity.name,
                        properties=relation_data.get("properties", {}),
                        description=relation_data.get("description", ""),
                        source_document_id=document_id,
                        document_id=document_id,
                        user_id=user_id,
                        confidence_score=1.0,
                        is_valid=True,
                        created_at=now,
                        updated_at=now
                    )
                    relations.append(relation)
            
            logger.info(f"从文档中提取到 {len(relations)} 个关系，行业: {industry}")
            return relations
            
        except Exception as e:
            logger.error(f"关系提取失败: {str(e)}")
            # 返回空列表作为回退
            return []
    
    async def enrich_entities(self, entities: List[Entity], industry: str = "通用") -> List[Entity]:
        """丰富实体信息"""
        try:
            if not entities:
                return entities
                
            # 批量处理实体，将所有实体合并为一次API调用，限制最多处理20个实体
            max_entities_to_enrich = 20
            entities_to_enrich = entities[:max_entities_to_enrich]
            enriched_entities = entities.copy()
            
            # 准备批量实体丰富提示词
            prompt = self._prepare_batch_entity_enrichment_prompt(entities_to_enrich, industry)
            response = await self._call_llm(prompt)
            
            # 解析批量响应
            enrichment_results = self._parse_batch_entity_enrichment(response, len(entities_to_enrich))
            
            # 更新实体信息
            for i, entity in enumerate(enriched_entities[:max_entities_to_enrich]):
                if i < len(enrichment_results):
                    enrichment_data = enrichment_results[i]
                    entity.type = enrichment_data.get("type", entity.type)
                    entity.description = enrichment_data.get("description", entity.description)
                    entity.properties = {**entity.properties, **enrichment_data.get("properties", {})}
            
            logger.info(f"实体丰富完成，共处理 {len(entities_to_enrich)} 个实体，行业: {industry}")
            return enriched_entities
            
        except Exception as e:
            logger.error(f"实体丰富失败: {str(e)}")
            # 返回原始实体列表
            return entities
    
    def _prepare_batch_entity_enrichment_prompt(self, entities: List[Entity], industry: str = "通用") -> str:
        """准备批量实体丰富提示词"""
        # 格式化实体列表
        entities_str = "\n".join([f"{i+1}. 名称: {entity.name}, 类型: {entity.type}, 描述: {entity.description}" for i, entity in enumerate(entities[:20])])  # 限制实体数量
        
        # 获取行业特定的提示词模板
        template = prompt_template_manager.get_template(industry, "batch_entity_enrichment")
        
        if not template:
            # 如果没有批量模板，使用默认模板
            template = """请为以下实体提供更详细的类型、描述和相关属性。每个实体的信息请使用JSON格式，包含type、description和properties字段。请返回一个JSON数组，顺序与输入实体列表一致。

实体列表：
{entities}

输出格式要求：
[
  {{"type": "实体类型", "description": "实体描述", "properties": {{"属性1": "值1", "属性2": "值2"}}}},
  {{"type": "实体类型", "description": "实体描述", "properties": {{"属性1": "值1", "属性2": "值2"}}}}
]
"""
        
        return template.format(
            entities=entities_str,
            industry=industry
        )
    
    def _parse_batch_entity_enrichment(self, response: str, expected_count: int) -> List[Dict]:
        """解析批量实体丰富响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                results = json.loads(json_str)
                return results[:expected_count]  # 确保返回数量与预期一致
            return []
        except Exception as e:
            logger.error(f"解析批量实体丰富响应失败: {str(e)}")
            return []
    
    async def validate_extractions(self, entities: List[Entity], relations: List[Relation]) -> Tuple[List[Entity], List[Relation], List[Dict]]:
        """验证提取的实体和关系的有效性"""
        validation_errors = []
        valid_entities = []
        valid_relations = []
        
        # 验证实体
        entity_names = set()
        for entity in entities:
            errors = []
            
            # 检查名称
            if not entity.name or not entity.name.strip():
                errors.append("实体名称不能为空")
            elif len(entity.name.strip()) < 2:
                errors.append("实体名称太短")
            elif entity.name in entity_names:
                errors.append("实体名称重复")
            
            # 检查类型
            if not entity.type or entity.type == "Unknown":
                errors.append("实体类型未知")
            
            if errors:
                validation_errors.append({
                    "type": "entity",
                    "id": entity.id,
                    "name": entity.name,
                    "errors": errors
                })
            else:
                valid_entities.append(entity)
                entity_names.add(entity.name)
        
        # 验证关系
        for relation in relations:
            errors = []
            
            # 检查关系类型
            if not relation.type or not relation.type.strip():
                errors.append("关系类型不能为空")
            
            # 检查实体引用
            source_exists = any(e.id == relation.source_entity_id for e in valid_entities)
            target_exists = any(e.id == relation.target_entity_id for e in valid_entities)
            
            if not source_exists:
                errors.append("源实体不存在")
            if not target_exists:
                errors.append("目标实体不存在")
            
            if errors:
                validation_errors.append({
                    "type": "relation",
                    "id": relation.id,
                    "source": relation.source_entity_name,
                    "target": relation.target_entity_name,
                    "relation_type": relation.type,
                    "errors": errors
                })
            else:
                valid_relations.append(relation)
        
        logger.info(f"验证结果 - 有效实体: {len(valid_entities)}, 有效关系: {len(valid_relations)}, 错误数: {len(validation_errors)}")
        return valid_entities, valid_relations, validation_errors
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM服务"""
        try:
            # 使用LLMService调用Kimi API
            response = await llm_service.generate_text(
                prompt=prompt,
                system_message="你是一个专业的知识图谱构建助手。请严格按照要求的格式输出JSON。",
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise
    
    def _prepare_entity_extraction_prompt(self, content: str, industry: str = "通用") -> str:
        """准备实体提取提示词"""
        # 行业特定实体类型映射
        industry_entity_types = {
            "金融": [
                "股票（Stock）",
                "债券（Bond）",
                "基金（Fund）",
                "期货（Futures）",
                "期权（Option）",
                "汇率（ExchangeRate）",
                "利率（InterestRate）",
                "金融机构（FinancialInstitution）",
                "金融产品（FinancialProduct）",
                "金融指标（FinancialIndicator）"
            ],
            "医疗": [
                "疾病（Disease）",
                "症状（Symptom）",
                "药物（Drug）",
                "治疗方法（Treatment）",
                "医疗器械（MedicalDevice）",
                "医疗机构（MedicalInstitution）",
                "医疗术语（MedicalTerm）",
                "基因（Gene）",
                "蛋白质（Protein）"
            ],
            "法律": [
                "法律条款（LegalClause）",
                "案例（Case）",
                "法规（Regulation）",
                "法律程序（LegalProcedure）",
                "法律主体（LegalSubject）",
                "法律责任（LegalLiability）"
            ],
            "技术": [
                "编程语言（ProgrammingLanguage）",
                "框架（Framework）",
                "库（Library）",
                "算法（Algorithm）",
                "数据结构（DataStructure）",
                "硬件设备（HardwareDevice）",
                "软件系统（SoftwareSystem）",
                "API接口（APIInterface）",
                "协议（Protocol）",
                "技术标准（TechnicalStandard）"
            ],
            "教育": [
                "课程（Course）",
                "学位（Degree）",
                "教育机构（EducationalInstitution）",
                "教育资源（EducationalResource）",
                "教育方法（EducationalMethod）"
            ],
            "电商": [
                "商品（Commodity）",
                "品牌（Brand）",
                "店铺（Store）",
                "订单（Order）",
                "用户评价（UserReview）",
                "促销活动（PromotionActivity）"
            ]
        }
        
        # 基础实体类型
        base_entity_types = [
            "人物（Person）",
            "组织（Organization）",
            "地点（Location）",
            "事件（Event）",
            "概念（Concept）",
            "产品（Product）",
            "服务（Service）",
            "时间（Time）",
            "数值（Number）",
            "日期（Date）",
            "货币（Currency）",
            "计量单位（Unit）",
            "文档（Document）",
            "媒体（Media）",
            "奖项（Award）",
            "理论（Theory）",
            "学说（Doctrine）",
            "原则（Principle）"
        ]
        
        # 合并基础实体类型和行业特定实体类型
        all_entity_types = base_entity_types.copy()
        if industry in industry_entity_types:
            all_entity_types.extend(industry_entity_types[industry])
        
        entity_types_str = "\n-".join(all_entity_types)
        
        # 获取行业特定的提示词模板
        template = prompt_template_manager.get_template(industry, "entity_extraction")
        
        return template.format(
            entity_types=entity_types_str,
            content=content[:3000]
        )
    
    def _parse_entities_from_response(self, response: str) -> List[Dict]:
        """从LLM响应中解析实体"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析实体响应失败: {str(e)}")
            return []
    
    def _prepare_relation_extraction_prompt(self, content: str, entities: List[Entity], industry: str = "通用") -> str:
        """准备关系提取提示词"""
        entities_str = "\n".join([f"- {e.name} ({e.type})" for e in entities[:50]])  # 限制实体数量
        
        # 行业特定关系类型映射
        industry_relation_types = {
            "金融": [
                "持有关系（Holds）",
                "投资关系（InvestsIn）",
                "交易关系（TradesWith）",
                "关联关系（AssociatedWith）",
                "监管关系（Regulates）",
                "合作关系（PartnersWith）",
                "竞争关系（CompetesWith）",
                "收购关系（Acquires）",
                "合并关系（MergesWith）",
                "提供服务（ProvidesService）",
                "接受服务（ReceivesService）",
                "支付关系（Pays）",
                "收款关系（ReceivesPayment）",
                "担保关系（Guarantees）",
                "借贷关系（LendsTo）",
                "借款关系（BorrowsFrom）",
                "股权关系（OwnsSharesIn）",
                "控制关系（Controls）",
                "影响关系（Influences）",
                "依赖关系（DependsOn）"
            ],
            "医疗": [
                "诊断关系（Diagnoses）",
                "治疗关系（Treats）",
                "导致关系（Causes）",
                "症状关系（HasSymptom）",
                "并发症关系（Complicates）",
                "预防关系（Prevents）",
                "副作用关系（HasSideEffect）",
                "适应症关系（IndicatedFor）",
                "禁忌症关系（ContraindicatedFor）",
                "相互作用关系（InteractsWith）",
                "组成关系（ConsistsOf）",
                "属于关系（BelongsTo）",
                "关联关系（AssociatedWith）",
                "影响关系（Affects）",
                "检测关系（Detects）"
            ],
            "法律": [
                "适用关系（AppliesTo）",
                "违反关系（Violates）",
                "遵循关系（CompliesWith）",
                "引用关系（Cites）",
                "修订关系（Amends）",
                "废止关系（Repeals）",
                "包含关系（Contains）",
                "属于关系（BelongsTo）",
                "关联关系（AssociatedWith）",
                "授权关系（Authorizes）",
                "禁止关系（Prohibits）",
                "允许关系（Permits）",
                "规定关系（Specifies）",
                "解释关系（Interprets）",
                "管辖关系（JurisdictionOver）"
            ],
            "技术": [
                "依赖关系（DependsOn）",
                "实现关系（Implements）",
                "使用关系（Uses）",
                "基于关系（BasedOn）",
                "扩展关系（Extends）",
                "继承关系（InheritsFrom）",
                "调用关系（Calls）",
                "返回关系（Returns）",
                "参数关系（TakesParameter）",
                "产生关系（Produces）",
                "消耗关系（Consumes）",
                "连接关系（ConnectsTo）",
                "通信关系（CommunicatesWith）",
                "包含关系（Contains）",
                "属于关系（BelongsTo）",
                "关联关系（AssociatedWith）",
                "影响关系（Affects）"
            ],
            "教育": [
                "教授关系（Teaches）",
                "学习关系（Learns）",
                "包含关系（Contains）",
                "属于关系（BelongsTo）",
                "关联关系（AssociatedWith）",
                "前置关系（PrerequisiteFor）",
                "后续关系（Follows）",
                "评估关系（Assesses）",
                "授予关系（Grants）",
                "参与关系（ParticipatesIn）",
                "提供关系（Provides）",
                "接受关系（Receives）",
                "指导关系（Advises）",
                "被指导关系（IsAdvisedBy）"
            ],
            "电商": [
                "销售关系（Sells）",
                "购买关系（Buys）",
                "评价关系（Reviews）",
                "评分关系（Rates）",
                "包含关系（Contains）",
                "属于关系（BelongsTo）",
                "关联关系（AssociatedWith）",
                "推荐关系（Recommends）",
                "搜索关系（SearchesFor）",
                "浏览关系（Views）",
                "添加购物车关系（AddsToCart）",
                "移除购物车关系（RemovesFromCart）",
                "下单关系（PlacesOrder）",
                "支付关系（PaysFor）",
                "配送关系（DeliversTo）",
                "收货关系（Receives）",
                "退货关系（Returns）",
                "退款关系（Refunds）",
                "投诉关系（ComplainsAbout）",
                "解决关系（Resolves）"
            ]
        }
        
        # 基础关系类型
        base_relation_types = [
            "包含关系（Contains）",
            "属于关系（BelongsTo）",
            "关联关系（AssociatedWith）",
            "因果关系（Causes）",
            "时间关系（OccursAt）",
            "创建关系（CreatedBy）",
            "拥有关系（Has）",
            "位置关系（LocatedAt）",
            "相似关系（SimilarTo）",
            "层次关系（PartOf）",
            "使用关系（Uses）",
            "产生关系（Produces）",
            "消耗关系（Consumes）",
            "影响关系（Affects）",
            "依赖关系（DependsOn）",
            "合作关系（PartnersWith）",
            "竞争关系（CompetesWith）",
            "继承关系（InheritsFrom）",
            "扩展关系（Extends）",
            "实现关系（Implements）"
        ]
        
        # 合并基础关系类型和行业特定关系类型
        all_relation_types = base_relation_types.copy()
        if industry in industry_relation_types:
            all_relation_types.extend(industry_relation_types[industry])
        
        relation_types_str = "\n-".join(all_relation_types)
        
        # 获取行业特定的提示词模板
        template = prompt_template_manager.get_template(industry, "relation_extraction")
        
        return template.format(
            entities=entities_str,
            content=content[:3000],
            relation_types=relation_types_str
        )
    
    def _parse_relations_from_response(self, response: str) -> List[Dict]:
        """从LLM响应中解析关系"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析关系响应失败: {str(e)}")
            return []
    
    def _prepare_entity_enrichment_prompt(self, entity: Entity, industry: str = "通用") -> str:
        """准备实体丰富提示词"""
        # 行业和实体类型特定的属性建议
        industry_entity_properties = {
            "金融": {
                "股票": ["股票代码", "上市交易所", "当前价格", "市值", "市盈率", "市净率", "股息率", "所属行业", "主要业务"],
                "债券": ["债券代码", "发行机构", "发行日期", "到期日期", "票面利率", "信用评级", "面值"],
                "基金": ["基金代码", "基金类型", "基金经理", "成立日期", "规模", "收益率", "投资策略"],
                "金融机构": ["成立时间", "总部地点", "注册资本", "业务范围", "监管机构", "主要股东", "资产规模"],
                "金融产品": ["产品名称", "发行机构", "风险等级", "预期收益", "投资期限", "起购金额"]
            },
            "医疗": {
                "疾病": ["病因", "症状", "诊断方法", "治疗方案", "预防措施", "发病率", "死亡率", "易感人群"],
                "药物": ["通用名", "商品名", "适应症", "禁忌症", "副作用", "用法用量", "生产厂商", "批准文号"],
                "症状": ["表现形式", "持续时间", "严重程度", "可能病因", "相关疾病"],
                "医疗器械": ["类型", "功能", "适用范围", "使用方法", "生产厂商", "注册证号"],
                "医疗机构": ["成立时间", "等级", "科室设置", "特色专科", "医护人员数量", "设备情况"]
            },
            "法律": {
                "法律条款": ["所属法规", "生效时间", "条款内容", "适用范围", "修订历史"],
                "案例": ["案号", "审理法院", "判决日期", "当事人", "争议焦点", "判决结果", "法律依据"],
                "法规": ["发布机关", "发布日期", "生效日期", "适用范围", "主要内容", "修订情况"],
                "法律程序": ["程序名称", "适用条件", "流程步骤", "时限要求", "法律后果"]
            },
            "技术": {
                "编程语言": ["设计人", "首次发布", "最新版本", "主要用途", "语法特点", "生态系统", "优缺点"],
                "框架": ["开发语言", "发布时间", "最新版本", "主要用途", "核心功能", "社区活跃度", "优缺点"],
                "算法": ["发明者", "发明时间", "算法类型", "时间复杂度", "空间复杂度", "应用场景", "优缺点"],
                "软件系统": ["开发公司", "发布时间", "最新版本", "主要功能", "技术架构", "用户规模", "收费模式"],
                "API接口": ["所属平台", "功能描述", "请求方式", "参数说明", "返回格式", "认证方式", "调用限制"]
            },
            "教育": {
                "课程": ["课程代码", "学分", "学时", "授课教师", "教学目标", "教学内容", "考核方式", "适用专业"],
                "教育机构": ["成立时间", "类型", "等级", "办学规模", "专业设置", "师资力量", "科研成果"],
                "学位": ["学位类型", "授予条件", "学习年限", "课程设置", "论文要求", "就业方向"],
                "教育资源": ["资源类型", "作者", "出版时间", "适用对象", "内容简介", "获取方式"]
            },
            "电商": {
                "商品": ["商品ID", "品牌", "类别", "价格", "库存", "销量", "评分", "评价数量", "规格参数", "产地", "保质期"],
                "品牌": ["成立时间", "总部地点", "品牌定位", "主要产品", "市场份额", "品牌价值"],
                "店铺": ["店铺ID", "店铺名称", "开店时间", "店铺等级", "评分", "主营类目", "服务承诺"],
                "订单": ["订单号", "下单时间", "订单状态", "商品信息", "订单金额", "支付方式", "配送信息"]
            }
        }
        
        # 基础实体类型的属性建议
        base_entity_properties = {
            "人物": ["出生日期", "国籍", "职业", "成就", "教育背景", "工作经历", "代表作品", "社会关系"],
            "组织": ["成立时间", "总部地点", "创始人", "业务范围", "规模", "组织结构", "主要产品", "市场地位"],
            "地点": ["地理位置", "人口", "面积", "历史背景", "经济发展", "文化特色", "旅游资源", "交通状况"],
            "事件": ["发生时间", "地点", "参与者", "原因", "经过", "结果", "影响", "历史意义"],
            "概念": ["定义", "起源", "发展历程", "核心思想", "应用领域", "相关理论", "争议点"],
            "产品": ["发布时间", "价格", "功能", "制造商", "规格参数", "技术指标", "市场评价", "竞品对比"],
            "服务": ["服务内容", "服务对象", "服务流程", "收费标准", "服务质量", "客户评价"]
        }
        
        # 获取适合当前实体的属性建议
        properties_suggestions = []
        
        # 首先检查行业特定的属性建议
        if industry in industry_entity_properties:
            industry_props = industry_entity_properties[industry]
            # 检查实体类型是否在行业特定属性中
            for entity_type, props in industry_props.items():
                if entity_type in entity.type or entity.type in entity_type:
                    properties_suggestions.extend(props)
                    break
            # 如果没有找到匹配的实体类型，使用行业通用属性
            if not properties_suggestions and "通用" in industry_props:
                properties_suggestions.extend(industry_props["通用"])
        
        # 如果行业特定属性为空，使用基础实体类型属性
        if not properties_suggestions:
            for base_type, props in base_entity_properties.items():
                if base_type in entity.type or entity.type in base_type:
                    properties_suggestions.extend(props)
                    break
            # 如果没有找到匹配的基础类型，使用通用属性
            if not properties_suggestions:
                properties_suggestions = ["描述", "分类", "相关实体", "重要性", "应用场景"]
        
        # 去重并格式化属性建议
        properties_suggestions = list(set(properties_suggestions))
        properties_str = ", ".join(properties_suggestions)
        
        # 获取行业特定的提示词模板
        template = prompt_template_manager.get_template(industry, "entity_enrichment")
        
        return template.format(
            entity_name=entity.name,
            entity_type=entity.type,
            entity_description=entity.description,
            industry=industry,
            properties_suggestions=properties_str
        )
    
    def _parse_entity_enrichment(self, response: str) -> Dict:
        """解析实体丰富响应"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return json.loads(response)
        except Exception as e:
            logger.error(f"解析实体丰富响应失败: {str(e)}")
            return {}
    
    def _fallback_entity_extraction(self, content: str, document_id: str, user_id: str) -> List[Entity]:
        """简单的回退实体提取方法"""
        # 这是一个简单的基于规则的回退方法
        # 在实际应用中可以实现更复杂的规则
        entities = []
        
        # 提取可能的人名（简单规则）
        person_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
        for match in re.finditer(person_pattern, content):
            name = match.group(1)
            entity = Entity(
                id=self._generate_entity_id(name, document_id),
                name=name,
                type="Person",
                description="",
                document_id=document_id,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            entities.append(entity)
        
        # 提取可能的组织名（简单规则）
        org_pattern = r'(公司|组织|机构|协会|集团|大学|学院)'
        for match in re.finditer(org_pattern, content):
            name = match.group(0)
            entity = Entity(
                id=self._generate_entity_id(name, document_id),
                name=name,
                type="Organization",
                description="",
                document_id=document_id,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            entities.append(entity)
        
        return entities
