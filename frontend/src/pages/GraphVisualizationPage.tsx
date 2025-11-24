import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Tabs,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Spin,
  message,
  Slider,
  Checkbox,
  Divider,
  Modal,
  Empty,
  Collapse,
  Row,
  Col,
} from 'antd';
import {
  SearchOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  FullscreenOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  FilterOutlined,
  ReloadOutlined,
  PlusOutlined,
  MinusOutlined,
  MenuOutlined,
  XOutlined,
  LinkOutlined,
  UserOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { useAuth } from '../context/AuthContext';
import { API_ENDPOINTS } from '../utils/config';
import axios from 'axios';
import { useLocation, useNavigate } from 'react-router-dom';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;

interface Entity {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
  degree: number;
}

interface Relationship {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphData {
  entities: Entity[];
  relationships: Relationship[];
}

const GraphVisualizationPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  
  // 状态管理
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<GraphData>({ entities: [], relationships: [] });
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<Relationship | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [graphLayout, setGraphLayout] = useState<'force' | 'circular' | 'none'>('force');
  const [graphOptions, setGraphOptions] = useState({
    force: {
      repulsion: 100,
      gravity: 0.1,
      edgeLength: 100,
    },
    nodeSize: 30,
    edgeWidth: 2,
  });
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [expandLevel, setExpandLevel] = useState(1);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);

  // 从URL获取文档ID
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const docId = params.get('doc_id');
    if (docId) {
      setSelectedDocId(docId);
      fetchGraphData(docId);
    }
  }, [location.search]);

  // 初始化图表
  useEffect(() => {
    if (chartRef.current && !chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current);
      
      // 监听窗口大小变化
      window.addEventListener('resize', handleResize);
      
      // 设置点击事件
      chartInstanceRef.current.on('click', (params) => {
        handleChartClick(params);
      });
    }
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
        chartInstanceRef.current = null;
      }
    };
  }, []);

  // 当图数据变化时更新图表
  useEffect(() => {
    if (graphData.entities.length > 0 && chartInstanceRef.current) {
      updateChart();
    }
  }, [graphData, graphLayout, graphOptions, selectedTypes, searchQuery]);

  // 处理窗口大小变化
  const handleResize = () => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.resize();
    }
  };

  // 获取图谱数据
  const fetchGraphData = async (docId: string) => {
    try {
      setLoading(true);
      // 这里应该调用真实的API
      // const response = await axios.get(API_ENDPOINTS.GRAPH.GET(docId));
      // const data = response.data;
      
      // 模拟数据
      setTimeout(() => {
        const mockData: GraphData = {
          entities: [
            { id: 'e1', name: '人工智能', type: 'technology', properties: { description: '计算机科学的分支' }, degree: 4 },
            { id: 'e2', name: '机器学习', type: 'algorithm', properties: { description: '人工智能的子集' }, degree: 3 },
            { id: 'e3', name: '深度学习', type: 'algorithm', properties: { description: '机器学习的子集' }, degree: 2 },
            { id: 'e4', name: '神经网络', type: 'structure', properties: { description: '深度学习的基础' }, degree: 1 },
            { id: 'e5', name: '自然语言处理', type: 'application', properties: { description: 'AI在语言方面的应用' }, degree: 2 },
          ],
          relationships: [
            { id: 'r1', source: 'e1', target: 'e2', type: '包含', properties: { strength: 0.9 } },
            { id: 'r2', source: 'e2', target: 'e3', type: '包含', properties: { strength: 0.8 } },
            { id: 'r3', source: 'e3', target: 'e4', type: '使用', properties: { strength: 0.7 } },
            { id: 'r4', source: 'e1', target: 'e5', type: '应用于', properties: { strength: 0.85 } },
            { id: 'r5', source: 'e3', target: 'e5', type: '支持', properties: { strength: 0.75 } },
          ],
        };
        
        setGraphData(mockData);
        
        // 提取实体类型
        const types = Array.from(new Set(mockData.entities.map(e => e.type)));
        setEntityTypes(types);
        setSelectedTypes(types); // 默认选择所有类型
        
        setLoading(false);
      }, 1500);
    } catch (error) {
      console.error('获取图谱数据失败:', error);
      message.error('获取图谱数据失败，请稍后重试');
      setLoading(false);
    }
  };

  // 过滤图谱数据
  const getFilteredData = () => {
    let filteredEntities = [...graphData.entities];
    let filteredRelationships = [...graphData.relationships];
    
    // 按实体类型过滤
    if (selectedTypes.length > 0) {
      filteredEntities = filteredEntities.filter(entity => 
        selectedTypes.includes(entity.type)
      );
      
      // 只保留与过滤后实体相关的关系
      const entityIds = new Set(filteredEntities.map(e => e.id));
      filteredRelationships = filteredRelationships.filter(rel => 
        entityIds.has(rel.source) && entityIds.has(rel.target)
      );
    }
    
    // 按搜索词过滤
    if (searchQuery) {
      const lowerQuery = searchQuery.toLowerCase();
      filteredEntities = filteredEntities.filter(entity => 
        entity.name.toLowerCase().includes(lowerQuery) || 
        (entity.properties.description && 
         entity.properties.description.toLowerCase().includes(lowerQuery))
      );
      
      // 只保留与过滤后实体相关的关系
      const entityIds = new Set(filteredEntities.map(e => e.id));
      filteredRelationships = filteredRelationships.filter(rel => 
        entityIds.has(rel.source) && entityIds.has(rel.target)
      );
    }
    
    return { entities: filteredEntities, relationships: filteredRelationships };
  };

  // 更新图表
  const updateChart = () => {
    if (!chartInstanceRef.current) return;
    
    const filteredData = getFilteredData();
    
    // 准备图表数据
    const nodes = filteredData.entities.map(entity => ({
      id: entity.id,
      name: entity.name,
      value: entity.name,
      category: entity.type,
      symbolSize: Math.max(20, Math.min(60, entity.degree * 10 + graphOptions.nodeSize)),
      itemStyle: {
        color: getColorByType(entity.type),
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{b}',
      },
      properties: entity.properties,
    }));
    
    const edges = filteredData.relationships.map(rel => ({
      source: rel.source,
      target: rel.target,
      value: rel.type,
      label: {
        show: rel.properties?.strength > 0.8,
        formatter: rel.type,
      },
      lineStyle: {
        width: Math.max(1, rel.properties?.strength * graphOptions.edgeWidth || graphOptions.edgeWidth),
        curveness: 0.3,
      },
      relationshipType: rel.type,
      properties: rel.properties,
      id: rel.id,
    }));
    
    // 准备分类数据
    const categories = entityTypes.map(type => ({
      name: type,
      itemStyle: {
        color: getColorByType(type),
      },
    }));
    
    // 设置图表选项
    const option: EChartsOption = {
      tooltip: {
        formatter: function (params: any) {
          if (params.dataType === 'node') {
            const entity = filteredData.entities.find(e => e.id === params.data.id);
            let tooltip = `<div><strong>${params.name}</strong></div><div>类型: ${params.data.category}</div>`;
            if (entity?.properties && Object.keys(entity.properties).length > 0) {
              tooltip += '<div>属性:</div>';
              Object.entries(entity.properties).forEach(([key, value]) => {
                tooltip += `<div>${key}: ${value}</div>`;
              });
            }
            return tooltip;
          } else if (params.dataType === 'edge') {
            return `${params.data.relationshipType}`;
          }
          return params.name || '';
        },
      },
      legend: {
        data: categories.map(c => c.name),
        orient: 'vertical',
        right: 10,
        top: 'center',
      },
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: graphLayout,
          data: nodes,
          links: edges,
          categories: categories,
          roam: true,
          label: {
            show: true,
          },
          force: graphLayout === 'force' ? graphOptions.force : undefined,
          lineStyle: {
            color: 'source',
            curveness: 0.3,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
        },
      ],
    };
    
    chartInstanceRef.current.setOption(option, true);
  };

  // 处理图表点击
  const handleChartClick = (params: any) => {
    if (params.dataType === 'node') {
      const entity = graphData.entities.find(e => e.id === params.data.id);
      setSelectedEntity(entity || null);
      setSelectedRelationship(null);
    } else if (params.dataType === 'edge') {
      const relationship = graphData.relationships.find(r => r.id === params.data.id);
      setSelectedRelationship(relationship || null);
      setSelectedEntity(null);
    }
  };

  // 根据类型获取颜色
  const getColorByType = (type: string): string => {
    const colorMap: Record<string, string> = {
      technology: '#1890ff',
      algorithm: '#52c41a',
      structure: '#fa8c16',
      application: '#f5222d',
      concept: '#722ed1',
      person: '#eb2f96',
      organization: '#13c2c2',
    };
    return colorMap[type] || '#faad14';
  };

  // 获取类型中文名
  const getTypeNameCN = (type: string): string => {
    const typeMap: Record<string, string> = {
      technology: '技术',
      algorithm: '算法',
      structure: '结构',
      application: '应用',
      concept: '概念',
      person: '人物',
      organization: '组织',
    };
    return typeMap[type] || type;
  };

  // 处理类型选择变化
  const handleTypeChange = (values: string[]) => {
    setSelectedTypes(values);
  };

  // 处理布局变化
  const handleLayoutChange = (value: string) => {
    setGraphLayout(value as 'force' | 'circular' | 'none');
  };

  // 处理力导向图参数变化
  const handleForceParamChange = (param: string, value: number) => {
    setGraphOptions(prev => ({
      ...prev,
      force: {
        ...prev.force,
        [param]: value,
      },
    }));
  };

  // 处理节点大小变化
  const handleNodeSizeChange = (value: number) => {
    setGraphOptions(prev => ({
      ...prev,
      nodeSize: value,
    }));
  };

  // 处理边宽度变化
  const handleEdgeWidthChange = (value: number) => {
    setGraphOptions(prev => ({
      ...prev,
      edgeWidth: value,
    }));
  };

  // 搜索实体
  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };

  // 重置图表
  const handleResetGraph = () => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispatchAction({
        type: 'restore',
      });
    }
  };

  // 缩放控制
  const handleZoomIn = () => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispatchAction({
        type: 'zoom',
        animation: true,
        zoom: 1.2,
      });
    }
  };

  const handleZoomOut = () => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispatchAction({
        type: 'zoom',
        animation: true,
        zoom: 0.8,
      });
    }
  };

  // 全屏切换
  const toggleFullscreen = () => {
    setFullscreen(!fullscreen);
    // 实际项目中可能需要更复杂的全屏实现
    setTimeout(() => {
      handleResize();
    }, 100);
  };

  // 侧边栏切换
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
    setTimeout(() => {
      handleResize();
    }, 100);
  };

  // 下载图谱
  const handleDownload = () => {
    if (chartInstanceRef.current) {
      const url = chartInstanceRef.current.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff',
      });
      
      const link = document.createElement('a');
      link.download = `knowledge_graph_${Date.now()}.png`;
      link.href = url;
      link.click();
      message.success('图谱下载成功');
    }
  };

  // 分享图谱
  const handleShare = () => {
    message.info('分享功能开发中');
  };

  // 展开/收缩侧边栏
  const sidebarWidth = sidebarVisible ? 300 : 0;

  return (
    <div className="graph-visualization-page" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部工具栏 */}
      <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button 
            icon={<MenuOutlined />} 
            onClick={toggleSidebar}
            size="small"
          />
          <h2 style={{ margin: 0 }}>知识图谱可视化</h2>
          {selectedDocId && (
            <Tag color="blue">文档ID: {selectedDocId}</Tag>
          )}
        </Space>
        
        <Space>
          <Search
            placeholder="搜索实体"
            allowClear
            style={{ width: 200 }}
            size="small"
            onSearch={handleSearch}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button 
            icon={<FilterOutlined />} 
            onClick={() => setFilterModalVisible(true)}
            size="small"
          >
            筛选
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleResetGraph}
            size="small"
          >
            重置视图
          </Button>
          <Button 
            icon={<DownloadOutlined />} 
            onClick={handleDownload}
            size="small"
          >
            下载
          </Button>
          <Button 
            icon={<ShareAltOutlined />} 
            onClick={handleShare}
            size="small"
          >
            分享
          </Button>
          <Button 
            icon={<FullscreenOutlined />} 
            onClick={toggleFullscreen}
            size="small"
          >
            全屏
          </Button>
        </Space>
      </div>

      {/* 主内容区域 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 侧边栏 */}
        {sidebarVisible && (
          <div style={{ 
            width: sidebarWidth, 
            borderRight: '1px solid #f0f0f0', 
            padding: '16px', 
            overflow: 'auto',
            backgroundColor: '#fafafa',
          }}>
            <Collapse defaultActiveKey={['1', '2']}>
              <Panel header="节点详情" key="1">
                {selectedEntity ? (
                  <div>
                    <h3>{selectedEntity.name}</h3>
                    <Tag color="blue">类型: {getTypeNameCN(selectedEntity.type)}</Tag>
                    <div style={{ marginTop: '16px' }}>
                      <h4>属性:</h4>
                      {Object.entries(selectedEntity.properties).map(([key, value]) => (
                        <div key={key}>
                          <strong>{key}:</strong> {value}
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: '16px' }}>
                      <Button size="small" onClick={() => {
                        // 这里可以实现展开关联实体的功能
                        message.info('展开关联实体功能开发中');
                      }}>
                        展开关联实体
                      </Button>
                    </div>
                  </div>
                ) : selectedRelationship ? (
                  <div>
                    <h3>关系: {selectedRelationship.type}</h3>
                    <div>
                      <strong>源实体:</strong> {graphData.entities.find(e => e.id === selectedRelationship.source)?.name}
                    </div>
                    <div>
                      <strong>目标实体:</strong> {graphData.entities.find(e => e.id === selectedRelationship.target)?.name}
                    </div>
                    {selectedRelationship.properties && Object.keys(selectedRelationship.properties).length > 0 && (
                      <div style={{ marginTop: '16px' }}>
                        <h4>属性:</h4>
                        {Object.entries(selectedRelationship.properties).map(([key, value]) => (
                          <div key={key}>
                            <strong>{key}:</strong> {value}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <Empty description="请选择节点或关系" />
                )}
              </Panel>
              
              <Panel header="统计信息" key="2">
                <div>
                  <div>总实体数: {graphData.entities.length}</div>
                  <div>总关系数: {graphData.relationships.length}</div>
                  <div>实体类型数: {entityTypes.length}</div>
                  <div>过滤后实体数: {getFilteredData().entities.length}</div>
                  <div>过滤后关系数: {getFilteredData().relationships.length}</div>
                </div>
              </Panel>
            </Collapse>
          </div>
        )}

        {/* 图表区域 */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {loading ? (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              height: '100%' 
            }}>
              <Spin size="large" tip="加载图谱数据中..." />
            </div>
          ) : (
            <>
              <div 
                ref={chartRef} 
                style={{ 
                  width: '100%', 
                  height: '100%',
                  backgroundColor: '#fff',
                }}
              />
              
              {/* 缩放控制 */}
              <div style={{ 
                position: 'absolute', 
                bottom: '20px', 
                right: sidebarVisible ? `${sidebarWidth + 20}px` : '20px', 
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}>
                <Button 
                  icon={<ZoomInOutlined />} 
                  onClick={handleZoomIn}
                  size="large"
                  style={{ borderRadius: '4px' }}
                />
                <Button 
                  icon={<ZoomOutOutlined />} 
                  onClick={handleZoomOut}
                  size="large"
                  style={{ borderRadius: '4px' }}
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* 筛选模态框 */}
      <Modal
        title="图谱筛选"
        open={filterModalVisible}
        onCancel={() => setFilterModalVisible(false)}
        footer={[
          <Button key="reset" onClick={() => setSelectedTypes(entityTypes)}>重置</Button>,
          <Button key="close" onClick={() => setFilterModalVisible(false)}>关闭</Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <h4>实体类型筛选</h4>
            <Checkbox.Group 
              options={entityTypes.map(type => ({ 
                label: getTypeNameCN(type), 
                value: type 
              }))} 
              value={selectedTypes}
              onChange={handleTypeChange}
              style={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: '12px' }}
            />
          </div>
          
          <Divider />
          
          <div>
            <h4>布局设置</h4>
            <Select 
              value={graphLayout} 
              onChange={handleLayoutChange}
              style={{ width: '100%', marginBottom: '16px' }}
            >
              <Option value="force">力导向布局</Option>
              <Option value="circular">环形布局</Option>
              <Option value="none">无布局</Option>
            </Select>
            
            {graphLayout === 'force' && (
              <>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>斥力强度</span>
                    <span>{graphOptions.force.repulsion}</span>
                  </div>
                  <Slider 
                    min={0} 
                    max={300} 
                    value={graphOptions.force.repulsion}
                    onChange={(value) => handleForceParamChange('repulsion', value)}
                  />
                </div>
                
                <div style={{ marginTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>重力强度</span>
                    <span>{graphOptions.force.gravity.toFixed(2)}</span>
                  </div>
                  <Slider 
                    min={0} 
                    max={1} 
                    step={0.01}
                    value={graphOptions.force.gravity}
                    onChange={(value) => handleForceParamChange('gravity', value)}
                  />
                </div>
                
                <div style={{ marginTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>边长</span>
                    <span>{graphOptions.force.edgeLength}</span>
                  </div>
                  <Slider 
                    min={50} 
                    max={300} 
                    value={graphOptions.force.edgeLength}
                    onChange={(value) => handleForceParamChange('edgeLength', value)}
                  />
                </div>
              </>
            )}
          </div>
          
          <Divider />
          
          <div>
            <h4>视觉设置</h4>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>节点基础大小</span>
                <span>{graphOptions.nodeSize}</span>
              </div>
              <Slider 
                min={10} 
                max={80} 
                value={graphOptions.nodeSize}
                onChange={handleNodeSizeChange}
              />
            </div>
            
            <div style={{ marginTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>边基础宽度</span>
                <span>{graphOptions.edgeWidth}</span>
              </div>
              <Slider 
                min={1} 
                max={10} 
                value={graphOptions.edgeWidth}
                onChange={handleEdgeWidthChange}
              />
            </div>
          </div>
        </Space>
      </Modal>
    </div>
  );
};

export default GraphVisualizationPage;