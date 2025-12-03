import React, { useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Grid
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

const GraphVisualizationPage: React.FC = () => {
  const graphContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 这里可以集成图表库如 D3.js, Cytoscape.js, 或 ECharts
    if (graphContainerRef.current) {
      // 示例：显示一个占位符
      graphContainerRef.current.innerHTML = `
        <div style="
          width: 100%;
          height: 500px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          border-radius: 8px;
          color: #666;
          font-size: 18px;
        ">
          知识图谱可视化区域<br/>
          <small>请上传文档以生成知识图谱</small>
        </div>
      `;
    }
  }, []);

  const handleRefreshGraph = () => {
    // 重新加载图谱数据
    console.log('刷新图谱');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            知识图谱可视化
          </Typography>
          <Typography variant="body1" color="text.secondary">
            交互式查看和管理知识图谱
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefreshGraph}
        >
          刷新图谱
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                知识图谱
              </Typography>
              <Box
                ref={graphContainerRef}
                sx={{
                  width: '100%',
                  minHeight: 500,
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  overflow: 'hidden'
                }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                图谱统计
              </Typography>
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="primary">
                  0
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  知识节点
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" color="secondary">
                  0
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  关系连接
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default GraphVisualizationPage;