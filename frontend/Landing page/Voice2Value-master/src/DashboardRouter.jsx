import React from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardLayout from './dashboard/DashboardLayout';
import OverviewPage from './dashboard/OverviewPage';
import IssuesPage from './dashboard/IssuesPage';
import IntegrationsPage from './dashboard/IntegrationsPage';
import ActivityPage from './dashboard/ActivityPage';
import SettingsPage from './dashboard/SettingsPage';
import IssueDetailPage from './dashboard/IssueDetailPage';
import './dashboard.css';


export default function DashboardRouter() {
  return (
    <div className="dashboard-container">
      <DashboardLayout>
        <Routes>
          <Route path="/dashboard" element={<OverviewPage />} />
          <Route path="/dashboard/overview" element={<OverviewPage />} />
          <Route path="/dashboard/issues" element={<IssuesPage />} />
          <Route path="/dashboard/issues/:id" element={<IssueDetailPage />} />
          <Route path="/dashboard/integrations" element={<IntegrationsPage />} />
          <Route path="/dashboard/activity" element={<ActivityPage />} />
          <Route path="/dashboard/settings" element={<SettingsPage />} />
        </Routes>
      </DashboardLayout>
    </div>
  );
}
