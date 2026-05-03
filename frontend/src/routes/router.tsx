import { createBrowserRouter, Navigate } from 'react-router-dom'
import { RequireAuth, RequireAdmin, RedirectIfAuth } from './guards'
import { StudentShell } from '@/shells/StudentShell'
import { AdminShell } from '@/shells/AdminShell'

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
import TraceDetailPage from '@/pages/admin/TraceDetailPage'
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
  },
  {
    path: '/register',
    element: (
      <RedirectIfAuth>
        <RegisterPage />
      </RedirectIfAuth>
    ),
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <StudentShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: 'onboarding', element: <OnboardingPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'coverage', element: <CoveragePage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'recommendations/:id', element: <RecommendationDetailPage /> },
      { path: 'dev/cards', element: <CardsDemoPage /> },
    ],
  },
  {
    path: '/admin',
    element: (
      <RequireAdmin>
        <AdminShell />
      </RequireAdmin>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'rules', element: <RulesPage /> },
      { path: 'simulator', element: <SimulatorPage /> },
      { path: 'traces', element: <TracesPage /> },
      { path: 'traces/:id', element: <TraceDetailPage /> },
      { path: 'catalog/:entity', element: <CatalogPage /> },
      { path: 'knowledge', element: <KnowledgePage /> },
      { path: 'users', element: <UsersPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
