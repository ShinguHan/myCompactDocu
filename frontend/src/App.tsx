import { Component } from 'react'
import type { ReactNode } from 'react'
import { createBrowserRouter, RouterProvider, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BookOutlined, DatabaseOutlined, BarChartOutlined,
  FileTextOutlined, PrinterOutlined,
} from '@ant-design/icons'

import LedgerPage from './pages/LedgerPage'
import MasterDataPage from './pages/MasterDataPage'
import AnnualStatusPage from './pages/AnnualStatusPage'
import MonthlyReportPage from './pages/MonthlyReportPage'
import ExitPassPage from './pages/ExitPassPage'

class PageErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null }
  static getDerivedStateFromError(error: Error) { return { error } }
  render() {
    if (this.state.error)
      return (
        <div style={{ padding: 40, color: '#cf1322' }}>
          <b>페이지 오류:</b> {(this.state.error as Error).message}
        </div>
      )
    return this.props.children
  }
}

const NAV_ITEMS = [
  { to: '/ledger',  icon: <BookOutlined />,      label: '입출고대장' },
  { to: '/master',  icon: <DatabaseOutlined />,   label: '기준정보'   },
  { to: '/annual',  icon: <BarChartOutlined />,   label: '연간현황'   },
  { to: '/report',  icon: <FileTextOutlined />,   label: '월말보고서' },
  { to: '/exitpass',icon: <PrinterOutlined />,    label: '반출증'     },
]

function AppLayout() {
  const location = useLocation()
  console.log('[Router]', location.pathname)
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <div style={{
        width: 180, background: '#001529',
        position: 'fixed', height: '100vh', zIndex: 1000,
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{
          height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: 15, borderBottom: '1px solid #2d2d2d',
          flexShrink: 0,
        }}>
          부산물·폐기물 관리
        </div>
        <nav style={{ marginTop: 4 }}>
          {NAV_ITEMS.map(({ to, icon, label }) => (
            <NavLink key={to} to={to} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              height: 40, padding: '0 16px',
              color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
              background: isActive ? '#1677ff' : 'transparent',
              textDecoration: 'none', fontSize: 14,
              transition: 'background 0.2s, color 0.2s',
            })}>
              {icon}<span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
      <div style={{ marginLeft: 180, flex: 1, padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
        <Outlet />
      </div>
    </div>
  )
}

const router = createBrowserRouter([{
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <LedgerPage /> },
      { path: 'ledger',  element: <PageErrorBoundary><LedgerPage /></PageErrorBoundary> },
      { path: 'master',  element: <PageErrorBoundary><MasterDataPage /></PageErrorBoundary> },
      { path: 'annual',  element: <PageErrorBoundary><AnnualStatusPage /></PageErrorBoundary> },
      { path: 'report',  element: <PageErrorBoundary><MonthlyReportPage /></PageErrorBoundary> },
      { path: 'exitpass',element: <PageErrorBoundary><ExitPassPage /></PageErrorBoundary> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
