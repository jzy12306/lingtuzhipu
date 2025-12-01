import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
        
        # 初始化调度器
        self.scheduler = AsyncIOScheduler()
        self.audit_jobs = {}  # 存储审计任务
        self.audit_history = []  # 存储审计历史
    
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
            
            # 6. 关系完整性检查
            integrity_conflicts = await self._check_relation_integrity(document_id)
            conflicts.extend(integrity_conflicts)
            
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
                
                # 检查实体属性完整性
                if not entity.properties or len(entity.properties) == 0:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="empty_entity_properties",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 没有属性",
                        severity="medium",
                        suggested_resolution="添加实体属性"
                    )
                    conflicts.append(conflict)
                
                # 检查实体创建时间
                if not entity.created_at:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="missing_created_at",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 缺少创建时间",
                        severity="high",
                        suggested_resolution="添加创建时间"
                    )
                    conflicts.append(conflict)
                
                # 检查实体更新时间
                if not entity.updated_at:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="missing_updated_at",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 缺少更新时间",
                        severity="high",
                        suggested_resolution="添加更新时间"
                    )
                    conflicts.append(conflict)
                
                # 检查实体来源文档
                if not entity.source_document_id:
                    conflict = KnowledgeConflict(
                        conflict_id=str(entity.id),
                        type="missing_source_document",
                        entities=[entity],
                        relations=[],
                        description=f"实体ID {entity.id} 缺少来源文档ID",
                        severity="medium",
                        suggested_resolution="添加来源文档ID"
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
                
                # 检查关系置信度
                if relation.confidence_score < 0.5:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="low_confidence_relation",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 置信度分数过低: {relation.confidence_score}",
                        severity="medium",
                        suggested_resolution="重新评估关系或提高置信度分数"
                    )
                    conflicts.append(conflict)
                
                # 检查关系创建时间
                if not relation.created_at:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="missing_relation_created_at",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 缺少创建时间",
                        severity="high",
                        suggested_resolution="添加创建时间"
                    )
                    conflicts.append(conflict)
                
                # 检查关系更新时间
                if not relation.updated_at:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="missing_relation_updated_at",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 缺少更新时间",
                        severity="high",
                        suggested_resolution="添加更新时间"
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
    
    async def _check_relation_integrity(self, document_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """检查关系完整性"""
        try:
            self.logger.info("开始检查关系完整性")
            conflicts = []
            
            # 获取关系列表
            relations = await self._get_relations(document_id)
            
            # 检查关系的唯一性：避免重复关系
            relation_set = set()
            for relation in relations:
                # 构建关系的唯一标识：源实体ID + 关系类型 + 目标实体ID
                relation_key = f"{relation.source_entity_id}_{relation.type}_{relation.target_entity_id}"
                if relation_key in relation_set:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="duplicate_relation",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 是重复关系: {relation_key}",
                        severity="medium",
                        suggested_resolution="删除重复关系或修改关系类型"
                    )
                    conflicts.append(conflict)
                else:
                    relation_set.add(relation_key)
            
            # 检查关系的方向性：避免循环依赖
            for relation in relations:
                if relation.source_entity_id == relation.target_entity_id:
                    conflict = KnowledgeConflict(
                        conflict_id=str(relation.id),
                        type="self_relation",
                        entities=[],
                        relations=[relation],
                        description=f"关系ID {relation.id} 是自引用关系",
                        severity="medium",
                        suggested_resolution="修正关系的源实体或目标实体"
                    )
                    conflicts.append(conflict)
            
            self.logger.info(f"关系完整性检查完成，发现 {len(conflicts)} 个冲突")
            return conflicts
        except Exception as e:
            self.logger.error(f"检查关系完整性失败: {str(e)}")
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
                    await self.knowledge_repository.update_entity(entity.id, {"name": entity.name})
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
                    await self.knowledge_repository.update_entity(entity.id, {"type": entity.type})
                    self.logger.info(f"自动修正实体类型: {entity.id} -> {entity.type}")
                    conflict.description = f"实体ID {entity.id} 类型已自动修正为: {entity.type}"
                    return conflict
            
            elif conflict.type == "low_confidence_entity":
                # 尝试使用LLM增强实体信息，提高置信度
                prompt = f"请增强以下实体的信息，提高其置信度: 名称: {entity.name}, 类型: {entity.type}, 属性: {entity.properties}"
                response = await llm_service.generate(prompt)
                if response and response.strip():
                    # 更新实体置信度
                    await self.knowledge_repository.update_entity(entity.id, {"confidence_score": 0.7})
                    self.logger.info(f"自动提高实体置信度: {entity.id} -> 0.7")
                    conflict.description = f"实体ID {entity.id} 置信度已自动提高到0.7"
                    return conflict
            
            elif conflict.type == "missing_created_at" or conflict.type == "missing_updated_at":
                # 自动添加时间戳
                now = datetime.now()
                update_data = {}
                if conflict.type == "missing_created_at":
                    update_data["created_at"] = now
                if conflict.type == "missing_updated_at":
                    update_data["updated_at"] = now
                
                await self.knowledge_repository.update_entity(entity.id, update_data)
                self.logger.info(f"自动修正实体时间戳: {entity.id}")
                conflict.description = f"实体ID {entity.id} 时间戳已自动添加"
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
                await self.knowledge_repository.update_relation(relation.id, {"is_valid": False})
                self.logger.info(f"自动修正关系: {relation.id} -> 标记为无效")
                conflict.description = f"关系ID {relation.id} 已自动标记为无效"
                return conflict
            
            elif conflict.type == "low_confidence_relation":
                # 自动提高关系置信度
                await self.knowledge_repository.update_relation(relation.id, {"confidence_score": 0.7})
                self.logger.info(f"自动提高关系置信度: {relation.id} -> 0.7")
                conflict.description = f"关系ID {relation.id} 置信度已自动提高到0.7"
                return conflict
            
            elif conflict.type == "empty_relation_type":
                # 尝试使用LLM生成关系类型
                source_entity = await self.knowledge_repository.find_entity_by_id(relation.source_entity_id)
                target_entity = await self.knowledge_repository.find_entity_by_id(relation.target_entity_id)
                
                if source_entity and target_entity:
                    prompt = f"请为以下关系生成一个合适的关系类型: 源实体: {source_entity.name} ({source_entity.type}), 目标实体: {target_entity.name} ({target_entity.type})"
                    response = await llm_service.generate(prompt)
                    if response and response.strip():
                        relation.type = response.strip()
                        await self.knowledge_repository.update_relation(relation.id, {"type": relation.type})
                        self.logger.info(f"自动修正关系类型: {relation.id} -> {relation.type}")
                        conflict.description = f"关系ID {relation.id} 类型已自动修正为: {relation.type}"
                        return conflict
            
            elif conflict.type == "duplicate_relation":
                # 删除重复关系
                await self.knowledge_repository.delete_relation(relation.id)
                self.logger.info(f"自动删除重复关系: {relation.id}")
                conflict.description = f"关系ID {relation.id} 已自动删除（重复关系）"
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
                await self.knowledge_repository.update_relation(relation.id, {"type": relation.type})
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
            
            # 计算知识图谱质量评分
            total_possible_points = len(conflicts) * 100
            if total_possible_points == 0:
                quality_score = 100
            else:
                # 根据严重程度计算扣分
                severity_weights = {
                    "high": 50,
                    "medium": 25,
                    "low": 10
                }
                total_deduction = 0
                for conflict in conflicts:
                    total_deduction += severity_weights.get(conflict.severity, 25)
                
                quality_score = max(0, 100 - (total_deduction / total_possible_points * 100))
            
            # 按严重程度分组冲突
            conflicts_by_severity = {}
            for conflict in conflicts:
                if conflict.severity not in conflicts_by_severity:
                    conflicts_by_severity[conflict.severity] = []
                conflicts_by_severity[conflict.severity].append({
                    "id": conflict.conflict_id,
                    "type": conflict.type,
                    "description": conflict.description,
                    "suggested_resolution": conflict.suggested_resolution,
                    "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in conflict.entities],
                    "relations": [{"id": r.id, "type": r.type} for r in conflict.relations]
                })
            
            # 生成报告
            report = {
                "audit_id": f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "audit_time": datetime.now().isoformat(),
                "total_conflicts": len(conflicts),
                "quality_score": round(quality_score, 2),
                "quality_level": "优秀" if quality_score >= 90 else "良好" if quality_score >= 70 else "中等" if quality_score >= 50 else "较差",
                "conflict_types": conflict_types,
                "severity_counts": severity_counts,
                "conflicts_by_severity": conflicts_by_severity,
                "conflicts": [{
                    "id": conflict.conflict_id,
                    "type": conflict.type,
                    "description": conflict.description,
                    "severity": conflict.severity,
                    "suggested_resolution": conflict.suggested_resolution,
                    "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in conflict.entities],
                    "relations": [{"id": r.id, "type": r.type} for r in conflict.relations]
                } for conflict in conflicts],
                "summary": {
                    "total_conflicts": len(conflicts),
                    "high_severity": severity_counts.get("high", 0),
                    "medium_severity": severity_counts.get("medium", 0),
                    "low_severity": severity_counts.get("low", 0),
                    "quality_score": round(quality_score, 2),
                    "quality_level": "优秀" if quality_score >= 90 else "良好" if quality_score >= 70 else "中等" if quality_score >= 50 else "较差",
                    "suggested_actions": [
                        "优先处理高严重程度的冲突",
                        "定期进行审计以保持知识图谱质量",
                        "考虑使用自动修正功能处理低严重程度的冲突"
                    ]
                }
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
    
    async def initialize(self) -> bool:
        """初始化审计智能体"""
        try:
            self.logger.info(f"初始化审计智能体: {self.agent_name}")
            
            # 启动调度器
            self.scheduler.start()
            self.logger.info("审计调度器启动成功")
            
            return True
        except Exception as e:
            self.logger.error(f"审计智能体初始化失败: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """关闭审计智能体"""
        try:
            self.logger.info(f"关闭审计智能体: {self.agent_name}")
            
            # 关闭调度器
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.logger.info("审计调度器已关闭")
            
            return True
        except Exception as e:
            self.logger.error(f"关闭审计智能体失败: {str(e)}")
            return False
    
    async def schedule_audit(self, audit_type: str, trigger, description: str = "") -> str:
        """调度审计任务
        
        Args:
            audit_type: 审计类型 (real_time, daily, weekly, monthly, on_demand)
            trigger: 调度器触发器
            description: 审计任务描述
            
        Returns:
            str: 任务ID
        """
        try:
            # 定义审计任务
            async def audit_job():
                self.logger.info(f"执行{audit_type}审计任务: {description}")
                
                # 执行审计
                conflicts = await self.audit_knowledge_graph()
                report = await self.generate_audit_report(conflicts)
                
                # 保存审计历史
                audit_record = {
                    "id": f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "type": audit_type,
                    "description": description,
                    "timestamp": datetime.now(),
                    "conflicts_count": len(conflicts),
                    "report": report
                }
                self.audit_history.append(audit_record)
                
                # 只保留最近100条审计记录
                if len(self.audit_history) > 100:
                    self.audit_history = self.audit_history[-100:]
                
                self.logger.info(f"{audit_type}审计任务完成，发现{len(conflicts)}个冲突")
            
            # 添加任务到调度器
            job = self.scheduler.add_job(
                audit_job,
                trigger=trigger,
                id=f"{audit_type}_audit_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=f"{audit_type}_audit",
                replace_existing=False
            )
            
            # 保存任务信息
            self.audit_jobs[job.id] = {
                "job_id": job.id,
                "type": audit_type,
                "description": description,
                "trigger": str(trigger),
                "next_run_time": job.next_run_time
            }
            
            self.logger.info(f"审计任务已调度，ID: {job.id}")
            return job.id
        except Exception as e:
            self.logger.error(f"调度审计任务失败: {str(e)}")
            raise
    
    async def trigger_audit(self, audit_type: str = "on_demand", description: str = "按需审计") -> Dict[str, Any]:
        """触发审计任务
        
        Args:
            audit_type: 审计类型
            description: 审计描述
            
        Returns:
            Dict[str, Any]: 审计结果
        """
        try:
            self.logger.info(f"触发{audit_type}审计: {description}")
            
            # 执行审计
            conflicts = await self.audit_knowledge_graph()
            report = await self.generate_audit_report(conflicts)
            
            # 保存审计历史
            audit_record = {
                "id": f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": audit_type,
                "description": description,
                "timestamp": datetime.now(),
                "conflicts_count": len(conflicts),
                "report": report
            }
            self.audit_history.append(audit_record)
            
            # 只保留最近100条审计记录
            if len(self.audit_history) > 100:
                self.audit_history = self.audit_history[-100:]
            
            result = {
                "audit_id": audit_record["id"],
                "conflicts_count": len(conflicts),
                "report": report
            }
            
            self.logger.info(f"{audit_type}审计完成，发现{len(conflicts)}个冲突")
            return result
        except Exception as e:
            self.logger.error(f"触发审计任务失败: {str(e)}")
            raise
    
    async def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取审计历史
        
        Args:
            limit: 返回的历史记录数量
            
        Returns:
            List[Dict[str, Any]]: 审计历史记录
        """
        try:
            # 返回最近的审计记录
            return self.audit_history[-limit:]
        except Exception as e:
            self.logger.error(f"获取审计历史失败: {str(e)}")
            raise
    
    async def get_audit_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取审计任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        try:
            return self.audit_jobs.get(job_id)
        except Exception as e:
            self.logger.error(f"获取审计任务失败: {str(e)}")
            raise
    
    async def list_audit_jobs(self) -> List[Dict[str, Any]]:
        """列出所有审计任务
        
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            return list(self.audit_jobs.values())
        except Exception as e:
            self.logger.error(f"列出审计任务失败: {str(e)}")
            raise
    
    async def remove_audit_job(self, job_id: str) -> bool:
        """移除审计任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            if job_id in self.audit_jobs:
                self.scheduler.remove_job(job_id)
                del self.audit_jobs[job_id]
                self.logger.info(f"审计任务已移除，ID: {job_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除审计任务失败: {str(e)}")
            raise
    
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
