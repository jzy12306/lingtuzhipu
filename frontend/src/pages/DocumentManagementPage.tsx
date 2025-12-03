import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Paper
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

const DocumentManagementPage: React.FC = () => {
  const [documents, setDocuments] = useState<Array<{id: string; name: string; uploadDate: string}>>([]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newDocs = Array.from(files).map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        uploadDate: new Date().toLocaleDateString()
      }));
      setDocuments([...documents, ...newDocs]);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          文档管理
        </Typography>
        <Typography variant="body1" color="text.secondary">
          上传和管理您的文档，支持多种格式
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                已上传文档
              </Typography>
              {documents.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  暂无文档，请上传文档开始构建知识图谱
                </Typography>
              ) : (
                <List>
                  {documents.map((doc) => (
                    <ListItem key={doc.id} disablePadding>
                      <ListItemButton>
                        <ListItemText
                          primary={doc.name}
                          secondary={`上传日期: ${doc.uploadDate}`}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                上传文档
              </Typography>
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <input
                  accept=".pdf,.doc,.docx,.txt"
                  style={{ display: 'none' }}
                  id="file-upload"
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="contained"
                    component="span"
                    startIcon={<UploadFileIcon />}
                    size="large"
                  >
                    选择文件
                  </Button>
                </label>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  支持 PDF、Word、文本文件
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DocumentManagementPage;