import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Tabs,
  Space,
  Table,
  Spin,
  message,
  Divider,
  Tag,
  Modal,
  Empty,
  Collapse,
  Row,
  Col,
  Select,
  Form,
  Statistic,
} from 'antd';
import {
  SearchOutlined,
  CodeOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  HistoryOutlined,
  SettingsOutlined,
  SendOutlined,
  PlayCircleOutlined,
  SaveOutlined,
  CopyOutlined,
  RefreshOutlined,
  HelpOutlined,
  ChevronRightOutlined,
  CheckOutlined,
  AlertCircleOutlined,
  UserOutlined,
  BrainOutlined,
} from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import { API_ENDPOINTS } from '../utils/config';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

interface QueryResult {
  id: string;
  query: string;
  cypher: string;
  result: any[];
  execution_time: number;
  timestamp: string;
  status: 'success' | 'error';
  error_message?: string;
}

interface QueryHistory {
  id: string;
  query: string;
  timestamp: string;
  success: boolean;
}

interface QuerySuggestion {
  id: string;
  text: string;
  category: string;
}

interface CodeExecutionResult {
  id: string;
  code: string;
  output: string;
  error?: string;
  execution_time: number;
  timestamp: string;
  status: 'success' | 'error';
}

const QueryPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('query');
  const [queryInput, setQueryInput] = useState('');
  const [codeInput, setCodeInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [codeLoading, setCodeLoading] = useState(false);
  const [queryResults, setQueryResults] = useState<QueryResult | null>(null);
  const [codeResults, setCodeResults] = useState<CodeExecutionResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [suggestions, setSuggestions] = useState<QuerySuggestion[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState('default');
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [maxResults, setMaxResults] = useState(50);
  const [queryComplexity, setQueryComplexity] = useState<{
    level: 'low' | 'medium' | 'high';
    explanation: string;
  } | null>(null);
  
  // 引用
  const queryInputRef = useRef<HTMLTextAreaElement>(null);
  const codeInputRef = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  // 加载查询历史
  useEffect(() => {
    fetchQueryHistory();
    fetchQuerySuggestions();
  }, []);

  // 获取查询历史
  const fetchQueryHistory = async () => {
    try {
      // 这里应该调用真实的API
      // const response = await axios.get(API_ENDPOINTS.QUERY.HISTORY);
      // setQueryHistory(response.data);
      
      // 模拟数据
      setTimeout(() => {
        const mockHistory: QueryHistory[] = [
          {
            id: 'h1',
            query: '查询所有与人工智能相关的技术',
            timestamp: '2023-12-01T10:30:00Z',
            success: true,
          },
          {
            id: 'h2',
            query: '找出所有研究人员及其研究领域',
            timestamp: '2023-11-30T16:45:00Z',
            success: true,
          },
          {
            id: 'h3',
            query: '统计不同类型的实体数量',
            timestamp: '2023-11-29T14:20:00Z',
            success: true,
          },
        ];
        setQueryHistory(mockHistory);
      }, 500);
    } catch (error) {
      console.error('获取查询历史失败:', error);
    }
  };

  // 获取查询建议
  const fetchQuerySuggestions = async () => {
    try {
      // 这里应该调用真实的API
      // const response = await axios.get(API_ENDPOINTS.QUERY.SUGGESTIONS);
      // setSuggestions(response.data);
      
      // 模拟数据
      setTimeout(() => {
        const mockSuggestions: QuerySuggestion[] = [
          { id: 's1', text: '查询最近添加的文档', category: '文档' },
          { id: 's2', text: '统计知识图谱中的实体数量', category: '统计' },
          { id: 's3', text: '找出特定实体的所有关联实体', category: '关系' },
          { id: 's4', text: '分析实体类型分布', category: '分析' },
          { id: 's5', text: '查询处理失败的文档', category: '文档' },
        ];
        setSuggestions(mockSuggestions);
      }, 500);
    } catch (error) {
      console.error('获取查询建议失败:', error);
    }
  };

  // 处理自然语言查询
  const handleQuery = async () => {
    if (!queryInput.trim()) {
      message.warning('请输入查询内容');
      return;
    }
    
    try {
      setLoading(true);
      // 调用API进行查询分析
      // const response = await axios.post(API_ENDPOINTS.QUERY.ANALYZE, {
      //   query: queryInput,
      //   database: selectedDatabase,
      //   max_results: maxResults,
      // });
      // setQueryResults(response.data);
      
      // 模拟查询过程
      setTimeout(() => {
        // 分析查询复杂度
        const complexity = analyzeQueryComplexity(queryInput);
        setQueryComplexity(complexity);
        
        // 模拟查询结果
        const mockResult: QueryResult = {
          id: `q_${Date.now()}`,
          query: queryInput,
          cypher: `MATCH (n) WHERE n.type CONTAINS '${queryInput.split(' ')[0]}' RETURN n LIMIT ${maxResults}`,
          result: [
            { id: '1', name: '人工智能', type: 'technology', properties: { description: '计算机科学的分支' } },
            { id: '2', name: '机器学习', type: 'algorithm', properties: { description: '人工智能的子集' } },
            { id: '3', name: '深度学习', type: 'algorithm', properties: { description: '机器学习的子集' } },
          ],
          execution_time: 45.6,
          timestamp: new Date().toISOString(),
          status: 'success',
        };
        
        setQueryResults(mockResult);
        
        // 添加到查询历史
        const newHistoryItem: QueryHistory = {
          id: `h_${Date.now()}`,
          query: queryInput,
          timestamp: new Date().toISOString(),
          success: true,
        };
        setQueryHistory(prev => [newHistoryItem, ...prev].slice(0, 10)); // 只保留最近10条
        
        setLoading(false);
        
        // 滚动到结果区域
        if (resultRef.current) {
          resultRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 2000);
    } catch (error) {
      console.error('查询失败:', error);
      message.error('查询处理失败，请稍后重试');
      setLoading(false);
    }
  };

  // 处理代码执行
  const handleCodeExecute = async () => {
    if (!codeInput.trim()) {
      message.warning('请输入要执行的代码');
      return;
    }
    
    try {
      setCodeLoading(true);
      // 调用API执行代码
      // const response = await axios.post(API_ENDPOINTS.QUERY.EXECUTE_CODE, {
      //   code: codeInput,
      // });
      // setCodeResults(response.data);
      
      // 模拟代码执行
      setTimeout(() => {
        // 简单模拟代码执行逻辑
        let output = '';
        let status: 'success' | 'error' = 'success';
        let error: string | undefined;
        
        if (codeInput.includes('error') || codeInput.includes('Exception')) {
          status = 'error';
          error = '执行错误: 代码中包含错误语句';
          output = 'Traceback (most recent call last):\n  File "<stdin>", line 1\nRuntimeError: 模拟的错误';
        } else if (codeInput.includes('import')) {
          output = '已成功导入依赖包\n模拟代码执行中...\n分析完成!';
        } else if (codeInput.includes('print')) {
          output = 'Hello, Knowledge Graph!\n这是一个模拟的输出';
        } else {
          output = '代码执行成功，这是模拟的输出结果\n数据分析完成\n结果已生成';
        }
        
        const mockCodeResult: CodeExecutionResult = {
          id: `code_${Date.now()}`,
          code: codeInput,
          output,
          error,
          execution_time: 123.4,
          timestamp: new Date().toISOString(),
          status,
        };
        
        setCodeResults(mockCodeResult);
        setCodeLoading(false);
        
        // 滚动到结果区域
        if (resultRef.current) {
          resultRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 2500);
    } catch (error) {
      console.error('代码执行失败:', error);
      message.error('代码执行失败，请稍后重试');
      setCodeLoading(false);
    }
  };

  // 分析查询复杂度（简单实现）
  const analyzeQueryComplexity = (query: string): { level: 'low' | 'medium' | 'high'; explanation: string } => {
    const queryLength = query.length;
    const wordCount = query.split(' ').length;
    
    if (queryLength < 20 && wordCount < 5) {
      return {
        level: 'low',
        explanation: '查询语句简短直接，复杂度低',
      };
    } else if (queryLength < 50 && wordCount < 10) {
      return {
        level: 'medium',
        explanation: '查询语句包含多个条件，复杂度中等',
      };
    } else {
      return {
        level: 'high',
        explanation: '查询语句较长且复杂，可能需要更复杂的处理',
      };
    }
  };

  // 使用查询建议
  const useSuggestion = (suggestion: QuerySuggestion) => {
    setQueryInput(suggestion.text);
    if (activeTab !== 'query') {
      setActiveTab('query');
    }
    // 聚焦到输入框
    setTimeout(() => {
      queryInputRef.current?.focus();
    }, 100);
  };

  // 使用历史查询
  const useHistoryQuery = (history: QueryHistory) => {
    setQueryInput(history.query);
    if (activeTab !== 'query') {
      setActiveTab('query');
    }
    // 聚焦到输入框
    setTimeout(() => {
      queryInputRef.current?.focus();
    }, 100);
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 复制查询结果
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => message.success('已复制到剪贴板'))
      .catch(() => message.error('复制失败'));
  };

  // 保存查询结果
  const saveQueryResult = () => {
    if (!queryResults) return;
    
    // 这里可以实现保存查询结果的功能
    message.info('保存功能开发中');
  };

  // 格式化代码输出
  const formatCodeOutput = (output: string) => {
    return output.split('\n').map((line, index) => (
      <div key={index} className="code-line">{line}</div>
    ));
  };

  // 获取复杂度标签颜色
  const getComplexityColor = (level: string) => {
    switch (level) {
      case 'low': return 'green';
      case 'medium': return 'orange';
      case 'high': return 'red';
      default: return 'default';
    }
  };

  return (
    <div className="query-page" style={{ padding: '20px' }}>
      <Card title="智能查询分析" style={{ marginBottom: '20px' }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab={<span><DatabaseOutlined /> 自然语言查询</span>} key="query">
            <div style={{ marginBottom: '16px' }}>
              <TextArea
                ref={queryInputRef}
                rows={4}
                placeholder="输入您的查询，例如：查询所有与人工智能相关的技术实体"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleQuery();
                  }
                }}
                style={{ resize: 'vertical' }}
              />
              <Space style={{ marginTop: '12px' }}>
                <Button 
                  type="primary" 
                  icon={<SearchOutlined />}
                  onClick={handleQuery}
                  loading={loading}
                >
                  执行查询
                </Button>
                <Button 
                  icon={<RefreshOutlined />}
                  onClick={() => {
                    setQueryInput('');
                    setQueryResults(null);
                    setQueryComplexity(null);
                    queryInputRef.current?.focus();
                  }}
                >
                  清空
                </Button>
                <Button 
                  icon={<HelpOutlined />}
                  onClick={() => message.info('查询帮助：请使用自然语言描述您想要查询的内容')}
                >
                  帮助
                </Button>
              </Space>
            </div>
            
            {/* 查询复杂度分析 */}
            {queryComplexity && (
              <Card size="small" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>查询复杂度分析:</strong> 
                    <Tag color={getComplexityColor(queryComplexity.level)}>
                      {queryComplexity.level === 'low' ? '低' : 
                       queryComplexity.level === 'medium' ? '中' : '高'}
                    </Tag>
                  </div>
                  <Text type="secondary">{queryComplexity.explanation}</Text>
                </div>
              </Card>
            )}

            {/* 查询结果 */}
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin size="large" tip="正在处理查询..." />
              </div>
            ) : queryResults ? (
              <div ref={resultRef}>
                {/* Cypher 查询语句 */}
                <Card title="生成的Cypher查询" size="small" style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <code style={{ fontSize: '14px', fontFamily: 'monospace' }}>{queryResults.cypher}</code>
                    <Button 
                      size="small" 
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(queryResults.cypher)}
                    />
                  </div>
                </Card>
                
                {/* 查询结果统计 */}
                <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic 
                        title="结果数量" 
                        value={queryResults.result.length} 
                        suffix="条" 
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic 
                        title="执行时间" 
                        value={queryResults.execution_time} 
                        precision={2}
                        suffix="ms" 
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic 
                        title="状态" 
                        value={queryResults.status === 'success' ? '成功' : '失败'} 
                        valueStyle={{ 
                          color: queryResults.status === 'success' ? '#3f8600' : '#cf1322' 
                        }} 
                      />
                    </Card>
                  </Col>
                </Row>
                
                {/* 查询结果列表 */}
                <Card title="查询结果" size="small">
                  {queryResults.result.length > 0 ? (
                    <Table
                      dataSource={queryResults.result}
                      rowKey="id"
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                      }}
                      scroll={{ x: 'max-content' }}
                      columns={[
                        {
                          title: 'ID',
                          dataIndex: 'id',
                          key: 'id',
                          width: 80,
                        },
                        {
                          title: '名称',
                          dataIndex: 'name',
                          key: 'name',
                          render: (name: string) => <strong>{name}</strong>,
                        },
                        {
                          title: '类型',
                          dataIndex: 'type',
                          key: 'type',
                          render: (type: string) => <Tag color="blue">{type}</Tag>,
                        },
                        {
                          title: '属性',
                          dataIndex: 'properties',
                          key: 'properties',
                          render: (properties: any) => (
                            <Collapse defaultActiveKey={[]}>
                              {Object.entries(properties || {}).map(([key, value]) => (
                                <Panel header={key} key={key}>
                                  {typeof value === 'object' ? JSON.stringify(value) : value}
                                </Panel>
                              ))}
                            </Collapse>
                          ),
                        },
                        {
                          title: '操作',
                          key: 'action',
                          render: (_, record) => (
                            <Button 
                              size="small" 
                              onClick={() => {
                                navigate(`/graph?entity_id=${record.id}`);
                              }}
                            >
                              查看图谱
                            </Button>
                          ),
                        },
                      ]}
                    />
                  ) : (
                    <Empty description="未找到匹配结果" />
                  )}
                </Card>
                
                {/* 操作按钮 */}
                <Space style={{ marginTop: '16px' }}>
                  <Button icon={<SaveOutlined />} onClick={saveQueryResult}>保存结果</Button>
                  <Button 
                    icon={<CopyOutlined />} 
                    onClick={() => copyToClipboard(JSON.stringify(queryResults.result, null, 2))}
                  >
                    复制所有结果
                  </Button>
                </Space>
              </div>
            ) : null}
          </TabPane>
          
          <TabPane tab={<span><CodeOutlined /> 代码执行器</span>} key="code">
            <div style={{ marginBottom: '16px' }}>
              <TextArea
                ref={codeInputRef}
                rows={8}
                placeholder="输入Python代码进行数据处理和分析，例如：import pandas as pd\ndata = pd.DataFrame(results)\ndata.describe()"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleCodeExecute();
                  }
                }}
                style={{ resize: 'vertical', fontFamily: 'monospace' }}
              />
              <Space style={{ marginTop: '12px' }}>
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />}
                  onClick={handleCodeExecute}
                  loading={codeLoading}
                >
                  执行代码
                </Button>
                <Button 
                  icon={<RefreshOutlined />}
                  onClick={() => {
                    setCodeInput('');
                    setCodeResults(null);
                    codeInputRef.current?.focus();
                  }}
                >
                  清空
                </Button>
                <Button 
                  icon={<HelpOutlined />}
                  onClick={() => message.info('支持标准Python库，结果会在下方显示')}
                >
                  帮助
                </Button>
              </Space>
            </div>
            
            {/* 代码执行结果 */}
            {codeLoading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin size="large" tip="正在执行代码..." />
              </div>
            ) : codeResults ? (
              <div ref={resultRef}>
                <Card title="执行结果" size="small">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div>
                      <Tag color={codeResults.status === 'success' ? 'green' : 'red'}>
                        {codeResults.status === 'success' ? '执行成功' : '执行失败'}
                      </Tag>
                      <Text type="secondary" style={{ marginLeft: '8px' }}>
                        耗时: {codeResults.execution_time}ms
                      </Text>
                    </div>
                    <Button 
                      size="small" 
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(codeResults.output)}
                    />
                  </div>
                  
                  <div style={{ 
                    backgroundColor: '#f6f8fa', 
                    padding: '16px', 
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    maxHeight: '400px',
                    overflow: 'auto',
                  }}>
                    {codeResults.output}
                  </div>
                  
                  {codeResults.error && (
                    <div style={{ 
                      marginTop: '16px',
                      backgroundColor: '#fff1f0', 
                      padding: '16px', 
                      borderRadius: '4px',
                      borderLeft: '4px solid #ff4d4f',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                        <AlertCircleOutlined style={{ color: '#ff4d4f', marginRight: '8px' }} />
                        <strong>错误信息:</strong>
                      </div>
                      <div style={{ 
                        fontFamily: 'monospace',
                        fontSize: '14px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all',
                      }}>
                        {codeResults.error}
                      </div>
                    </div>
                  )}
                </Card>
              </div>
            ) : null}
          </TabPane>
        </Tabs>
      </Card>
      
      <Row gutter={[20, 20]}>
        {/* 查询建议 */}
        <Col xs={24} md={12}>
          <Card title="查询建议" size="small">
            {suggestions.length > 0 ? (
              <div className="suggestions-list">
                {suggestions.map(suggestion => (
                  <div 
                    key={suggestion.id}
                    className="suggestion-item"
                    onClick={() => useSuggestion(suggestion)}
                    style={{
                      padding: '12px',
                      border: '1px solid #f0f0f0',
                      borderRadius: '4px',
                      marginBottom: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <BrainOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                        <span>{suggestion.text}</span>
                      </div>
                      <Tag color="default">{suggestion.category}</Tag>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无查询建议" />
            )}
          </Card>
        </Col>
        
        {/* 查询历史 */}
        <Col xs={24} md={12}>
          <Card title="查询历史" size="small">
            {queryHistory.length > 0 ? (
              <div className="history-list">
                {queryHistory.map(history => (
                  <div 
                    key={history.id}
                    className="history-item"
                    onClick={() => useHistoryQuery(history)}
                    style={{
                      padding: '12px',
                      border: '1px solid #f0f0f0',
                      borderRadius: '4px',
                      marginBottom: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', maxWidth: '80%' }}>
                        <HistoryOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {history.query}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        {history.success ? (
                          <CheckOutlined style={{ color: '#52c41a', marginRight: '4px' }} />
                        ) : (
                          <AlertCircleOutlined style={{ color: '#ff4d4f', marginRight: '4px' }} />
                        )}
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {formatDate(history.timestamp)}
                        </Text>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无查询历史" />
            )}
          </Card>
        </Col>
      </Row>
      
      {/* 设置模态框 */}
      <Modal
        title="查询设置"
        open={settingsModalVisible}
        onCancel={() => setSettingsModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setSettingsModalVisible(false)}>取消</Button>,
          <Button key="confirm" type="primary" onClick={() => setSettingsModalVisible(false)}>确定</Button>,
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="最大结果数量">
            <Slider 
              min={10} 
              max={500} 
              value={maxResults}
              onChange={setMaxResults}
              marks={{
                10: '10',
                100: '100',
                200: '200',
                300: '300',
                400: '400',
                500: '500',
              }}
            />
            <Text type="secondary" style={{ marginLeft: '16px' }}>{maxResults}</Text>
          </Form.Item>
          
          <Form.Item label="数据库选择">
            <Select 
              value={selectedDatabase} 
              onChange={setSelectedDatabase}
              style={{ width: '100%' }}
            >
              <Option value="default">默认数据库</Option>
              <Option value="archive">归档数据库</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QueryPage;