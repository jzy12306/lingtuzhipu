import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Upload,
  Table,
  Tag,
  Space,
  Modal,
  message,
  Spin,
  Typography,
  Input,
  Select,
  Empty,
  Progress,
  Dropdown,
  Menu,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
  EditOutlined,
  ReloadOutlined,
  MoreOutlined,
  SearchOutlined,
  CalendarOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import type { TableColumnsType } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_ENDPOINTS, APP_CONFIG } from '../utils/config';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface Document {
  id: string;
  title: string;
  filename: string;
  type: string;
  size: number;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  entities: number;
  relationships: number;
  created_at: string;
  updated_at: string;
  uploaded_by: string;
}

const DocumentManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [currentDoc, setCurrentDoc] = useState<Document | null>(null);
  const [processingDoc, setProcessingDoc] = useState<string | null>(null);
  
  // 上传进度引用
  const uploadProgressRef = useRef<{ [key: string]: number }>({});
  const [batchProcessing, setBatchProcessing] = useState(false);

  // 获取文档列表
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      // 这里应该调用API获取真实数据
      // const response = await axios.get(API_ENDPOINTS.DOCUMENTS.LIST);
      // setDocuments(response.data);
      
      // 模拟数据
      setTimeout(() => {
        const mockDocs: Document[] = [
          {
            id: '1',
            title: '技术白皮书',
            filename: 'tech_whitepaper.pdf',
            type: 'pdf',
            size: 2048576,
            status: 'processed',
            entities: 456,
            relationships: 234,
            created_at: '2023-12-01T10:30:00Z',
            updated_at: '2023-12-01T10:45:00Z',
            uploaded_by: user?.username || 'admin',
          },
          {
            id: '2',
            title: '市场调研报告',
            filename: 'market_research.docx',
            type: 'docx',
            size: 1048576,
            status: 'processing',
            entities: 0,
            relationships: 0,
            created_at: '2023-12-01T09:15:00Z',
            updated_at: '2023-12-01T09:15:00Z',
            uploaded_by: user?.username || 'admin',
          },
          {
            id: '3',
            title: '数据分析报告',
            filename: 'data_analysis.md',
            type: 'md',
            size: 524288,
            status: 'processed',
            entities: 128,
            relationships: 64,
            created_at: '2023-11-30T16:45:00Z',
            updated_at: '2023-11-30T16:50:00Z',
            uploaded_by: 'system',
          },
          {
            id: '4',
            title: '产品规格说明书',
            filename: 'product_spec.txt',
            type: 'txt',
            size: 262144,
            status: 'failed',
            entities: 0,
            relationships: 0,
            created_at: '2023-11-30T14:20:00Z',
            updated_at: '2023-11-30T14:25:00Z',
            uploaded_by: user?.username || 'admin',
          },
          {
            id: '5',
            title: '客户反馈汇总',
            filename: 'customer_feedback.csv',
            type: 'csv',
            size: 786432,
            status: 'processed',
            entities: 210,
            relationships: 95,
            created_at: '2023-11-29T11:05:00Z',
            updated_at: '2023-11-29T11:10:00Z',
            uploaded_by: 'system',
          },
        ];
        setDocuments(mockDocs);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('获取文档列表失败:', error);
      message.error('获取文档列表失败，请稍后重试');
      setLoading(false);
    }
  };

  // 组件加载时获取文档列表
  useEffect(() => {
    fetchDocuments();
  }, [user]);

  // 处理文件上传
  const handleUpload = async (file: any) => {
    return new Promise((resolve, reject) => {
      // 创建FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
      
      // 开始上传
      uploadProgressRef.current[file.uid] = 0;
      setUploading(true);
      
      // 这里应该调用真实的上传API
      // const config = {
      //   headers: {
      //     'Content-Type': 'multipart/form-data',
      //   },
      //   onUploadProgress: (progressEvent: any) => {
      //     if (progressEvent.total) {
      //       const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      //       uploadProgressRef.current[file.uid] = percentCompleted;
      //     }
      //   },
      // };
      
      // axios.post(API_ENDPOINTS.DOCUMENTS.CREATE, formData, config)
      //   .then((response) => {
      //     message.success('文件上传成功');
      //     fetchDocuments();
      //     resolve(response.data);
      //   })
      //   .catch((error) => {
      //     message.error('文件上传失败');
      //     reject(error);
      //   })
      //   .finally(() => {
      //     setUploading(false);
      //   });
      
      // 模拟上传过程
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        uploadProgressRef.current[file.uid] = progress;
        
        if (progress >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            message.success('文件上传成功');
            fetchDocuments();
            setUploading(false);
            resolve({ status: 'success' });
          }, 500);
        }
      }, 200);
    });
  };

  // 处理文档处理
  const handleProcessDocument = async (docId: string) => {
    try {
      setProcessingDoc(docId);
      // 调用API处理文档
      // await axios.post(API_ENDPOINTS.DOCUMENTS.PROCESS(docId));
      
      // 模拟处理过程
      setTimeout(() => {
        message.success('文档处理成功');
        fetchDocuments();
        setProcessingDoc(null);
      }, 2000);
    } catch (error) {
      console.error('处理文档失败:', error);
      message.error('处理文档失败，请稍后重试');
      setProcessingDoc(null);
    }
  };

  // 批量处理文档
  const handleBatchProcess = async () => {
    if (selectedDocs.length === 0) {
      message.warning('请先选择要处理的文档');
      return;
    }
    
    try {
      setBatchProcessing(true);
      // 调用批量处理API
      // await axios.post(API_ENDPOINTS.DOCUMENTS.BATCH_PROCESS, { ids: selectedDocs });
      
      // 模拟批量处理
      setTimeout(() => {
        message.success(`成功处理 ${selectedDocs.length} 个文档`);
        fetchDocuments();
        setSelectedDocs([]);
        setBatchProcessing(false);
      }, 3000);
    } catch (error) {
      console.error('批量处理文档失败:', error);
      message.error('批量处理文档失败，请稍后重试');
      setBatchProcessing(false);
    }
  };

  // 删除文档
  const handleDeleteDocument = async (docId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文档吗？此操作不可撤销。',
      onOk: async () => {
        try {
          // 调用API删除文档
          // await axios.delete(API_ENDPOINTS.DOCUMENTS.DELETE(docId));
          
          // 模拟删除
          message.success('文档删除成功');
          fetchDocuments();
        } catch (error) {
          console.error('删除文档失败:', error);
          message.error('删除文档失败，请稍后重试');
        }
      },
    });
  };

  // 批量删除文档
  const handleBatchDelete = async () => {
    if (selectedDocs.length === 0) {
      message.warning('请先选择要删除的文档');
      return;
    }
    
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedDocs.length} 个文档吗？此操作不可撤销。`,
      onOk: async () => {
        try {
          // 调用批量删除API
          // await axios.post(API_ENDPOINTS.DOCUMENTS.BATCH_DELETE, { ids: selectedDocs });
          
          // 模拟批量删除
          message.success(`成功删除 ${selectedDocs.length} 个文档`);
          fetchDocuments();
          setSelectedDocs([]);
        } catch (error) {
          console.error('批量删除文档失败:', error);
          message.error('批量删除文档失败，请稍后重试');
        }
      },
    });
  };

  // 查看文档详情
  const handleViewDocument = (doc: Document) => {
    setCurrentDoc(doc);
    setViewModalVisible(true);
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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

  // 获取状态标签
  const getStatusTag = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <Tag color="default">已上传</Tag>;
      case 'processing':
        return <Tag color="processing">处理中</Tag>;
      case 'processed':
        return <Tag color="success">已处理</Tag>;
      case 'failed':
        return <Tag color="error">失败</Tag>;
      default:
        return <Tag color="default">未知</Tag>;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      case 'processing':
        return <Spin size="small" style={{ color: '#1890ff' }} />;
      case 'processed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      default:
        return null;
    }
  };

  // 筛选文档
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 表格列配置
  const columns: TableColumnsType<Document> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title, record) => (
        <Space>
          <FileTextOutlined />
          <span>{title}</span>
        </Space>
      ),
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="blue">.{type}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Space>
          {getStatusIcon(status)}
          {getStatusTag(status)}
        </Space>
      ),
    },
    {
      title: '实体',
      dataIndex: 'entities',
      key: 'entities',
    },
    {
      title: '关系',
      dataIndex: 'relationships',
      key: 'relationships',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => formatDate(date),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => handleViewDocument(record)}
          />
          {(record.status === 'uploaded' || record.status === 'failed') && (
            <Button 
              type="link" 
              icon={<ReloadOutlined />} 
              onClick={() => handleProcessDocument(record.id)}
              loading={processingDoc === record.id}
            />
          )}
          <Dropdown
            menu={{
              items: [
                {
                  key: '1',
                  label: '编辑',
                  icon: <EditOutlined />,
                  onClick: () => message.info('编辑功能暂未实现'),
                },
                {
                  key: '2',
                  label: '删除',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDeleteDocument(record.id),
                },
                {
                  key: '3',
                  label: '查看知识图谱',
                  onClick: () => navigate(`/graph?doc_id=${record.id}`),
                },
              ],
            }}
          >
            <Button type="link" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 文件上传配置
  const uploadProps = {
    name: 'file',
    customRequest: ({ file, onSuccess }) => {
      handleUpload(file).then(() => {
        onSuccess?.(null, file);
      });
    },
    listType: 'picture-card',
    accept: APP_CONFIG.FILE_UPLOAD.ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(','),
    beforeUpload: (file) => {
      // 检查文件大小
      if (file.size > APP_CONFIG.FILE_UPLOAD.MAX_SIZE) {
        message.error(`${file.name} 文件大小超过限制 (最大 ${APP_CONFIG.FILE_UPLOAD.MAX_SIZE / 1024 / 1024}MB)`);
        return Upload.LIST_IGNORE;
      }
      // 检查文件类型
      const isValidType = APP_CONFIG.FILE_UPLOAD.ALLOWED_EXTENSIONS.some(ext => 
        file.name.toLowerCase().endsWith(ext)
      );
      if (!isValidType) {
        message.error(`不支持的文件类型，仅支持: ${APP_CONFIG.FILE_UPLOAD.ALLOWED_EXTENSIONS.join(', ')}`);
        return Upload.LIST_IGNORE;
      }
      return true;
    },
    showUploadList: true,
    multiple: true,
    disabled: uploading || batchProcessing,
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={4} style={{ margin: 0 }}>文档管理</Title>
        
        {/* 批量操作按钮 */}
        {selectedDocs.length > 0 && (
          <Space>
            <Button 
              onClick={handleBatchProcess}
              loading={batchProcessing}
              disabled={batchProcessing}
            >
              批量处理 ({selectedDocs.length})
            </Button>
            <Button 
              danger 
              onClick={handleBatchDelete}
              disabled={batchProcessing}
            >
              批量删除 ({selectedDocs.length})
            </Button>
          </Space>
        )}
      </div>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Search
              placeholder="搜索文档标题或文件名"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </Col>
          <Col xs={24} md={12}>
            <Space size="middle" style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button type="primary" icon={<FilterOutlined />}>高级筛选</Button>
              <Upload {...uploadProps}>
                <div>
                  <PlusOutlined />
                  <div style={{ marginTop: 8 }}>上传文档</div>
                </div>
              </Upload>
            </Space>
          </Col>
          <Col xs={24} md={24}>
            <Space size="middle">
              <Text>状态筛选:</Text>
              <Select 
                value={statusFilter} 
                onChange={setStatusFilter}
                style={{ width: 120 }}
              >
                <Option value="all">全部</Option>
                <Option value="uploaded">已上传</Option>
                <Option value="processing">处理中</Option>
                <Option value="processed">已处理</Option>
                <Option value="failed">失败</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 文档列表 */}
      <Table
        rowKey="id"
        columns={columns}
        dataSource={filteredDocuments}
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
        }}
        rowSelection={{
          onChange: (selectedRowKeys) => {
            setSelectedDocs(selectedRowKeys as string[]);
          },
        }}
        locale={{
          emptyText: (
            <Empty
              description="暂无文档"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              actions={
                <Button type="primary" icon={<UploadOutlined />} onClick={() => {}}>
                  上传文档
                </Button>
              }
            />
          ),
        }}
      />

      {/* 文档详情模态框 */}
      <Modal
        title="文档详情"
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>关闭</Button>,
          {currentDoc && (currentDoc.status === 'uploaded' || currentDoc.status === 'failed') && (
            <Button 
              key="process" 
              type="primary" 
              onClick={() => {
                handleProcessDocument(currentDoc.id);
                setViewModalVisible(false);
              }}
              loading={processingDoc === currentDoc.id}
            >
              处理文档
            </Button>
          )},
        ]}
      >
        {currentDoc && (
          <div>
            <Title level={5}>{currentDoc.title}</Title>
            <Divider />
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space justify="space-between">
                <Text>文件名:</Text>
                <Text strong>{currentDoc.filename}</Text>
              </Space>
              <Space justify="space-between">
                <Text>文件类型:</Text>
                <Tag color="blue">.{currentDoc.type}</Tag>
              </Space>
              <Space justify="space-between">
                <Text>文件大小:</Text>
                <Text>{formatFileSize(currentDoc.size)}</Text>
              </Space>
              <Space justify="space-between">
                <Text>状态:</Text>
                <Space>
                  {getStatusIcon(currentDoc.status)}
                  {getStatusTag(currentDoc.status)}
                </Space>
              </Space>
              <Space justify="space-between">
                <Text>提取的实体:</Text>
                <Text>{currentDoc.entities}</Text>
              </Space>
              <Space justify="space-between">
                <Text>提取的关系:</Text>
                <Text>{currentDoc.relationships}</Text>
              </Space>
              <Space justify="space-between">
                <Text>创建时间:</Text>
                <Text>{formatDate(currentDoc.created_at)}</Text>
              </Space>
              <Space justify="space-between">
                <Text>最后更新:</Text>
                <Text>{formatDate(currentDoc.updated_at)}</Text>
              </Space>
              <Space justify="space-between">
                <Text>上传者:</Text>
                <Text>{currentDoc.uploaded_by}</Text>
              </Space>
            </Space>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DocumentManagementPage;