import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
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

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface SystemStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  recent_users: number;
}

const AdminConsolePage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      // 模拟加载用户数据
      const mockUsers: User[] = [
        {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          full_name: '系统管理员',
          is_active: true,
          is_admin: true,
          created_at: '2023-01-01T00:00:00Z'
        },
        {
          id: '2',
          username: 'user1',
          email: 'user1@example.com',
          full_name: '普通用户1',
          is_active: true,
          is_admin: false,
          created_at: '2023-05-01T00:00:00Z'
        }
      ];
      
      // 模拟加载系统统计数据
      const mockStats: SystemStats = {
        total_users: 42,
        active_users: 38,
        admin_users: 3,
        recent_users: 5
      };
      
      setUsers(mockUsers);
      setStats(mockStats);
      setError(null);
    } catch (err) {
      setError('加载系统数据失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setOpenDialog(true);
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      // 这里应该调用后端API删除用户
      setUsers(prev => prev.filter(user => user.id !== userId));
    } catch (err) {
      setError('删除用户失败');
      console.error(err);
    }
  };

  const handleAddUser = () => {
    setEditingUser(null);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingUser(null);
  };

  const handleSubmit = async () => {
    try {
      // 这里应该调用后端API保存用户信息
      handleCloseDialog();
    } catch (err) {
      setError('保存用户信息失败');
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
        <Typography variant="h4">管理员控制台</Typography>
        <IconButton onClick={loadSystemData} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {stats && (
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6">总用户数</Typography>
            <Typography variant="h4">{stats.total_users}</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6">活跃用户</Typography>
            <Typography variant="h4">{stats.active_users}</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6">管理员数</Typography>
            <Typography variant="h4">{stats.admin_users}</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6">新增用户(30天)</Typography>
            <Typography variant="h4">{stats.recent_users}</Typography>
          </Paper>
        </Box>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="用户管理" />
          <Tab label="系统设置" />
          <Tab label="日志查看" />
        </Tabs>

        {tabValue === 0 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">用户列表</Typography>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />} 
                onClick={handleAddUser}
              >
                添加用户
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>用户名</TableCell>
                      <TableCell>邮箱</TableCell>
                      <TableCell>全名</TableCell>
                      <TableCell>状态</TableCell>
                      <TableCell>角色</TableCell>
                      <TableCell>创建时间</TableCell>
                      <TableCell>操作</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>{user.username}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.full_name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={user.is_active ? '激活' : '禁用'} 
                            color={user.is_active ? 'success' : 'default'} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={user.is_admin ? '管理员' : '用户'} 
                            color={user.is_admin ? 'primary' : 'default'} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{formatDate(user.created_at)}</TableCell>
                        <TableCell>
                          <Tooltip title="编辑">
                            <IconButton onClick={() => handleEditUser(user)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="删除">
                            <IconButton onClick={() => handleDeleteUser(user.id)}>
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {tabValue === 1 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              系统设置
            </Typography>
            <Typography color="textSecondary">
              系统设置功能正在开发中...
            </Typography>
          </Box>
        )}

        {tabValue === 2 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              系统日志
            </Typography>
            <Typography color="textSecondary">
              日志查看功能正在开发中...
            </Typography>
          </Box>
        )}
      </Paper>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? '编辑用户' : '添加用户'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="用户名"
              margin="normal"
              defaultValue={editingUser?.username || ''}
            />
            <TextField
              fullWidth
              label="邮箱"
              margin="normal"
              type="email"
              defaultValue={editingUser?.email || ''}
            />
            <TextField
              fullWidth
              label="全名"
              margin="normal"
              defaultValue={editingUser?.full_name || ''}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>角色</InputLabel>
              <Select
                defaultValue={editingUser?.is_admin ? 'admin' : 'user'}
              >
                <MenuItem value="user">普通用户</MenuItem>
                <MenuItem value="admin">管理员</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>状态</InputLabel>
              <Select
                defaultValue={editingUser?.is_active ? 'active' : 'inactive'}
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

export default AdminConsolePage;