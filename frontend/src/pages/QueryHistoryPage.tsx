import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Divider, 
  Chip, 
  Paper, 
  IconButton,
  Tooltip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon
} from '@mui/icons-material';

interface QueryHistoryItem {
  id: string;
  query: string;
  result_summary: string;
  timestamp: string;
  complexity: string;
  execution_time: number;
}

const QueryHistoryPage: React.FC = () => {
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQueryHistory();
  }, []);

  const fetchQueryHistory = async () => {
    try {
      setLoading(true);
      // 这里应该调用后端API获取查询历史
      // 暂时使用模拟数据
      const mockData: QueryHistoryItem[] = [
        {
          id: '1',
          query: '查找人工智能的发展历程',
          result_summary: '找到了关于AI发展的重要节点和关键人物',
          timestamp: '2023-05-15T10:30:00Z',
          complexity: 'MODERATE',
          execution_time: 2.3
        },
        {
          id: '2',
          query: '分析机器学习算法的优缺点',
          result_summary: '比较了多种主流机器学习算法的特点',
          timestamp: '2023-05-14T14:20:00Z',
          complexity: 'HIGH',
          execution_time: 5.1
        }
      ];
      setHistory(mockData);
      setError(null);
    } catch (err) {
      setError('获取查询历史失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const deleteHistoryItem = async (id: string) => {
    try {
      // 这里应该调用后端API删除指定的历史记录
      setHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      setError('删除历史记录失败');
      console.error(err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'LOW': return 'success';
      case 'MODERATE': return 'warning';
      case 'HIGH': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">查询历史</Typography>
        <IconButton onClick={fetchQueryHistory} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Paper elevation={3}>
          <List>
            {history.map((item) => (
              <React.Fragment key={item.id}>
                <ListItem 
                  secondaryAction={
                    <Tooltip title="删除">
                      <IconButton 
                        edge="end" 
                        aria-label="delete"
                        onClick={() => deleteHistoryItem(item.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="h6">{item.query}</Typography>
                        <Chip 
                          label={item.complexity} 
                          color={getComplexityColor(item.complexity) as any} 
                          size="small" 
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          {item.result_summary}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                          <Typography variant="caption">
                            执行时间: {item.execution_time.toFixed(2)}秒
                          </Typography>
                          <Typography variant="caption">
                            {formatDate(item.timestamp)}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            ))}
          </List>
          
          {history.length === 0 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <SearchIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary">
                暂无查询历史
              </Typography>
              <Typography variant="body2" color="textSecondary">
                开始使用系统进行查询，历史记录将显示在这里
              </Typography>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default QueryHistoryPage;