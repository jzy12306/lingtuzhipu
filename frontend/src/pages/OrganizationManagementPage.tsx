import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

interface Organization {
  id: string;
  name: string;
  description: string;
  member_count: number;
  created_at: string;
  is_active: boolean;
}

const OrganizationManagementPage: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      // 模拟加载组织数据
      const mockData: Organization[] = [
        {
          id: '1',
          name: '研发部',
          description: '负责产品研发和技术研发',
          member_count: 25,
          created_at: '2023-01-15T00:00:00Z',
          is_active: true
        },
        {
          id: '2',
          name: '市场部',
          description: '负责市场推广和客户关系',
          member_count: 18,
          created_at: '2023-02-20T00:00:00Z',
          is_active: true
        }
      ];
      setOrganizations(mockData);
      setError(null);
    } catch (err) {
      setError('加载组织数据失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddOrg = () => {
    setEditingOrg(null);
    setOpenDialog(true);
  };

  const handleEditOrg = (org: Organization) => {
    setEditingOrg(org);
    setOpenDialog(true);
  };

  const handleDeleteOrg = async (orgId: string) => {
    try {
      // 这里应该调用后端API删除组织
      setOrganizations(prev => prev.filter(org => org.id !== orgId));
    } catch (err) {
      setError('删除组织失败');
      console.error(err);
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingOrg(null);
  };

  const handleSubmit = async () => {
    try {
      // 这里应该调用后端API保存组织信息
      handleCloseDialog();
    } catch (err) {
      setError('保存组织信息失败');
      console.error(err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">组织管理</Typography>
        <IconButton onClick={loadOrganizations} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">组织列表</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={handleAddOrg}
        >
          添加组织
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>组织名称</TableCell>
                  <TableCell>描述</TableCell>
                  <TableCell>成员数</TableCell>
                  <TableCell>创建时间</TableCell>
                  <TableCell>状态</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {organizations.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell>{org.name}</TableCell>
                    <TableCell>{org.description}</TableCell>
                    <TableCell>{org.member_count}</TableCell>
                    <TableCell>{formatDate(org.created_at)}</TableCell>
                    <TableCell>
                      <Chip 
                        label={org.is_active ? '激活' : '禁用'} 
                        color={org.is_active ? 'success' : 'default'} 
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="编辑">
                        <IconButton onClick={() => handleEditOrg(org)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="删除">
                        <IconButton onClick={() => handleDeleteOrg(org.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            {organizations.length === 0 && (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="textSecondary">
                  暂无组织数据
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  点击"添加组织"按钮创建新的组织
                </Typography>
              </Box>
            )}
          </TableContainer>
        </Paper>
      )}

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingOrg ? '编辑组织' : '添加组织'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="组织名称"
              margin="normal"
              defaultValue={editingOrg?.name || ''}
              required
            />
            <TextField
              fullWidth
              label="描述"
              margin="normal"
              multiline
              rows={3}
              defaultValue={editingOrg?.description || ''}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>状态</InputLabel>
              <Select
                defaultValue={editingOrg?.is_active ? 'active' : 'inactive'}
              >
                <MenuItem value="active">激活</MenuItem>
                <MenuItem value="inactive">禁用</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationManagementPage;