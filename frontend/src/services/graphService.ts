import axios from 'axios';
import { API_ENDPOINTS } from '../utils/config';

// 定义知识图谱相关的数据结构
export interface Node {
  id: string;
  name: string;
  type: string;
  value?: number;
  symbolSize?: number;
  category?: number;
}

export interface Edge {
  source: string;
  target: string;
  value?: number;
  label?: {
    show?: boolean;
    formatter?: string;
  };
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
  categories: {
    name: string;
    itemStyle?: {
      color?: string;
    };
  }[];
}

export interface NodeDetail {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
  relationships: {
    type: string;
    target: Node;
  }[];
}

export interface GraphStats {
  totalNodes: number;
  totalEdges: number;
  nodeTypes: Record<string, number>;
  edgeTypes: Record<string, number>;
  recentlyAdded: {
    nodes: Node[];
    edges: Edge[];
  };
  lastUpdated: string;
}

export interface GraphQueryParams {
  entityTypes?: string[];
  relationshipTypes?: string[];
  limit?: number;
  depth?: number;
  centralEntityId?: string;
  searchTerm?: string;
  sortBy?: 'created' | 'updated' | 'name';
  order?: 'asc' | 'desc';
}

/**
 * 知识图谱服务类
 * 提供图谱数据的获取、操作和分析功能
 */
class GraphService {
  /**
   * 获取完整的知识图谱数据
   * @param params 查询参数
   * @returns 图谱数据
   */
  async getGraphData(params?: GraphQueryParams): Promise<GraphData> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.DATA, { params });
      // return response.data;
      
      // 模拟数据
      return this.getMockGraphData(params);
    } catch (error) {
      console.error('获取图谱数据失败:', error);
      throw new Error('获取图谱数据失败，请稍后重试');
    }
  }

  /**
   * 根据实体ID获取节点详情
   * @param nodeId 节点ID
   * @returns 节点详情
   */
  async getNodeDetail(nodeId: string): Promise<NodeDetail> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(`${API_ENDPOINTS.GRAPH.NODE_DETAIL}/${nodeId}`);
      // return response.data;
      
      // 模拟数据
      return this.getMockNodeDetail(nodeId);
    } catch (error) {
      console.error(`获取节点${nodeId}详情失败:`, error);
      throw new Error('获取节点详情失败');
    }
  }

  /**
   * 获取节点的关联节点（邻居）
   * @param nodeId 节点ID
   * @param limit 限制数量
   * @returns 邻居节点数据
   */
  async getNodeNeighbors(nodeId: string, limit = 20): Promise<GraphData> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(`${API_ENDPOINTS.GRAPH.NODE_NEIGHBORS}/${nodeId}`, {
      //   params: { limit }
      // });
      // return response.data;
      
      // 模拟数据
      return this.getMockNeighborsData(nodeId, limit);
    } catch (error) {
      console.error(`获取节点${nodeId}邻居失败:`, error);
      throw new Error('获取邻居节点失败');
    }
  }

  /**
   * 获取图谱统计信息
   * @returns 统计数据
   */
  async getGraphStats(): Promise<GraphStats> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.STATS);
      // return response.data;
      
      // 模拟数据
      return this.getMockGraphStats();
    } catch (error) {
      console.error('获取图谱统计失败:', error);
      throw new Error('获取统计信息失败');
    }
  }

  /**
   * 搜索图谱中的实体
   * @param query 搜索关键词
   * @param limit 限制数量
   * @returns 搜索结果
   */
  async searchEntities(query: string, limit = 10): Promise<Node[]> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.SEARCH, {
      //   params: { query, limit }
      // });
      // return response.data;
      
      // 模拟搜索
      const nodes = this.getMockNodes().filter(node => 
        node.name.toLowerCase().includes(query.toLowerCase()) ||
        node.type.toLowerCase().includes(query.toLowerCase())
      );
      return nodes.slice(0, limit);
    } catch (error) {
      console.error('搜索实体失败:', error);
      throw new Error('搜索失败，请稍后重试');
    }
  }

  /**
   * 获取图谱中的所有实体类型
   * @returns 实体类型列表
   */
  async getEntityTypes(): Promise<string[]> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.ENTITY_TYPES);
      // return response.data;
      
      // 模拟数据
      return ['technology', 'person', 'organization', 'document', 'concept', 'project', 'event', 'location'];
    } catch (error) {
      console.error('获取实体类型失败:', error);
      throw new Error('获取实体类型失败');
    }
  }

  /**
   * 获取图谱中的所有关系类型
   * @returns 关系类型列表
   */
  async getRelationshipTypes(): Promise<string[]> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.RELATIONSHIP_TYPES);
      // return response.data;
      
      // 模拟数据
      return ['related_to', 'works_for', 'wrote', 'contains', 'part_of', 'developed_by', 'located_in', 'participates_in'];
    } catch (error) {
      console.error('获取关系类型失败:', error);
      throw new Error('获取关系类型失败');
    }
  }

  /**
   * 扩展图谱（加载更多相关节点）
   * @param nodeIds 要扩展的节点ID列表
   * @param depth 扩展深度
   * @returns 扩展后的图谱数据
   */
  async expandGraph(nodeIds: string[], depth = 1): Promise<GraphData> {
    try {
      // 实际环境中调用真实API
      // const response = await axios.post(API_ENDPOINTS.GRAPH.EXPAND, {
      //   nodeIds,
      //   depth
      // });
      // return response.data;
      
      // 模拟数据
      return this.getMockExpandedGraph(nodeIds, depth);
    } catch (error) {
      console.error('扩展图谱失败:', error);
      throw new Error('扩展图谱失败，请稍后重试');
    }
  }

  // ===== 模拟数据生成方法 =====

  /**
   * 生成模拟节点数据
   */
  private getMockNodes(): Node[] {
    return [
      { id: 'n1', name: '人工智能', type: 'technology', symbolSize: 40 },
      { id: 'n2', name: '机器学习', type: 'technology', symbolSize: 35 },
      { id: 'n3', name: '深度学习', type: 'technology', symbolSize: 35 },
      { id: 'n4', name: '自然语言处理', type: 'technology', symbolSize: 35 },
      { id: 'n5', name: '计算机视觉', type: 'technology', symbolSize: 35 },
      { id: 'n6', name: '知识图谱', type: 'technology', symbolSize: 35 },
      { id: 'n7', name: '张三', type: 'person', symbolSize: 30 },
      { id: 'n8', name: '李四', type: 'person', symbolSize: 30 },
      { id: 'n9', name: '王五', type: 'person', symbolSize: 30 },
      { id: 'n10', name: 'AI研究院', type: 'organization', symbolSize: 45 },
      { id: 'n11', name: '科技公司', type: 'organization', symbolSize: 45 },
      { id: 'n12', name: '《深度学习入门》', type: 'document', symbolSize: 25 },
      { id: 'n13', name: '《知识图谱技术》', type: 'document', symbolSize: 25 },
      { id: 'n14', name: '实体识别', type: 'concept', symbolSize: 30 },
      { id: 'n15', name: '关系抽取', type: 'concept', symbolSize: 30 },
      { id: 'n16', name: 'AI项目X', type: 'project', symbolSize: 35 },
      { id: 'n17', name: '技术峰会2023', type: 'event', symbolSize: 35 },
      { id: 'n18', name: '北京', type: 'location', symbolSize: 25 },
      { id: 'n19', name: '上海', type: 'location', symbolSize: 25 },
      { id: 'n20', name: '知识图谱构建', type: 'project', symbolSize: 35 },
    ];
  }

  /**
   * 生成模拟边数据
   */
  private getMockEdges(): Edge[] {
    return [
      { source: 'n1', target: 'n2', label: { show: true, formatter: '包含' } },
      { source: 'n1', target: 'n4', label: { show: true, formatter: '包含' } },
      { source: 'n1', target: 'n5', label: { show: true, formatter: '包含' } },
      { source: 'n1', target: 'n6', label: { show: true, formatter: '包含' } },
      { source: 'n2', target: 'n3', label: { show: true, formatter: '包含' } },
      { source: 'n6', target: 'n14', label: { show: true, formatter: '使用' } },
      { source: 'n6', target: 'n15', label: { show: true, formatter: '使用' } },
      { source: 'n7', target: 'n10', label: { show: true, formatter: '工作于' } },
      { source: 'n8', target: 'n11', label: { show: true, formatter: '工作于' } },
      { source: 'n9', target: 'n10', label: { show: true, formatter: '工作于' } },
      { source: 'n7', target: 'n12', label: { show: true, formatter: '编写' } },
      { source: 'n9', target: 'n13', label: { show: true, formatter: '编写' } },
      { source: 'n10', target: 'n16', label: { show: true, formatter: '开发' } },
      { source: 'n10', target: 'n20', label: { show: true, formatter: '开发' } },
      { source: 'n7', target: 'n17', label: { show: true, formatter: '参与' } },
      { source: 'n8', target: 'n17', label: { show: true, formatter: '参与' } },
      { source: 'n10', target: 'n18', label: { show: true, formatter: '位于' } },
      { source: 'n11', target: 'n19', label: { show: true, formatter: '位于' } },
      { source: 'n16', target: 'n2', label: { show: true, formatter: '应用' } },
      { source: 'n16', target: 'n3', label: { show: true, formatter: '应用' } },
      { source: 'n20', target: 'n6', label: { show: true, formatter: '专注于' } },
      { source: 'n17', target: 'n1', label: { show: true, formatter: '主题' } },
    ];
  }

  /**
   * 生成模拟图谱数据
   */
  private getMockGraphData(params?: GraphQueryParams): GraphData {
    let nodes = this.getMockNodes();
    let edges = this.getMockEdges();
    
    // 应用过滤条件
    if (params?.entityTypes && params.entityTypes.length > 0) {
      const filteredNodeIds = new Set(
        nodes.filter(node => params!.entityTypes!.includes(node.type)).map(node => node.id)
      );
      nodes = nodes.filter(node => filteredNodeIds.has(node.id));
      edges = edges.filter(edge => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target));
    }
    
    // 限制数量
    if (params?.limit && params.limit > 0) {
      nodes = nodes.slice(0, params.limit);
      // 只保留相关的边
      const nodeIds = new Set(nodes.map(node => node.id));
      edges = edges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target));
    }
    
    // 获取所有类别
    const categories = Array.from(new Set(nodes.map(node => node.type))).map(type => ({
      name: type,
    }));
    
    // 为节点分配类别索引
    const categorizedNodes = nodes.map(node => ({
      ...node,
      category: categories.findIndex(cat => cat.name === node.type),
    }));
    
    return {
      nodes: categorizedNodes,
      edges,
      categories,
    };
  }

  /**
   * 生成模拟节点详情
   */
  private getMockNodeDetail(nodeId: string): NodeDetail {
    const node = this.getMockNodes().find(n => n.id === nodeId);
    if (!node) {
      throw new Error('节点不存在');
    }
    
    // 找出相关关系
    const allEdges = this.getMockEdges();
    const outEdges = allEdges.filter(edge => edge.source === nodeId);
    const inEdges = allEdges.filter(edge => edge.target === nodeId);
    
    const relationships = [];
    const allNodes = this.getMockNodes();
    
    // 处理出边
    outEdges.forEach(edge => {
      const targetNode = allNodes.find(n => n.id === edge.target);
      if (targetNode) {
        relationships.push({
          type: edge.label?.formatter || '相关于',
          target: targetNode,
        });
      }
    });
    
    // 处理入边
    inEdges.forEach(edge => {
      const sourceNode = allNodes.find(n => n.id === edge.source);
      if (sourceNode) {
        relationships.push({
          type: `被${edge.label?.formatter || '相关于'}`,
          target: sourceNode,
        });
      }
    });
    
    return {
      id: node.id,
      name: node.name,
      type: node.type,
      properties: {
        description: `这是一个${this.getEntityTypeName(node.type)}类型的实体`,
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-06-15T14:30:00Z',
        source: '系统导入',
        confidence: 0.95,
        popularity: Math.floor(Math.random() * 100),
        metadata: {
          tags: this.getMockTags(node.type),
          version: '1.0',
          verified: true,
        },
      },
      relationships,
    };
  }

  /**
   * 生成模拟邻居数据
   */
  private getMockNeighborsData(nodeId: string, limit = 20): GraphData {
    const allEdges = this.getMockEdges();
    const allNodes = this.getMockNodes();
    
    // 找出与目标节点相连的所有边
    const relatedEdges = allEdges.filter(
      edge => edge.source === nodeId || edge.target === nodeId
    );
    
    // 收集所有相关的节点ID
    const nodeIds = new Set([nodeId]);
    relatedEdges.forEach(edge => {
      nodeIds.add(edge.source);
      nodeIds.add(edge.target);
    });
    
    // 获取相关节点
    let nodes = allNodes.filter(node => nodeIds.has(node.id));
    const edges = relatedEdges;
    
    // 限制数量
    if (nodes.length > limit) {
      // 保留中心节点
      const centerNode = nodes.find(n => n.id === nodeId);
      // 随机选择其他节点
      const otherNodes = nodes.filter(n => n.id !== nodeId);
      const selectedOtherNodes = otherNodes.slice(0, limit - 1);
      nodes = centerNode ? [centerNode, ...selectedOtherNodes] : selectedOtherNodes;
      
      // 更新边
      const newNodeIds = new Set(nodes.map(n => n.id));
      edges.filter(edge => newNodeIds.has(edge.source) && newNodeIds.has(edge.target));
    }
    
    // 获取所有类别
    const categories = Array.from(new Set(nodes.map(node => node.type))).map(type => ({
      name: type,
    }));
    
    // 为节点分配类别索引
    const categorizedNodes = nodes.map(node => ({
      ...node,
      category: categories.findIndex(cat => cat.name === node.type),
      // 中心节点更大更突出
      symbolSize: node.id === nodeId ? (node.symbolSize || 30) * 1.5 : node.symbolSize,
    }));
    
    return {
      nodes: categorizedNodes,
      edges,
      categories,
    };
  }

  /**
   * 生成模拟扩展图谱数据
   */
  private getMockExpandedGraph(nodeIds: string[], depth = 1): GraphData {
    // 简化实现，获取包含所有指定节点的图谱
    const allNodes = this.getMockNodes();
    const allEdges = this.getMockEdges();
    
    // 收集所有相关节点ID
    const relatedNodeIds = new Set<string>(nodeIds);
    
    // 根据深度扩展
    for (let d = 0; d < depth; d++) {
      const currentIds = Array.from(relatedNodeIds);
      allEdges.forEach(edge => {
        if (currentIds.includes(edge.source) || currentIds.includes(edge.target)) {
          relatedNodeIds.add(edge.source);
          relatedNodeIds.add(edge.target);
        }
      });
    }
    
    // 过滤节点和边
    const nodes = allNodes.filter(node => relatedNodeIds.has(node.id));
    const edges = allEdges.filter(edge => 
      relatedNodeIds.has(edge.source) && relatedNodeIds.has(edge.target)
    );
    
    // 获取所有类别
    const categories = Array.from(new Set(nodes.map(node => node.type))).map(type => ({
      name: type,
    }));
    
    // 为节点分配类别索引
    const categorizedNodes = nodes.map(node => ({
      ...node,
      category: categories.findIndex(cat => cat.name === node.type),
      // 原始节点更大更突出
      symbolSize: nodeIds.includes(node.id) ? (node.symbolSize || 30) * 1.2 : node.symbolSize,
    }));
    
    return {
      nodes: categorizedNodes,
      edges,
      categories,
    };
  }

  /**
   * 生成模拟统计数据
   */
  private getMockGraphStats(): GraphStats {
    const nodes = this.getMockNodes();
    const edges = this.getMockEdges();
    
    // 统计节点类型
    const nodeTypeStats: Record<string, number> = {};
    nodes.forEach(node => {
      nodeTypeStats[node.type] = (nodeTypeStats[node.type] || 0) + 1;
    });
    
    // 统计边类型
    const edgeTypeStats: Record<string, number> = {};
    edges.forEach(edge => {
      const type = edge.label?.formatter || 'unknown';
      edgeTypeStats[type] = (edgeTypeStats[type] || 0) + 1;
    });
    
    return {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      nodeTypes: nodeTypeStats,
      edgeTypes: edgeTypeStats,
      recentlyAdded: {
        nodes: nodes.slice(-5),
        edges: edges.slice(-3),
      },
      lastUpdated: new Date().toISOString(),
    };
  }

  /**
   * 获取实体类型的中文名称
   */
  private getEntityTypeName(type: string): string {
    const typeMap: Record<string, string> = {
      'technology': '技术',
      'person': '人物',
      'organization': '组织',
      'document': '文档',
      'concept': '概念',
      'project': '项目',
      'event': '事件',
      'location': '地点',
    };
    return typeMap[type] || type;
  }

  /**
   * 生成模拟标签
   */
  private getMockTags(type: string): string[] {
    const tagSets: Record<string, string[]> = {
      'technology': ['热门', '前沿', 'AI相关'],
      'person': ['专家', '研究人员'],
      'organization': ['研究机构', '企业'],
      'document': ['教程', '学术'],
      'concept': ['基础', '重要'],
      'project': ['活跃', '创新'],
      'event': ['会议', '交流'],
      'location': ['总部', '分部'],
    };
    
    return tagSets[type] || ['默认'];
  }
}

// 导出单例
export default new GraphService();