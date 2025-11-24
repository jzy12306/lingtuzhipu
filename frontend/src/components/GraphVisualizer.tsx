import React, { useRef, useEffect, useState } from 'react';
import * as echarts from 'echarts';
import {
  Card,
  Button,
  Slider,
  Select,
  Input,
  Tag,
  Tooltip,
  Modal,
  Spin,
  message,
  Radio,
  Space,
} from 'antd';
import { 
  ZoomInOutlined, 
  ZoomOutOutlined, 
  FullscreenOutlined,
  FileImageOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  PlusOutlined,
  MinusOutlined,
  LayoutOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  UndoOutlined,
  RedoOutlined,
  SaveOutlined,
} from '@ant-design/icons';

const { Option } = Select;
const { Search } = Input;

interface Node {
  id: string;
  name: string;
  type: string;
  value?: number;
  symbolSize?: number;
  category?: number;
  draggable?: boolean;
  itemStyle?: {
    color?: string;
    borderColor?: string;
    borderWidth?: number;
    shadowBlur?: number;
    shadowColor?: string;
  };
  label?: {
    show?: boolean;
    fontSize?: number;
    color?: string;
    formatter?: string | Function;
  };
  emphasis?: {
    itemStyle?: {
      color?: string;
      borderColor?: string;
      borderWidth?: number;
    };
  };
}

interface Edge {
  source: string;
  target: string;
  value?: number;
  label?: {
    show?: boolean;
    formatter?: string;
  };
  lineStyle?: {
    color?: string | string[];
    width?: number;
    curveness?: number;
  };
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  categories: {
    name: string;
    itemStyle?: {
      color?: string;
    };
  }[];
}

interface NodeDetail {
  id: string;
  name: string;
  type: string;
  properties: Record<string, any>;
  relationships: {
    type: string;
    target: Node;
  }[];
}

interface GraphVisualizerProps {
  initialData?: GraphData;
  height?: string | number;
  autoFit?: boolean;
  defaultLayout?: 'force' | 'circular' | 'radial' | 'graph' | 'none';
  selectedEntityId?: string;
  onNodeClick?: (node: Node) => void;
  onNodeDoubleClick?: (node: Node) => void;
  onEdgeClick?: (edge: Edge) => void;
  loading?: boolean;
  readonly?: boolean;
}

const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  initialData,
  height = 600,
  autoFit = true,
  defaultLayout = 'force',
  selectedEntityId,
  onNodeClick,
  onNodeDoubleClick,
  onEdgeClick,
  loading = false,
  readonly = false,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [currentLayout, setCurrentLayout] = useState(defaultLayout);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [nodeDetail, setNodeDetail] = useState<NodeDetail | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showLabels, setShowLabels] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [nodeFilters, setNodeFilters] = useState<string[]>([]);
  const [edgeFilters, setEdgeFilters] = useState<string[]>([]);
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    edges: [],
    categories: [],
  });
  const [categories, setCategories] = useState<Set<string>>(new Set());
  const [edgeTypes, setEdgeTypes] = useState<Set<string>>(new Set());

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current) return;

    // 销毁已有的实例
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // 创建新实例
    chartInstance.current = echarts.init(chartRef.current);

    // 设置响应式
    if (autoFit) {
      const handleResize = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', handleResize);
      
      // 组件卸载时移除事件监听
      return () => {
        window.removeEventListener('resize', handleResize);
        chartInstance.current?.dispose();
      };
    }
  }, [autoFit]);

  // 当数据或布局变化时更新图表
  useEffect(() => {
    if (!chartInstance.current) return;

    const data = initialData || graphData;
    if (!data.nodes.length && !data.edges.length) {
      // 显示空状态
      chartInstance.current.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16,
          },
        },
      });
      return;
    }

    // 收集所有类型
    const allCategories = new Set<string>();
    const allEdgeTypes = new Set<string>();
    
    data.nodes.forEach(node => {
      allCategories.add(node.type);
    });
    
    data.edges.forEach(edge => {
      if (edge.label?.formatter) {
        allEdgeTypes.add(typeof edge.label.formatter === 'string' ? edge.label.formatter : '');
      }
    });
    
    setCategories(allCategories);
    setEdgeTypes(allEdgeTypes);
    
    // 准备图表配置
    const option = {
      tooltip: {
        formatter: function(params: any) {
          if (params.dataType === 'node') {
            return `
              <div style="padding: 8px;">
                <strong>${params.name}</strong><br/>
                <span style="color: #666;">类型: ${params.data.type}</span><br/>
                ${params.data.value ? `<span>值: ${params.data.value}</span>` : ''}
              </div>
            `;
          } else if (params.dataType === 'edge') {
            return `
              <div style="padding: 8px;">
                <strong>关系</strong><br/>
                <span style="color: #666;">${params.data.sourceName} -> ${params.data.targetName}</span><br/>
                ${params.data.label?.formatter ? `<span>类型: ${params.data.label.formatter}</span>` : ''}
              </div>
            `;
          }
          return params.name || '';
        },
      },
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut',
      legend: {
        data: Array.from(allCategories),
        bottom: 10,
        left: 'center',
        selectedMode: 'multiple',
        textStyle: {
          fontSize: 12,
        },
      },
      series: [
        {
          type: 'graph',
          layout: currentLayout === 'none' ? 'none' : currentLayout,
          data: data.nodes.map(node => ({
            ...node,
            label: {
              show: showLabels,
              fontSize: 12,
              color: '#333',
              formatter: '{b}',
              ...node.label,
            },
            draggable: !readonly,
          })),
          links: data.edges.map(edge => ({
            ...edge,
            label: {
              show: edge.label?.show !== false && showLabels,
              fontSize: 10,
              formatter: edge.label?.formatter || '',
              ...edge.label,
            },
          })),
          categories: Array.from(allCategories).map((category, index) => ({
            name: category,
            itemStyle: {
              color: getCategoryColor(index),
            },
          })),
          roam: true,
          scaleLimit: {
            min: 0.1,
            max: 10,
          },
          label: {
            position: 'right',
            formatter: '{b}',
          },
          lineStyle: {
            color: 'source',
            curveness: 0.3,
            width: 2,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
          // 力导向图配置
          force: currentLayout === 'force' ? {
            repulsion: 1000,
            edgeLength: [100, 150],
            gravity: 0.1,
            layoutAnimation: true,
          } : undefined,
          // 圆形布局配置
          circular: currentLayout === 'circular' ? {
            rotateLabel: true,
            radius: ['40%', '70%'],
          } : undefined,
          // 放射状布局配置
          radial: currentLayout === 'radial' ? {
            center: ['50%', '50%'],
            r: ['15%', '80%'],
            autoRotate: true,
          } : undefined,
        },
      ],
    };

    chartInstance.current.setOption(option);

    // 添加事件监听
    chartInstance.current.off('click');
    chartInstance.current.on('click', (params) => {
      if (params.dataType === 'node') {
        handleNodeClick(params.data);
        onNodeClick?.(params.data);
      } else if (params.dataType === 'edge') {
        onEdgeClick?.(params.data);
      }
    });

    chartInstance.current.off('dblclick');
    chartInstance.current.on('dblclick', (params) => {
      if (params.dataType === 'node') {
        onNodeDoubleClick?.(params.data);
      }
    });

    // 监听缩放事件
    chartInstance.current.off('dataZoom');
    chartInstance.current.on('dataZoom', (params) => {
      setZoomLevel(params.batch[0]?.zoom || 1);
    });

    // 如果指定了选中实体，则高亮显示
    if (selectedEntityId) {
      highlightNodeById(selectedEntityId);
    }
  }, [chartInstance.current, initialData, graphData, currentLayout, showLabels, selectedEntityId]);

  // 处理节点点击
  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
    // 模拟获取节点详情
    fetchNodeDetail(node.id).then(detail => {
      setNodeDetail(detail);
      setDetailModalVisible(true);
    });
  };

  // 模拟获取节点详情
  const fetchNodeDetail = async (nodeId: string): Promise<NodeDetail> => {
    // 这里应该调用真实API获取节点详情
    // const response = await axios.get(`${API_ENDPOINTS.GRAPH.NODE_DETAIL}/${nodeId}`);
    // return response.data;
    
    // 模拟数据
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          id: nodeId,
          name: selectedNode?.name || '未知实体',
          type: selectedNode?.type || 'unknown',
          properties: {
            description: '这是一个实体的详细描述信息',
            createdAt: '2023-01-01',
            updatedAt: '2023-01-15',
            source: '系统导入',
            confidence: 0.95,
            metadata: {
              tags: ['重要', '已验证'],
              version: '1.0',
            },
          },
          relationships: [
            {
              type: '相关于',
              target: {
                id: 'related1',
                name: '相关实体1',
                type: 'related_type',
              },
            },
            {
              type: '包含',
              target: {
                id: 'related2',
                name: '子实体2',
                type: 'child_type',
              },
            },
          ],
        });
      }, 500);
    });
  };

  // 根据索引获取类别颜色
  const getCategoryColor = (index: number): string => {
    const colors = [
      '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
      '#13c2c2', '#eb2f96', '#fa8c16', '#a0d911', '#fadb14',
      '#f759ab', '#722ed1', '#13c2c2', '#fa541c', '#2f54eb',
    ];
    return colors[index % colors.length];
  };

  // 缩放控制
  const handleZoomIn = () => {
    const newZoom = zoomLevel * 1.2;
    chartInstance.current?.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100 / newZoom,
    });
    setZoomLevel(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = zoomLevel * 0.8;
    chartInstance.current?.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100 / newZoom,
    });
    setZoomLevel(newZoom);
  };

  // 重置视图
  const handleResetView = () => {
    chartInstance.current?.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100,
    });
    setZoomLevel(1);
  };

  // 导出为图片
  const handleExportImage = () => {
    if (!chartInstance.current) return;
    
    const url = chartInstance.current.getDataURL({
      pixelRatio: 2,
      backgroundColor: '#fff',
    });
    
    const link = document.createElement('a');
    link.download = `knowledge-graph-${Date.now()}.png`;
    link.href = url;
    link.click();
    
    message.success('图片导出成功');
  };

  // 切换标签显示
  const toggleLabels = () => {
    setShowLabels(!showLabels);
  };

  // 高亮指定节点
  const highlightNodeById = (nodeId: string) => {
    if (!chartInstance.current) return;
    
    // 获取所有节点
    const option = chartInstance.current.getOption();
    const nodes = option.series?.[0]?.data as Node[];
    
    if (!nodes) return;
    
    // 更新节点样式以高亮目标节点及其相邻节点
    const updatedNodes = nodes.map(node => {
      if (node.id === nodeId) {
        return {
          ...node,
          itemStyle: {
            color: '#ff4d4f',
            borderColor: '#ff4d4f',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(255, 77, 79, 0.5)',
          },
          emphasis: {
            itemStyle: {
              color: '#ff4d4f',
              borderColor: '#ff4d4f',
              borderWidth: 3,
            },
          },
          symbolSize: node.symbolSize ? node.symbolSize * 1.5 : 50,
        };
      }
      return node;
    });
    
    // 更新图表
    chartInstance.current.setOption({
      series: [{
        data: updatedNodes,
      }],
    });
    
    setHighlightedNodes([nodeId]);
  };

  // 切换筛选面板
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  // 应用筛选
  const applyFilters = () => {
    // 这里实现筛选逻辑
    message.info('筛选功能开发中');
  };

  // 切换节点类型筛选
  const toggleNodeFilter = (type: string) => {
    setNodeFilters(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  // 切换关系类型筛选
  const toggleEdgeFilter = (type: string) => {
    setEdgeFilters(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  // 改变布局
  const changeLayout = (layout: string) => {
    setCurrentLayout(layout as any);
  };

  // 实体搜索
  const handleEntitySearch = (value: string) => {
    if (!value.trim()) return;
    
    // 这里实现搜索逻辑
    message.info(`搜索实体: ${value}`);
  };

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <span>知识图谱可视化</span>
          <Space size="middle">
            <Search
              placeholder="搜索实体"
              allowClear
              style={{ width: 200 }}
              onSearch={handleEntitySearch}
              enterButton
            />
            <Button 
              icon={<FilterOutlined />}
              onClick={toggleFilters}
            >
              筛选
            </Button>
          </Space>
        </div>
      }
      extra={
        <Tooltip title="刷新">
          <Button icon={<ReloadOutlined />} onClick={() => {
            chartInstance.current?.dispatchAction({ type: 'dataZoom', start: 0, end: 100 });
          }} />
        </Tooltip>
      }
    >
      {/* 控制工具栏 */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        padding: '10px 0', 
        borderBottom: '1px solid #f0f0f0',
        marginBottom: '10px',
      }}>
        <Space size="middle">
          {/* 布局选择 */}
          <Tooltip title="布局">
            <Select 
              value={currentLayout} 
              onChange={changeLayout}
              style={{ width: 100 }}
              size="small"
            >
              <Option value="force">力导向</Option>
              <Option value="circular">圆形</Option>
              <Option value="radial">放射状</Option>
              <Option value="graph">常规图</Option>
              <Option value="none">无布局</Option>
            </Select>
          </Tooltip>
          
          {/* 标签显示控制 */}
          <Tooltip title={showLabels ? '隐藏标签' : '显示标签'}>
            <Button 
              icon={showLabels ? <EyeOutlined /> : <EyeInvisibleOutlined />} 
              size="small"
              onClick={toggleLabels}
            />
          </Tooltip>
          
          <Divider type="vertical" />
          
          {/* 缩放控制 */}
          <Tooltip title="放大">
            <Button icon={<PlusOutlined />} size="small" onClick={handleZoomIn} />
          </Tooltip>
          
          <Tooltip title="缩小">
            <Button icon={<MinusOutlined />} size="small" onClick={handleZoomOut} />
          </Tooltip>
          
          <Tooltip title="重置视图">
            <Button icon={<UndoOutlined />} size="small" onClick={handleResetView} />
          </Tooltip>
          
          <Divider type="vertical" />
          
          {/* 导出 */}
          <Tooltip title="导出为图片">
            <Button icon={<FileImageOutlined />} size="small" onClick={handleExportImage} />
          </Tooltip>
          
          <Tooltip title="全屏显示">
            <Button 
              icon={<FullscreenOutlined />} 
              size="small"
              onClick={() => {
                chartRef.current?.requestFullscreen().catch(() => {
                  message.warning('浏览器不支持全屏功能');
                });
              }}
            />
          </Tooltip>
        </Space>
      </div>
      
      {/* 筛选面板 */}
      {showFilters && (
        <Card size="small" title="筛选" style={{ marginBottom: '10px' }}>
          <div>
            <h4 style={{ marginBottom: '8px' }}>实体类型</h4>
            <div style={{ marginBottom: '16px' }}>
              {Array.from(categories).map(type => (
                <Tag
                  key={type}
                  color={nodeFilters.includes(type) ? 'blue' : 'default'}
                  closable
                  onClose={() => toggleNodeFilter(type)}
                  onClick={() => toggleNodeFilter(type)}
                  style={{ cursor: 'pointer', margin: '4px' }}
                >
                  {type}
                </Tag>
              ))}
            </div>
            
            <h4 style={{ marginBottom: '8px' }}>关系类型</h4>
            <div>
              {Array.from(edgeTypes).map(type => (
                <Tag
                  key={type}
                  color={edgeFilters.includes(type) ? 'green' : 'default'}
                  closable
                  onClose={() => toggleEdgeFilter(type)}
                  onClick={() => toggleEdgeFilter(type)}
                  style={{ cursor: 'pointer', margin: '4px' }}
                >
                  {type}
                </Tag>
              ))}
            </div>
            
            <div style={{ marginTop: '16px', textAlign: 'right' }}>
              <Button onClick={applyFilters} type="primary" size="small">应用筛选</Button>
            </div>
          </div>
        </Card>
      )}
      
      {/* 图表容器 */}
      <div 
        ref={chartRef} 
        style={{ 
          height: height,
          width: '100%',
          position: 'relative',
        }}
      >
        {loading && (
          <div 
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(255, 255, 255, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Spin size="large" tip="正在加载图谱数据..." />
          </div>
        )}
      </div>
      
      {/* 节点详情模态框 */}
      <Modal
        title={`实体详情: ${nodeDetail?.name}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={700}
        footer={[
          <Button key="cancel" onClick={() => setDetailModalVisible(false)}>关闭</Button>,
          <Button 
            key="more" 
            type="primary" 
            onClick={() => {
              message.info('查看更多详情功能开发中');
            }}
          >
            查看更多
          </Button>,
        ]}
      >
        {nodeDetail && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h3>基本信息</h3>
              <div style={{ backgroundColor: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                <p><strong>ID:</strong> {nodeDetail.id}</p>
                <p><strong>名称:</strong> {nodeDetail.name}</p>
                <p><strong>类型:</strong> <Tag color="blue">{nodeDetail.type}</Tag></p>
              </div>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <h3>属性</h3>
              <div style={{ backgroundColor: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {Object.entries(nodeDetail.properties).map(([key, value]) => (
                  <p key={key}>
                    <strong>{key}:</strong> 
                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                  </p>
                ))}
              </div>
            </div>
            
            <div>
              <h3>关系</h3>
              {nodeDetail.relationships.length > 0 ? (
                <div>
                  {nodeDetail.relationships.map((rel, index) => (
                    <div 
                      key={index} 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: '8px',
                        padding: '8px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ fontWeight: 'bold', marginRight: '8px' }}>{rel.type}</div>
                      <div>
                        <Tag color="green">{rel.target.type}</Tag>
                        <span style={{ marginLeft: '8px' }}>{rel.target.name}</span>
                      </div>
                      <Button 
                        size="small" 
                        style={{ marginLeft: 'auto' }}
                        onClick={() => {
                          highlightNodeById(rel.target.id);
                          setDetailModalVisible(false);
                        }}
                      >
                        查看
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999' }}>无相关关系</p>
              )}
            </div>
          </div>
        )}
      </Modal>
    </Card>
  );
};

// 添加缺失的Divider组件
const Divider = ({ type }: { type: string }) => {
  return <div style={{ width: '1px', height: '24px', backgroundColor: '#f0f0f0' }} />;
};

export default GraphVisualizer;