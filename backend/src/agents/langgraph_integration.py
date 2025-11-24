from langgraph.graph import Graph, StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, Optional, List, Callable
import logging
import asyncio

logger = logging.getLogger(__name__)


class LangGraphIntegration:
    """LangGraph集成模块"""
    
    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graphs: Dict[str, StateGraph] = {}
        self.logger = logger.getChild("LangGraphIntegration")
    
    def create_knowledge_processing_graph(self, agent_manager) -> StateGraph:
        """创建知识处理工作流图"""
        # 定义状态类型
        class KnowledgeState:
            def __init__(self):
                self.document_content: Optional[str] = None
                self.document_type: Optional[str] = None
                self.entities = []
                self.relations = []
                self.errors = []
                self.current_step: Optional[str] = None
                self.completed_steps = []
        
        # 创建状态图
        workflow = StateGraph(KnowledgeState)
        
        # 定义节点函数
        async def analyze_document(state: KnowledgeState) -> Dict[str, Any]:
            """分析文档类型"""
            self.logger.info("执行文档分析步骤")
            try:
                # 使用分析智能体分析文档
                result = await agent_manager.process_with_agent(
                    "analyzer",
                    {"task": "analyze_document", "content": state.document_content}
                )
                
                if result.success:
                    state.document_type = result.data.get("document_type")
                    state.current_step = "extraction"
                else:
                    state.errors.append("文档分析失败")
                    state.current_step = "error"
            except Exception as e:
                self.logger.error(f"文档分析节点失败: {str(e)}")
                state.errors.append(str(e))
                state.current_step = "error"
            
            state.completed_steps.append("analyze_document")
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def extract_entities_relations(state: KnowledgeState) -> Dict[str, Any]:
            """提取实体和关系"""
            self.logger.info("执行实体关系提取步骤")
            try:
                # 使用构建者智能体提取实体关系
                result = await agent_manager.process_with_agent(
                    "builder",
                    {"task": "extract_knowledge", "content": state.document_content}
                )
                
                if result.success:
                    state.entities = result.data.get("entities", [])
                    state.relations = result.data.get("relations", [])
                    state.current_step = "validation"
                else:
                    state.errors.append("实体关系提取失败")
                    state.current_step = "error"
            except Exception as e:
                self.logger.error(f"实体关系提取节点失败: {str(e)}")
                state.errors.append(str(e))
                state.current_step = "error"
            
            state.completed_steps.append("extract_entities_relations")
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def validate_knowledge(state: KnowledgeState) -> Dict[str, Any]:
            """验证提取的知识"""
            self.logger.info("执行知识验证步骤")
            try:
                # 使用审计智能体验证知识
                result = await agent_manager.process_with_agent(
                    "auditor",
                    {
                        "task": "validate_knowledge",
                        "entities": state.entities,
                        "relations": state.relations
                    }
                )
                
                if result.success:
                    # 更新实体和关系
                    state.entities = result.data.get("validated_entities", state.entities)
                    state.relations = result.data.get("validated_relations", state.relations)
                    state.current_step = "complete"
                else:
                    # 有冲突需要处理
                    state.errors = result.data.get("conflicts", [])
                    state.current_step = "conflict_resolution"
            except Exception as e:
                self.logger.error(f"知识验证节点失败: {str(e)}")
                state.errors.append(str(e))
                state.current_step = "error"
            
            state.completed_steps.append("validate_knowledge")
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def resolve_conflicts(state: KnowledgeState) -> Dict[str, Any]:
            """解决知识冲突"""
            self.logger.info("执行冲突解决步骤")
            try:
                # 使用分析智能体解决冲突
                result = await agent_manager.process_with_agent(
                    "analyzer",
                    {
                        "task": "resolve_conflicts",
                        "conflicts": state.errors,
                        "entities": state.entities,
                        "relations": state.relations
                    }
                )
                
                if result.success:
                    state.entities = result.data.get("entities", state.entities)
                    state.relations = result.data.get("relations", state.relations)
                    state.errors = []
                    state.current_step = "complete"
                else:
                    state.current_step = "error"
            except Exception as e:
                self.logger.error(f"冲突解决节点失败: {str(e)}")
                state.errors.append(str(e))
                state.current_step = "error"
            
            state.completed_steps.append("resolve_conflicts")
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def handle_error(state: KnowledgeState) -> Dict[str, Any]:
            """处理错误"""
            self.logger.error(f"工作流错误: {state.errors}")
            state.current_step = "error"
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        # 添加节点
        workflow.add_node("analyze_document", analyze_document)
        workflow.add_node("extract_entities_relations", extract_entities_relations)
        workflow.add_node("validate_knowledge", validate_knowledge)
        workflow.add_node("resolve_conflicts", resolve_conflicts)
        workflow.add_node("handle_error", handle_error)
        
        # 添加边
        workflow.add_edge(START, "analyze_document")
        
        # 条件边函数
        def route_after_analysis(state: Dict[str, Any]) -> str:
            return "extract_entities_relations" if state.get("current_step") == "extraction" else "handle_error"
        
        def route_after_extraction(state: Dict[str, Any]) -> str:
            return "validate_knowledge" if state.get("current_step") == "validation" else "handle_error"
        
        def route_after_validation(state: Dict[str, Any]) -> str:
            if state.get("current_step") == "complete":
                return END
            elif state.get("current_step") == "conflict_resolution":
                return "resolve_conflicts"
            return "handle_error"
        
        def route_after_resolution(state: Dict[str, Any]) -> str:
            return END if state.get("current_step") == "complete" else "handle_error"
        
        # 添加条件边
        workflow.add_conditional_edges(
            "analyze_document",
            route_after_analysis
        )
        
        workflow.add_conditional_edges(
            "extract_entities_relations",
            route_after_extraction
        )
        
        workflow.add_conditional_edges(
            "validate_knowledge",
            route_after_validation
        )
        
        workflow.add_conditional_edges(
            "resolve_conflicts",
            route_after_resolution
        )
        
        workflow.add_edge("handle_error", END)
        
        # 编译图
        self.graphs["knowledge_processing"] = workflow
        return workflow
    
    def create_query_processing_graph(self, agent_manager) -> StateGraph:
        """创建查询处理工作流图"""
        # 定义状态类型
        class QueryState:
            def __init__(self):
                self.query: Optional[str] = None
                self.interpreted_query: Optional[str] = None
                self.knowledge_graph_queries: List[Dict[str, Any]] = []
                self.results: List[Dict[str, Any]] = []
                self.explanation: Optional[str] = None
                self.errors = []
        
        # 创建状态图
        workflow = StateGraph(QueryState)
        
        # 定义节点函数
        async def interpret_query(state: QueryState) -> Dict[str, Any]:
            """解释用户查询"""
            try:
                result = await agent_manager.process_with_agent(
                    "analyzer",
                    {"task": "interpret_query", "query": state.query}
                )
                
                if result.success:
                    state.interpreted_query = result.data.get("interpreted_query")
                    state.knowledge_graph_queries = result.data.get("graph_queries", [])
                else:
                    state.errors.append("查询解释失败")
            except Exception as e:
                state.errors.append(str(e))
            
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def execute_queries(state: QueryState) -> Dict[str, Any]:
            """执行知识图谱查询"""
            if state.errors:
                return state.dict() if hasattr(state, "dict") else state.__dict__
            
            try:
                for gq in state.knowledge_graph_queries:
                    result = await agent_manager.process_with_agent(
                        "builder",
                        {"task": "execute_graph_query", "query": gq}
                    )
                    
                    if result.success:
                        state.results.append(result.data)
                    else:
                        state.errors.append(f"查询执行失败: {gq.get('id')}")
            except Exception as e:
                state.errors.append(str(e))
            
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        async def generate_explanation(state: QueryState) -> Dict[str, Any]:
            """生成查询结果解释"""
            if state.errors:
                return state.dict() if hasattr(state, "dict") else state.__dict__
            
            try:
                result = await agent_manager.process_with_agent(
                    "analyzer",
                    {
                        "task": "explain_results",
                        "query": state.query,
                        "results": state.results
                    }
                )
                
                if result.success:
                    state.explanation = result.data.get("explanation")
                else:
                    state.errors.append("结果解释生成失败")
            except Exception as e:
                state.errors.append(str(e))
            
            return state.dict() if hasattr(state, "dict") else state.__dict__
        
        # 添加节点
        workflow.add_node("interpret_query", interpret_query)
        workflow.add_node("execute_queries", execute_queries)
        workflow.add_node("generate_explanation", generate_explanation)
        
        # 添加边
        workflow.add_edge(START, "interpret_query")
        workflow.add_edge("interpret_query", "execute_queries")
        workflow.add_edge("execute_queries", "generate_explanation")
        workflow.add_edge("generate_explanation", END)
        
        # 编译图
        self.graphs["query_processing"] = workflow
        return workflow
    
    def compile_graph(self, graph_id: str, config: Optional[Dict[str, Any]] = None) -> Graph:
        """编译指定的图"""
        if graph_id not in self.graphs:
            raise ValueError(f"图不存在: {graph_id}")
        
        graph = self.graphs[graph_id]
        config = config or {"checkpointer": self.checkpointer}
        
        return graph.compile(**config)
    
    async def run_graph(
        self, 
        graph_id: str, 
        initial_state: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """运行图"""
        try:
            graph = self.compile_graph(graph_id)
            
            # 如果提供了线程ID，则使用它
            config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
            
            # 运行图
            result = await graph.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "result": result,
                "graph_id": graph_id
            }
        except Exception as e:
            self.logger.error(f"图运行失败: {str(e)}")
            raise


# 创建全局LangGraph集成实例
langgraph_integration = LangGraphIntegration()