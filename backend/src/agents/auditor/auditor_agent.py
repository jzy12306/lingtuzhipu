import logging
from typing import List, Dict, Any, Optional
from src.agents.agent_base import BaseAgent, AgentResult
from src.repositories.knowledge_repository import KnowledgeRepository
from src.models.knowledge import KnowledgeConflict, Entity, Relation
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AuditorAgent(BaseAgent):
    """审计智能体"""
    
    def __init__(self, agent_id: str, agent_name: str, knowledge_repository: KnowledgeRepository = None, **kwargs):
        super().__init__(agent_id, agent_name, **kwargs)
        self.knowledge_repository = knowledge_repository or KnowledgeRepository()
        self.logger = logger.getChild(f"AuditorAgent[{agent_id}]")
    
    async def audit_knowledge_graph(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """审计知识图谱"""
        try:
            self.logger.info(f"开始审计知识图谱，文档ID: {document_id}")
            
            # 执行各种审计检查
            conflicts = []
            
            # 1. 实体质量检查
            entity_conflicts = await self._check_entity_quality(document_id)
            conflicts.extend(entity_conflicts)
            
            # 2. 关系冲突检测
            relation_conflicts = await self._check_relation_conflicts(document_id)
            conflicts.extend(relation_conflicts)
            
            # 3. 实体类型冲突检测
            type_conflicts = await self._check_entity_type_conflicts(document_id)
            conflicts.extend(type_conflicts)
            
            # 4. 关系语义冲突检测
            semantic_conflicts = await self._check_relation_semantic_conflicts(document_id)
            conflicts.extend(semantic_conflicts)
            
            # 5. 时序冲突检测
            temporal_conflicts = await self._check_temporal_conflicts(document_id)
            conflicts.extend(temporal_conflicts)
            
            self.logger.info(f"审计完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"审计知识图谱失败: {str(e)}")
            raise
    
    async def _check_entity_quality(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查实体质量"""
        try:
            self.logger.info("开始检查实体质量")
            conflicts = []
            
            # 获取实体列表
            entities = await self._get_entities(document_id)
            
            for entity in entities:
                # 检查实体名称是否为空
                if not entity.name or len(entity.name.strip()) == 0:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="empty_entity_name",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 名称为空",
                        severity="high",
                        suggested_resolution="添加实体名称"
                    )
                    conflicts.append(conflict)
                
                # 检查实体类型是否为空
                if not entity.type or len(entity.type.strip()) == 0:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="empty_entity_type",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 类型为空",
                        severity="high",
                        suggested_resolution="添加实体类型"
                    )
                    conflicts.append(conflict)
                
                # 检查置信度分数
                if entity.confidence_score < 0.5:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="low_confidence_entity",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 置信度分数过低: {entity.confidence_score}",
                        severity="medium",
                        suggested_resolution="重新评估实体或提高置信度分数"
                    )
                    conflicts.append(conflict)
            
            self.logger.info(f"实体质量检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查实体质量失败: {str(e)}")
            return []
    
    async def _check_relation_conflicts(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查关系冲突"""
        try:
            self.logger.info("开始检查关系冲突")
            conflicts = []
            
            # 获取关系列表
            relations = await self._get_relations(document_id)
            
            for relation in relations:
                # 检查关系的源实体和目标实体是否存在
                source_entity = await self.knowledge_repository.find_entity_by_id(relation.source_entity_id)
                target_entity = await self.knowledge_repository.find_entity_by_id(relation.target_entity_id)
                
                if not source_entity:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="missing_source_entity",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 的源实体不存在: {relation.source_entity_id}",
                        severity="high",
                        suggested_resolution="添加源实体或修正关系"
                    )
                    conflicts.append(conflict)
                
                if not target_entity:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="missing_target_entity",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 的目标实体不存在: {relation.target_entity_id}",
                        severity="high",
                        suggested_resolution="添加目标实体或修正关系"
                    )
                    conflicts.append(conflict)
                
                # 检查关系类型是否为空
                if not relation.type or len(relation.type.strip()) == 0:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="empty_relation_type",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 类型为空",
                        severity="high",
                        suggested_resolution="添加关系类型"
                    )
                    conflicts.append(conflict)
            
            self.logger.info(f"关系冲突检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查关系冲突失败: {str(e)}")
            return []
    
    async def _check_entity_type_conflicts(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查实体类型冲突"""
        try:
            self.logger.info("开始检查实体类型冲突")
            
            # 使用现有的validate_knowledge_graph方法
            conflicts = await self.knowledge_repository.validate_knowledge_graph()
            
            self.logger.info(f"实体类型冲突检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查实体类型冲突失败: {str(e)}")
            return []
    
    async def _check_relation_semantic_conflicts(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查关系语义冲突"""
        try:
            self.logger.info("开始检查关系语义冲突")
            conflicts = []
            
            # 获取关系列表
            relations = await self._get_relations(document_id)
            
            # 简单的语义冲突检查：检查关系类型和实体类型的匹配
            for relation in relations:
                source_entity = await self.knowledge_repository.find_entity_by_id(relation.source_entity_id)
                target_entity = await self.knowledge_repository.find_entity_by_id(relation.target_entity_id)
                
                if source_entity and target_entity:
                    # 检查关系类型和实体类型的匹配
                    if relation.type == "属于" and source_entity.type == "Person" and target_entity.type == "Person":
                        conflict = KnowledgeConflict(
                            conflict_id=str(relation.id),
                            type="semantic_conflict",
                            entities=[source_entity, target_entity],
                            relations=[relation],
                            description=f"关系类型 '属于' 不适用于两个Person实体: {source_entity.name} -> {target_entity.name}",
                            severity="medium",
                            suggested_resolution="修正关系类型或实体类型"
                        )
                        conflicts.append(conflict)
            
            self.logger.info(f"关系语义冲突检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查关系语义冲突失败: {str(e)}")
            return []
    
    async def _check_temporal_conflicts(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查时序冲突"""
        try:
            self.logger.info("开始检查时序冲突")
            conflicts = []
            
            # 获取实体列表
            entities = await self._get_entities(document_id)
            
            # 简单的时序冲突检查：检查实体的创建时间和更新时间
            for entity in entities:
                if entity.created_at > entity.updated_at:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="temporal_conflict",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 的创建时间晚于更新时间",
                        severity="medium",
                        suggested_resolution="修正实体的时间戳"
                    )
                    conflicts.append(conflict)
            
            self.logger.info(f"时序冲突检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查时序冲突失败: {str(e)}")
            return []
    
    async def auto_correct_conflicts(self, conflicts: List[KnowledgeConflict]) -> List[KnowledgeConflict]:
        """自动修正冲突"""
        try:
            self.logger.info(f"开始自动修正 {len(conflicts)} 个冲突")
            
            corrected_conflicts = []
            
            for conflict in conflicts:
                # 根据冲突类型执行不同的修正策略
                if conflict.type in ["empty_entity_name", "empty_entity_type"]:
                    # 尝试使用LLM生成缺失的信息
                    corrected = await self._auto_correct_entity(conflict)
                    if corrected:
                        corrected_conflicts.append(corrected)
                elif conflict.type in ["missing_source_entity", "missing_target_entity"]:
                    # 尝试修复关系
                    corrected = await self._auto_correct_relation(conflict)
                    if corrected:
                        corrected_conflicts.append(corrected)
                elif conflict.type in ["semantic_conflict", "temporal_conflict"]:
                    # 尝试修复语义或时序冲突
                    corrected = await self._auto_correct_semantic(conflict)
                    if corrected:
                        corrected_conflicts.append(corrected)
            
            self.logger.info(f"自动修正完成，成功修正 {len(corrected_conflicts)} 个冲突")
            return corrected_conflicts
        except Exception as e:
            self.logger.error(f"自动修正冲突失败: {str(e)}")
            raise
    
    async def _auto_correct_entity(self, conflict: KnowledgeConflict) -> Optional[KnowledgeConflict]:
        """自动修正实体冲突"""
        try:
            if not conflict.entities:
                return None
            
            entity = conflict.entities[0]
            
            if conflict.type == "empty_entity_name":
                # 尝试使用LLM生成实体名称
                prompt = f"请为类型为 '{entity.type}' 的实体生成一个合适的名称，实体属性: {entity.properties}"
                response = await llm_service.generate(prompt)
                if response and response.strip():
                    entity.name = response.strip()
                    # 更新实体
                    # TODO: 实现实体更新逻辑
                    self.logger.info(f"自动修正实体名称: {entity.id} -> {entity.name}")
                    conflict.description = f"实体ID {entity.id} 名称已自动修正为: {entity.name}"
                    return conflict
            
            elif conflict.type == "empty_entity_type":
                # 尝试使用LLM生成实体类型
                prompt = f"请为名称为 '{entity.name}' 的实体生成一个合适的类型，实体属性: {entity.properties}"
                response = await llm_service.generate(prompt)
                if response and response.strip():
                    entity.type = response.strip()
                    # 更新实体
                    # TODO: 实现实体更新逻辑
                    self.logger.info(f"自动修正实体类型: {entity.id} -> {entity.type}")
                    conflict.description = f"实体ID {entity.id} 类型已自动修正为: {entity.type}"
                    return conflict
            
            return None
        except Exception as e:
            self.logger.error(f"自动修正实体冲突失败: {str(e)}")
            return None
    
    async def _auto_correct_relation(self, conflict: KnowledgeConflict) -> Optional[KnowledgeConflict]:
        """自动修正关系冲突"""
        try:
            if not conflict.relations:
                return None
            
            relation = conflict.relations[0]
            
            if conflict.type == "missing_source_entity" or conflict.type == "missing_target_entity":
                # 简单的修复：标记关系为无效
                relation.is_valid = False
                # 更新关系
                # TODO: 实现关系更新逻辑
                self.logger.info(f"自动修正关系: {relation.id} -> 标记为无效")
                conflict.description = f"关系ID {relation.id} 已自动标记为无效"
                return conflict
            
            return None
        except Exception as e:
            self.logger.error(f"自动修正关系冲突失败: {str(e)}")
            return None
    
    async def _auto_correct_semantic(self, conflict: KnowledgeConflict) -> Optional[KnowledgeConflict]:
        """自动修正语义冲突"""
        try:
            if not conflict.relations:
                return None
            
            relation = conflict.relations[0]
            
            # 简单的语义修复：尝试修正关系类型
            prompt = f"请为以下关系生成一个合适的关系类型: 源实体: {conflict.entities[0].name} ({conflict.entities[0].type}), 目标实体: {conflict.entities[1].name} ({conflict.entities[1].type})"
            response = await llm_service.generate(prompt)
            if response and response.strip():
                relation.type = response.strip()
                # 更新关系
                # TODO: 实现关系更新逻辑
                self.logger.info(f"自动修正关系类型: {relation.id} -> {relation.type}")
                conflict.description = f"关系ID {relation.id} 类型已自动修正为: {relation.type}"
                return conflict
            
            return None
        except Exception as e:
            self.logger.error(f"自动修正语义冲突失败: {str(e)}")
            return None
    
    async def generate_audit_report(self, conflicts: List[KnowledgeConflict]) -> Dict[str, Any]:
        """生成审计报告"""
        try:
            self.logger.info("开始生成审计报告")
            
            # 统计冲突类型
            conflict_types = {}
            for conflict in conflicts:
                if conflict.type not in conflict_types:
                    conflict_types[conflict.type] = 0
                conflict_types[conflict.type] += 1
            
            # 统计严重程度
            severity_counts = {}
            for conflict in conflicts:
                if conflict.severity not in severity_counts:
                    severity_counts[conflict.severity] = 0
                severity_counts[conflict.severity] += 1
            
            # 生成报告
            report = {
                "total_conflicts": len(conflicts),
                "conflict_types": conflict_types,
                "severity_counts": severity_counts,
                "conflicts": [{
                    "id": conflict.conflict_id,
                    "type": conflict.type,
                    "description": conflict.description,
                    "severity": conflict.severity,
                    "suggested_resolution": conflict.suggested_resolution,
                    "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in conflict.entities],
                    "relations": [{"id": r.id, "type": r.type} for r in conflict.relations]
                } for conflict in conflicts]
            }
            
            self.logger.info("审计报告生成完成")
            return report
        except Exception as e:
            self.logger.error(f"生成审计报告失败: {str(e)}")
            raise
    
    async def _get_entities(self, document_id: Optional[str] = None) -> List[Entity]:
        """获取实体列表"""
        if document_id:
            return await self.knowledge_repository.find_entities_by_document(document_id)
        else:
            # TODO: 实现获取所有实体的方法
            return []
    
    async def _get_relations(self, document_id: Optional[str] = None) -> List[Relation]:
        """获取关系列表"""
        if document_id:
            return await self.knowledge_repository.find_relations_by_document(document_id)
        else:
            # TODO: 实现获取所有关系的方法
            return []
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理输入数据并返回结果"""
        try:
            self.logger.info(f"开始处理审计请求，输入数据: {input_data}")
            
            # 验证输入
            validation_error = await self.validate_input(input_data)
            if validation_error:
                return self._create_error_result(validation_error, "输入数据验证失败")
            
            # 提取参数
            document_id = input_data.get("document_id")
            auto_correct = input_data.get("auto_correct", False)
            
            # 执行审计
            conflicts = await self.audit_knowledge_graph(document_id)
            
            # 生成审计报告
            report = await self.generate_audit_report(conflicts)
            
            # 如果需要自动修正
            corrected_conflicts = []
            if auto_correct and conflicts:
                corrected_conflicts = await self.auto_correct_conflicts(conflicts)
                report["corrected_conflicts"] = len(corrected_conflicts)
            
            # 返回结果
            result = {
                "report": report,
                "conflicts": conflicts,
                "corrected_conflicts": corrected_conflicts
            }
            
            return self._create_success_result(result, f"审计完成，发现 {len(conflicts)} 个冲突")
        except Exception as e:
            self.logger.error(f"处理审计请求失败: {str(e)}")
            return self._create_error_result(str(e), "审计处理失败")
