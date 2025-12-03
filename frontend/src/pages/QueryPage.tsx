import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface QueryMessage {
  id: string;
  text: string;
  type: 'user' | 'assistant';
  timestamp: Date;
}

const QueryPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<QueryMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: QueryMessage = {
      id: Math.random().toString(36).substr(2, 9),
      text: query,
      type: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    // 模拟API调用
    setTimeout(() => {
      const assistantMessage: QueryMessage = {
        id: Math.random().toString(36).substr(2, 9),
        text: '这是模拟的回答。在实际应用中，这里会调用后端API获取知识图谱查询结果。',
        type: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          智能问答
        </Typography>
        <Typography variant="body1" color="text.secondary">
          基于知识图谱的智能查询系统
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                对话记录
              </Typography>
              <Box sx={{ 
                height: 400, 
                overflowY: 'auto', 
                border: '1px solid #e0e0e0', 
                borderRadius: 1, 
                p: 2, 
                mb: 2 
              }}>
                {messages.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 8 }}>
                    请输入您的问题开始对话
                  </Typography>
                ) : (
                  <List>
                    {messages.map((message) => (
                      <ListItem key={message.id} sx={{ px: 0 }}>
                        <Box sx={{ width: '100%' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Chip 
                              label={message.type === 'user' ? '用户' : '助手'} 
                              color={message.type === 'user' ? 'primary' : 'secondary'}
                              size="small"
                            />
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              {message.timestamp.toLocaleTimeString()}
                            </Typography>
                          </Box>
                          <Typography variant="body1">
                            {message.text}
                          </Typography>
                        </Box>
                      </ListItem>
                    ))}
                    {isLoading && (
                      <ListItem sx={{ px: 0 }}>
                        <Box sx={{ width: '100%' }}>
                          <Chip label="助手" color="secondary" size="small" />
                          <Typography variant="body1" sx={{ mt: 1 }}>
                            正在思考...
                          </Typography>
                        </Box>
                      </ListItem>
                    )}
                  </List>
                )}
              </Box>
              
              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  variant="outlined"
                  placeholder="请输入您的问题..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isLoading}
                  sx={{ mb: 2 }}
                />
                <Button
                  type="submit"
                  variant="contained"
                  endIcon={<SendIcon />}
                  disabled={!query.trim() || isLoading}
                  fullWidth
                >
                  发送问题
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                查询提示
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                您可以询问关于知识图谱中的实体、关系、属性等信息。
              </Typography>
              <Typography variant="body2" color="text.secondary">
                例如：
              </Typography>
              <Box component="ul" sx={{ mt: 1 }}>
                <li><Typography variant="body2">某个实体的相关信息</Typography></li>
                <li><Typography variant="body2">两个实体之间的关系</Typography></li>
                <li><Typography variant="body2">特定类型的知识节点</Typography></li>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default QueryPage;