"""知识图谱质量评估模块"""

import logging
from typing import List, Dict, Any, Tuple
from src.models.knowledge import Entity, Relation

logger = logging.getLogger(__name__)


class KnowledgeGraphQualityEvaluator:
    """知识图谱质量评估器"""
    
    def __init__(self):
        self._metrics = {
            "entity_completeness": 0.0,
            "entity_accuracy": 0.0,
            "entity_consistency": 0.0,
            "relation_completeness": 0.0,
            "relation_accuracy": 0.0,
            "relation_consistency": 0.0,
            "property_completeness": 0.0,
            "property_accuracy": 0.0,
            "property_consistency": 0.0,
            "overall_quality": 0.0
        }
    
    def evaluate_entities(self, entities: List[Entity]) -> Dict[str, Any]:
        """评估实体质量"""
        if not entities:
            return {
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "errors": ["没有实体可评估"]
            }
        
        total_entities = len(entities)
        complete_entities = 0
        accurate_entities = 0
        consistent_entities = 0
        errors = []
        
        # 实体名称集合，用于检查一致性
        entity_names = set()
        
        for entity in entities:
            entity_errors = []
            
            # 评估完整性
            is_complete = True
            if not entity.name or not entity.name.strip():
                entity_errors.append(f"实体ID {entity.id} 缺少名称")
                is_complete = False
            if entity.type == "Unknown":
                entity_errors.append(f"实体 {entity.name} 类型未知")
                is_complete = False
            # 检查description属性是否存在
            if hasattr(entity, 'description') and not entity.description or not entity.description.strip():
                entity_errors.append(f"实体 {entity.name} 缺少描述")
                # 描述缺失不影响完整性评分，但会记录警告
            
            if is_complete:
                complete_entities += 1
            
            # 评估准确性
            is_accurate = True
            if len(entity.name.strip()) < 2:
                entity_errors.append(f"实体 {entity.name} 名称过短")
                is_accurate = False
            
            if is_accurate:
                accurate_entities += 1
            
            # 评估一致性
            is_consistent = True
            if entity.name in entity_names:
                entity_errors.append(f"实体 {entity.name} 名称重复")
                is_consistent = False
            else:
                entity_names.add(entity.name)
            
            if is_consistent:
                consistent_entities += 1
            
            if entity_errors:
                errors.extend(entity_errors)
        
        # 计算评分
        completeness = complete_entities / total_entities
        accuracy = accurate_entities / total_entities
        consistency = consistent_entities / total_entities
        
        return {
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "total_entities": total_entities,
            "complete_entities": complete_entities,
            "accurate_entities": accurate_entities,
            "consistent_entities": consistent_entities,
            "errors": errors
        }
    
    def evaluate_relations(self, relations: List[Relation], entities: List[Entity]) -> Dict[str, Any]:
        """评估关系质量"""
        if not relations:
            return {
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "total_relations": 0,
                "complete_relations": 0,
                "accurate_relations": 0,
                "consistent_relations": 0,
                "relation_type_count": 0,
                "errors": ["没有关系可评估"]
            }
        
        total_relations = len(relations)
        complete_relations = 0
        accurate_relations = 0
        consistent_relations = 0
        errors = []
        
        # 实体ID集合，用于检查关系的源实体和目标实体是否存在
        entity_ids = {entity.id for entity in entities}
        
        # 关系类型集合，用于统计关系类型分布
        relation_types = {}
        
        for relation in relations:
            relation_errors = []
            
            # 评估完整性
            is_complete = True
            if not relation.type or not relation.type.strip():
                relation_errors.append(f"关系ID {relation.id} 缺少类型")
                is_complete = False
            if not relation.source_entity_id:
                relation_errors.append(f"关系ID {relation.id} 缺少源实体ID")
                is_complete = False
            if not relation.target_entity_id:
                relation_errors.append(f"关系ID {relation.id} 缺少目标实体ID")
                is_complete = False
            # 移除对不存在属性的检查，实体名称不是关系模型的必填字段
            
            if is_complete:
                complete_relations += 1
            
            # 评估准确性
            is_accurate = True
            if relation.source_entity_id not in entity_ids:
                relation_errors.append(f"关系 {relation.id} 的源实体 {relation.source_entity_id} 不存在")
                is_accurate = False
            if relation.target_entity_id not in entity_ids:
                relation_errors.append(f"关系 {relation.id} 的目标实体 {relation.target_entity_id} 不存在")
                is_accurate = False
            
            if is_accurate:
                accurate_relations += 1
            
            # 评估一致性
            is_consistent = True
            relation_key = f"{relation.source_entity_id}_{relation.target_entity_id}_{relation.type}"
            if relation_key in relation_types:
                relation_errors.append(f"关系 {relation.source_entity_id} - {relation.type} - {relation.target_entity_id} 重复")
                is_consistent = False
            else:
                relation_types[relation_key] = 1
            
            if is_consistent:
                consistent_relations += 1
            
            if relation_errors:
                errors.extend(relation_errors)
        
        # 计算评分，添加除数检查
        completeness = complete_relations / total_relations if total_relations > 0 else 0.0
        accuracy = accurate_relations / total_relations if total_relations > 0 else 0.0
        consistency = consistent_relations / total_relations if total_relations > 0 else 0.0
        
        return {
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "total_relations": total_relations,
            "complete_relations": complete_relations,
            "accurate_relations": accurate_relations,
            "consistent_relations": consistent_relations,
            "relation_type_count": len(relation_types),
            "errors": errors
        }
    
    def evaluate_properties(self, entities: List[Entity]) -> Dict[str, Any]:
        """评估属性质量"""
        if not entities:
            return {
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "errors": ["没有实体可评估属性"]
            }
        
        total_properties = 0
        complete_properties = 0
        accurate_properties = 0
        consistent_properties = 0
        errors = []
        
        # 统计不同实体类型的属性数量，用于检查一致性
        type_property_counts = {}
        
        for entity in entities:
            # 初始化实体类型的属性计数
            if entity.type not in type_property_counts:
                type_property_counts[entity.type] = {
                    "total_entities": 0,
                    "property_count": 0,
                    "properties": {}
                }
            
            type_property_counts[entity.type]["total_entities"] += 1
            
            # 评估实体的属性
            if hasattr(entity, 'properties') and entity.properties:
                entity_properties = entity.properties
                total_properties += len(entity_properties)
                
                for prop_name, prop_value in entity_properties.items():
                    # 评估属性完整性
                    if prop_value and prop_value.strip():
                        complete_properties += 1
                    
                    # 评估属性准确性
                    if prop_value and len(prop_value.strip()) > 0:
                        accurate_properties += 1
                    
                    # 记录属性信息，用于后续一致性检查
                    if prop_name not in type_property_counts[entity.type]["properties"]:
                        type_property_counts[entity.type]["properties"][prop_name] = 0
                    type_property_counts[entity.type]["properties"][prop_name] += 1
        
        # 评估属性一致性
        if total_properties > 0:
            # 计算每种实体类型的平均属性数量
            for entity_type, stats in type_property_counts.items():
                if stats["total_entities"] > 0:
                    avg_properties = stats["property_count"] / stats["total_entities"]
                    # 检查属性分布是否均匀
                    for prop_name, count in stats["properties"].items():
                        prop_coverage = count / stats["total_entities"]
                        if prop_coverage < 0.5:
                            errors.append(f"实体类型 {entity_type} 的属性 {prop_name} 覆盖率低 ({prop_coverage:.2f})")
                        else:
                            consistent_properties += 1
        
        # 计算评分
        completeness = complete_properties / total_properties if total_properties > 0 else 0.0
        accuracy = accurate_properties / total_properties if total_properties > 0 else 0.0
        consistency = consistent_properties / total_properties if total_properties > 0 else 0.0
        
        return {
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "total_properties": total_properties,
            "complete_properties": complete_properties,
            "accurate_properties": accurate_properties,
            "consistent_properties": consistent_properties,
            "entity_types_with_properties": len(type_property_counts),
            "errors": errors
        }
    
    def evaluate_knowledge_graph(self, entities: List[Entity], relations: List[Relation]) -> Dict[str, Any]:
        """评估整个知识图谱的质量"""
        logger.info(f"开始评估知识图谱质量，实体数量: {len(entities)}, 关系数量: {len(relations)}")
        
        # 评估实体
        entity_evaluation = self.evaluate_entities(entities)
        
        # 评估关系
        relation_evaluation = self.evaluate_relations(relations, entities)
        
        # 评估属性
        property_evaluation = self.evaluate_properties(entities)
        
        # 计算整体质量评分
        # 实体、关系、属性的权重分别为0.4、0.4、0.2
        entity_score = (entity_evaluation["completeness"] + entity_evaluation["accuracy"] + entity_evaluation["consistency"]) / 3
        relation_score = (relation_evaluation["completeness"] + relation_evaluation["accuracy"] + relation_evaluation["consistency"]) / 3
        property_score = (property_evaluation["completeness"] + property_evaluation["accuracy"] + property_evaluation["consistency"]) / 3
        
        overall_quality = entity_score * 0.4 + relation_score * 0.4 + property_score * 0.2
        
        # 更新指标
        self._metrics = {
            "entity_completeness": entity_evaluation["completeness"],
            "entity_accuracy": entity_evaluation["accuracy"],
            "entity_consistency": entity_evaluation["consistency"],
            "relation_completeness": relation_evaluation["completeness"],
            "relation_accuracy": relation_evaluation["accuracy"],
            "relation_consistency": relation_evaluation["consistency"],
            "property_completeness": property_evaluation["completeness"],
            "property_accuracy": property_evaluation["accuracy"],
            "property_consistency": property_evaluation["consistency"],
            "overall_quality": overall_quality
        }
        
        # 生成评估报告
        report = {
            "timestamp": "2025-11-27",  # 实际应用中应使用当前时间
            "entity_evaluation": entity_evaluation,
            "relation_evaluation": relation_evaluation,
            "property_evaluation": property_evaluation,
            "metrics": self._metrics,
            "overall_quality": overall_quality,
            "quality_level": self._get_quality_level(overall_quality),
            "recommendations": self._generate_recommendations(entity_evaluation, relation_evaluation, property_evaluation)
        }
        
        logger.info(f"知识图谱质量评估完成，整体质量评分: {overall_quality:.2f}")
        return report
    
    def _get_quality_level(self, score: float) -> str:
        """根据评分获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "中等"
        elif score >= 0.6:
            return "及格"
        else:
            return "不及格"
    
    def _generate_recommendations(self, entity_eval: Dict[str, Any], relation_eval: Dict[str, Any], property_eval: Dict[str, Any]) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        # 基于实体评估的建议
        if entity_eval["completeness"] < 0.8:
            recommendations.append("提高实体完整性，确保所有实体都有明确的名称和类型")
        if entity_eval["accuracy"] < 0.8:
            recommendations.append("提高实体准确性，确保实体名称符合规范")
        if entity_eval["consistency"] < 0.8:
            recommendations.append("提高实体一致性，避免重复实体")
        
        # 基于关系评估的建议
        if relation_eval["completeness"] < 0.8:
            recommendations.append("提高关系完整性，确保所有关系都有明确的类型和实体引用")
        if relation_eval["accuracy"] < 0.8:
            recommendations.append("提高关系准确性，确保关系引用的实体存在")
        if relation_eval["consistency"] < 0.8:
            recommendations.append("提高关系一致性，避免重复关系")
        if relation_eval["relation_type_count"] < 5 and len(relation_eval) > 10:
            recommendations.append("增加关系类型多样性，丰富知识图谱的语义连接")
        
        # 基于属性评估的建议
        if property_eval["completeness"] < 0.8:
            recommendations.append("提高属性完整性，为实体添加更多相关属性")
        if property_eval["accuracy"] < 0.8:
            recommendations.append("提高属性准确性，确保属性值符合规范")
        if property_eval["consistency"] < 0.8:
            recommendations.append("提高属性一致性，确保相同类型实体具有相似的属性结构")
        
        return recommendations
    
    def get_metrics(self) -> Dict[str, float]:
        """获取当前的质量指标"""
        return self._metrics.copy()
    
    def generate_quality_report(self, evaluation_result: Dict[str, Any]) -> str:
        """生成格式化的质量评估报告"""
        report = f"""
# 知识图谱质量评估报告

## 基本信息
- 评估时间: {evaluation_result['timestamp']}
- 实体数量: {evaluation_result['entity_evaluation']['total_entities']}
- 关系数量: {evaluation_result['relation_evaluation']['total_relations']}
- 整体质量评分: {evaluation_result['overall_quality']:.2f}
- 质量等级: {evaluation_result['quality_level']}

## 实体评估
- 完整性: {evaluation_result['entity_evaluation']['completeness']:.2f}
- 准确性: {evaluation_result['entity_evaluation']['accuracy']:.2f}
- 一致性: {evaluation_result['entity_evaluation']['consistency']:.2f}
- 完整实体数: {evaluation_result['entity_evaluation']['complete_entities']}/{evaluation_result['entity_evaluation']['total_entities']}
- 准确实体数: {evaluation_result['entity_evaluation']['accurate_entities']}/{evaluation_result['entity_evaluation']['total_entities']}
- 一致实体数: {evaluation_result['entity_evaluation']['consistent_entities']}/{evaluation_result['entity_evaluation']['total_entities']}

## 关系评估
- 完整性: {evaluation_result['relation_evaluation']['completeness']:.2f}
- 准确性: {evaluation_result['relation_evaluation']['accuracy']:.2f}
- 一致性: {evaluation_result['relation_evaluation']['consistency']:.2f}
- 完整关系数: {evaluation_result['relation_evaluation']['complete_relations']}/{evaluation_result['relation_evaluation']['total_relations']}
- 准确关系数: {evaluation_result['relation_evaluation']['accurate_relations']}/{evaluation_result['relation_evaluation']['total_relations']}
- 一致关系数: {evaluation_result['relation_evaluation']['consistent_relations']}/{evaluation_result['relation_evaluation']['total_relations']}
- 关系类型数量: {evaluation_result['relation_evaluation']['relation_type_count']}

## 属性评估
- 完整性: {evaluation_result['property_evaluation']['completeness']:.2f}
- 准确性: {evaluation_result['property_evaluation']['accuracy']:.2f}
- 一致性: {evaluation_result['property_evaluation']['consistency']:.2f}
- 属性总数: {evaluation_result['property_evaluation']['total_properties']}
- 完整属性数: {evaluation_result['property_evaluation']['complete_properties']}
- 准确属性数: {evaluation_result['property_evaluation']['accurate_properties']}
- 一致属性数: {evaluation_result['property_evaluation']['consistent_properties']}
- 具有属性的实体类型数: {evaluation_result['property_evaluation']['entity_types_with_properties']}

## 改进建议
"""
        
        for i, recommendation in enumerate(evaluation_result['recommendations'], 1):
            report += f"{i}. {recommendation}\n"
        
        # 添加错误信息
        all_errors = []
        if evaluation_result['entity_evaluation']['errors']:
            all_errors.extend([f"实体错误: {error}" for error in evaluation_result['entity_evaluation']['errors']])
        if evaluation_result['relation_evaluation']['errors']:
            all_errors.extend([f"关系错误: {error}" for error in evaluation_result['relation_evaluation']['errors']])
        if evaluation_result['property_evaluation']['errors']:
            all_errors.extend([f"属性错误: {error}" for error in evaluation_result['property_evaluation']['errors']])
        
        if all_errors:
            report += "\n## 错误信息\n"
            for i, error in enumerate(all_errors, 1):
                report += f"{i}. {error}\n"
        
        return report


# 创建全局质量评估器实例
quality_evaluator = KnowledgeGraphQualityEvaluator()
