import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  FormControlLabel,
  Switch,
  Button,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormGroup,
  Divider,
  Alert,
  Snackbar
} from '@mui/material';

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh' | 'en';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  privacy: {
    profileVisible: boolean;
    showActivity: boolean;
  };
  defaultQueryMode: 'simple' | 'advanced';
  autoSaveQueries: boolean;
}

const UserPreferencesPage: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'auto',
    language: 'zh',
    notifications: {
      email: true,
      push: true,
      sms: false
    },
    privacy: {
      profileVisible: true,
      showActivity: true
    },
    defaultQueryMode: 'simple',
    autoSaveQueries: true
  });
  
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  useEffect(() => {
    // 这里应该从后端API获取用户偏好设置
    // 暂时使用默认值
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      // 模拟从后端获取数据
      // const response = await fetch('/api/user/preferences');
      // const data = await response.json();
      // setPreferences(data);
    } catch (err) {
      console.error('加载用户偏好设置失败:', err);
      showSnackbar('加载用户偏好设置失败');
    }
  };

  const handleSave = async () => {
    try {
      // 这里应该调用后端API保存用户偏好设置
      // await fetch('/api/user/preferences', {
      //   method: 'PUT',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(preferences),
      // });
      showSnackbar('偏好设置已保存');
    } catch (err) {
      console.error('保存用户偏好设置失败:', err);
      showSnackbar('保存用户偏好设置失败');
    }
  };

  const handleChange = (field: keyof UserPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNestedChange = (parent: keyof UserPreferences, field: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [parent]: {
        ...(prev[parent] as object),
        [field]: value
      }
    }));
  };

  const showSnackbar = (message: string) => {
    setSnackbarMessage(message);
    setOpenSnackbar(true);
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        个人偏好设置
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            显示设置
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>主题</InputLabel>
            <Select
              value={preferences.theme}
              onChange={(e) => handleChange('theme', e.target.value)}
            >
              <MenuItem value="light">浅色主题</MenuItem>
              <MenuItem value="dark">深色主题</MenuItem>
              <MenuItem value="auto">自动</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth>
            <InputLabel>语言</InputLabel>
            <Select
              value={preferences.language}
              onChange={(e) => handleChange('language', e.target.value)}
            >
              <MenuItem value="zh">中文</MenuItem>
              <MenuItem value="en">English</MenuItem>
            </Select>
          </FormControl>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            通知设置
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.email}
                  onChange={(e) => handleNestedChange('notifications', 'email', e.target.checked)}
                />
              }
              label="邮件通知"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.push}
                  onChange={(e) => handleNestedChange('notifications', 'push', e.target.checked)}
                />
              }
              label="推送通知"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.sms}
                  onChange={(e) => handleNestedChange('notifications', 'sms', e.target.checked)}
                />
              }
              label="短信通知"
            />
          </FormGroup>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            隐私设置
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.privacy.profileVisible}
                  onChange={(e) => handleNestedChange('privacy', 'profileVisible', e.target.checked)}
                />
              }
              label="公开个人资料"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.privacy.showActivity}
                  onChange={(e) => handleNestedChange('privacy', 'showActivity', e.target.checked)}
                />
              }
              label="显示活动状态"
            />
          </FormGroup>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            查询设置
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>默认查询模式</InputLabel>
            <Select
              value={preferences.defaultQueryMode}
              onChange={(e) => handleChange('defaultQueryMode', e.target.value)}
            >
              <MenuItem value="simple">简单模式</MenuItem>
              <MenuItem value="advanced">高级模式</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={preferences.autoSaveQueries}
                onChange={(e) => handleChange('autoSaveQueries', e.target.checked)}
              />
            }
            label="自动保存查询历史"
          />
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleSave}
          >
            保存设置
          </Button>
        </Box>
      </Paper>
      
      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default UserPreferencesPage;