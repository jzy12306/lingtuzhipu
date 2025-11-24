import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  List,
  Button,
  Avatar,
  Progress,
  Tag,
  Space,
  Spin,
  message,
} from 'antd';
import {
  FileTextOutlined,
  DatabaseOutlined,
  UserOutlined,
  MessageOutlined,
  BarChartOutlined,
  LineChartOutlined,
  BellOutlined,
  FileAddOutlined,
  SearchOutlined,
  CodeOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { API_ENDPOINTS } from '../utils/config';

const { Title, Text, Paragraph } = Typography;

interface StatisticCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  onClick?: () => void;
}

// 统计卡片组件
const StatisticCard: React.FC<StatisticCardProps> = ({
  title,
  value,
  icon,
  color,
  trend,
  trendValue,
  onClick,
}) => {
  return (
    <Card 
      hoverable 
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <Text type="secondary">{title}</Text>
        <div style={{ color, fontSize: '20px' }}>{icon}</div>
      </div>
      <Statistic 
        value={value} 
        valueStyle={{ color }} 
        suffix={
          trend && trendValue !== undefined ? (
            <div style={{ fontSize: '12px', color: trend === 'up' ? '#f5222d' : trend === 'down' ? '#52c41a' : '#8c8c8c' }}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}%
            </div>
          ) : null
        }
      />
    </Card>
  );
};

// 快速操作卡片组件
const QuickActionCard: React.FC<{
  title: string;
  icon: React.ReactNode;
  description: string;
  color: string;
  onClick: () => void;
}> = ({ title, icon, description, color, onClick }) => {
  return (
    <Card 
      hoverable 
      onClick={onClick}
      style={{ cursor: 'pointer', borderTop: `4px solid ${color}` }}
      bodyStyle={{ padding: '16px' }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ fontSize: '24px', color }}>{icon}</div>
        <div>
          <Title level={4} style={{ margin: 0, fontSize: '16px' }}>{title}</Title>
          <Text type="secondary" style={{ fontSize: '12px', lineHeight: 1.5 }}>{description}</Text>
        </div>
      </div>
    </Card>
  );
};

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    processedDocuments: 0,
    knowledgeEntities: 0,
    recentQueries: 0,
    processingRate: 0,
    querySuccessRate: 0,
  });
  
  // 最近活动数据
  const [recentActivities, setRecentActivities] = useState([
    { id: 1, type: 'document', title: '技术白皮书.pdf', action: '上传成功', time: '2分钟前', status: 'success' },
    { id: 2, type: 'query', title: '查询产品销售数据', action: '执行完成', time: '15分钟前', status: 'success' },
    { id: 3, type: 'document', title: '市场调研报告.docx', action: '处理中', time: '30分钟前', status: 'processing' },
    { id: 4, type: 'system', title: '系统更新', action: '完成', time: '2小时前', status: 'info' },
    { id: 5, type: 'query', title: '分析客户满意度趋势', action: '执行失败', time: '昨天', status: 'error' },
  ]);

  // 获取仪表盘数据
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // 这里应该调用API获取真实数据
        // const response = await axios.get(API_ENDPOINTS.DASHBOARD.DATA);
        // setStats(response.data);
        
        // 模拟数据
        setTimeout(() => {
          setStats({
            totalDocuments: 142,
            processedDocuments: 128,
            knowledgeEntities: 5642,
            recentQueries: 38,
            processingRate: 90.1,
            querySuccessRate: 95.3,
          });
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error('获取仪表盘数据失败:', error);
        message.error('获取数据失败，请稍后重试');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // 渲染活动项
  const renderActivityItem = (item: any) => {
    let icon = <FileTextOutlined />;
    let color = '#1890ff';
    let tagColor = 'blue';
    
    switch (item.type) {
      case 'query':
        icon = <SearchOutlined />;
        color = '#52c41a';
        break;
      case 'system':
        icon = <BellOutlined />;
        color = '#faad14';
        break;
      default:
        break;
    }
    
    switch (item.status) {
      case 'success':
        tagColor = 'success';
        break;
      case 'processing':
        tagColor = 'processing';
        break;
      case 'error':
        tagColor = 'error';
        break;
      case 'info':
        tagColor = 'default';
        break;
      default:
        break;
    }

    return (
      <List.Item
        key={item.id}
        actions={[<Tag color={tagColor}>{item.action}</Tag>, <Text type="secondary">{item.time}</Text>]}
      >
        <List.Item.Meta
          avatar={<Avatar style={{ color }}>{icon}</Avatar>}
          title={<span>{item.title}</span>}
        />
      </List.Item>
    );
  };

  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={4} style={{ margin: 0 }}>欢迎回来，{user?.profile?.full_name || user?.username}</Title>
        <Text type="secondary">这是您的仪表盘，概览系统的核心数据和活动</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <StatisticCard
            title="总文档数"
            value={stats.totalDocuments}
            icon={<FileTextOutlined />}
            color="#1890ff"
            trend="up"
            trendValue={12.5}
            onClick={() => navigate('/documents')}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatisticCard
            title="已处理文档"
            value={stats.processedDocuments}
            icon={<DatabaseOutlined />}
            color="#52c41a"
            trend="up"
            trendValue={8.3}
            onClick={() => navigate('/documents?status=processed')}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatisticCard
            title="知识实体"
            value={stats.knowledgeEntities}
            icon={<DatabaseOutlined />}
            color="#722ed1"
            trend="up"
            trendValue={15.2}
            onClick={() => navigate('/graph')}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatisticCard
            title="最近查询"
            value={stats.recentQueries}
            icon={<MessageOutlined />}
            color="#fa8c16"
            trend="down"
            trendValue={2.1}
            onClick={() => navigate('/query')}
          />
        </Col>
      </Row>

      {/* 性能指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} md={12}>
          <Card title="文档处理率" bodyStyle={{ padding: '16px' }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <Text>处理进度</Text>
                <Text strong>{stats.processingRate}%</Text>
              </div>
              <Progress percent={stats.processingRate} status="active" strokeColor="#52c41a" />
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {stats.processedDocuments}/{stats.totalDocuments} 文档已处理
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="查询成功率" bodyStyle={{ padding: '16px' }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <Text>成功比例</Text>
                <Text strong>{stats.querySuccessRate}%</Text>
              </div>
              <Progress percent={stats.querySuccessRate} status="active" strokeColor="#1890ff" />
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                基于最近 30 天的查询统计
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card title="快速操作" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <QuickActionCard
              title="上传文档"
              icon={<FileAddOutlined />}
              description="上传新文档并提取知识"
              color="#1890ff"
              onClick={() => navigate('/documents')}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <QuickActionCard
              title="执行查询"
              icon={<SearchOutlined />}
              description="使用自然语言查询知识图谱"
              color="#52c41a"
              onClick={() => navigate('/query')}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <QuickActionCard
              title="代码解释器"
              icon={<CodeOutlined />}
              description="使用代码分析和处理数据"
              color="#fa8c16"
              onClick={() => navigate('/query?tab=code')}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <QuickActionCard
              title="查看图谱"
              icon={<DatabaseOutlined />}
              description="可视化浏览知识图谱"
              color="#722ed1"
              onClick={() => navigate('/graph')}
            />
          </Col>
        </Row>
      </Card>

      {/* 最近活动 */}
      <Card title="最近活动" extra={<Button type="link">查看全部 <ArrowRightOutlined /></Button>}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin tip="加载中..." />
          </div>
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={recentActivities}
            renderItem={renderActivityItem}
          />
        )}
      </Card>
    </div>
  );
};

export default DashboardPage;