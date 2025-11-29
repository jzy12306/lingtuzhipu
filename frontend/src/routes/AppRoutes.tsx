import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';
import DocumentManagementPage from '../pages/DocumentManagementPage';
import GraphVisualizationPage from '../pages/GraphVisualizationPage';
import LoginPage from '../pages/LoginPage';
import NewHomePage from '../pages/NewHomePage';
import QueryPage from '../pages/QueryPage';
import RegisterPage from '../pages/RegisterPage';
import QueryHistoryPage from '../pages/QueryHistoryPage';
import UserPreferencesPage from '../pages/UserPreferencesPage';
import AdminConsolePage from '../pages/AdminConsolePage';
import OrganizationManagementPage from '../pages/OrganizationManagementPage';

const AppRoutes: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<NewHomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentManagementPage />} />
        <Route path="/graph" element={<GraphVisualizationPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/query" element={<QueryPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/query-history" element={<QueryHistoryPage />} />
        <Route path="/preferences" element={<UserPreferencesPage />} />
        <Route path="/admin" element={<AdminConsolePage />} />
        <Route path="/organization" element={<OrganizationManagementPage />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;