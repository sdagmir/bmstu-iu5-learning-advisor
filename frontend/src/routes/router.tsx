import { createBrowserRouter, Navigate } from 'react-router-dom'
import { RequireAuth, RequireAdmin, RedirectIfAuth } from './guards'
import { StudentShell } from '@/shells/StudentShell'
import { AdminShell } from '@/shells/AdminShell'
import { ErrorPage } from '@/components/common/ErrorPage'

import LoginPage from '@/pages/auth/LoginPage'
import RegisterPage from '@/pages/auth/RegisterPage'

import HomePage from '@/pages/student/HomePage'
import OnboardingPage from '@/pages/student/OnboardingPage'
import ChatPage from '@/pages/student/ChatPage'
import ProfilePage from '@/pages/student/ProfilePage'
import CoveragePage from '@/pages/student/CoveragePage'
import HistoryPage from '@/pages/student/HistoryPage'
import RecommendationDetailPage from '@/pages/student/RecommendationDetailPage'
import CardsDemoPage from '@/pages/dev/CardsDemoPage'

import DashboardPage from '@/pages/admin/DashboardPage'
import RulesPage from '@/pages/admin/RulesPage'
import SimulatorPage from '@/pages/admin/SimulatorPage'
import TracesPage from '@/pages/admin/TracesPage'
import CatalogPage from '@/pages/admin/CatalogPage'
import KnowledgePage from '@/pages/admin/KnowledgePage'
import UsersPage from '@/pages/admin/UsersPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <RedirectIfAuth>
        <LoginPage />
      </RedirectIfAuth>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: '/register',
    element: (
      <RedirectIfAuth>
        <RegisterPage />
      </RedirectIfAuth>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <StudentShell />
      </RequireAuth>
    ),
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <HomePage />, errorElement: <ErrorPage /> },
      { path: 'onboarding', element: <OnboardingPage />, errorElement: <ErrorPage /> },
      { path: 'chat', element: <ChatPage />, errorElement: <ErrorPage /> },
      { path: 'profile', element: <ProfilePage />, errorElement: <ErrorPage /> },
      { path: 'coverage', element: <CoveragePage />, errorElement: <ErrorPage /> },
      { path: 'history', element: <HistoryPage />, errorElement: <ErrorPage /> },
      {
        path: 'recommendations/:id',
        element: <RecommendationDetailPage />,
        errorElement: <ErrorPage />,
      },
      { path: 'dev/cards', element: <CardsDemoPage />, errorElement: <ErrorPage /> },
    ],
  },
  {
    path: '/admin',
    element: (
      <RequireAdmin>
        <AdminShell />
      </RequireAdmin>
    ),
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <DashboardPage />, errorElement: <ErrorPage /> },
      { path: 'rules', element: <RulesPage />, errorElement: <ErrorPage /> },
      { path: 'simulator', element: <SimulatorPage />, errorElement: <ErrorPage /> },
      { path: 'traces', element: <TracesPage />, errorElement: <ErrorPage /> },
      { path: 'catalog/:entity', element: <CatalogPage />, errorElement: <ErrorPage /> },
      { path: 'knowledge', element: <KnowledgePage />, errorElement: <ErrorPage /> },
      { path: 'users', element: <UsersPage />, errorElement: <ErrorPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
