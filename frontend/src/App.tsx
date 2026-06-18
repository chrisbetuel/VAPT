import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import MainLayout from "./components/layout/MainLayout";
import AuthLayout from "./components/layout/AuthLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import DashboardPage from "./pages/dashboard/DashboardPage";
import ScansPage from "./pages/scans/ScansPage";
import ScanDetailPage from "./pages/scans/ScanDetailPage";
import NewScanPage from "./pages/scans/NewScanPage";
import TargetsPage from "./pages/targets/TargetsPage";
import TargetDetailPage from "./pages/targets/TargetDetailPage";
import ReportsPage from "./pages/reports/ReportsPage";
import ReportDetailPage from "./pages/reports/ReportDetailPage";
import UsersPage from "./pages/admin/UsersPage";
import SettingsPage from "./pages/settings/SettingsPage";
import NotFoundPage from "./pages/errors/NotFoundPage";

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/scans" element={<ScansPage />} />
          <Route path="/scans/new" element={<NewScanPage />} />
          <Route path="/scans/:id" element={<ScanDetailPage />} />
          <Route path="/targets" element={<TargetsPage />} />
          <Route path="/targets/:id" element={<TargetDetailPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/reports/:id" element={<ReportDetailPage />} />
          <Route path="/admin/users" element={<UsersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { background: "#18181b", color: "#fff" },
        }}
      />
    </>
  );
}
