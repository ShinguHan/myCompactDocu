import { Component, Suspense, lazy } from 'react'
import type { ReactNode } from 'react'
import { createBrowserRouter, RouterProvider, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BookOutlined, DatabaseOutlined, BarChartOutlined,
  FileTextOutlined, PrinterOutlined,
} from '@ant-design/icons'

const LedgerPage = lazy(() => import('./pages/LedgerPage'))
const MasterDataPage = lazy(() => import('./pages/MasterDataPage'))
const AnnualStatusPage = lazy(() => import('./pages/AnnualStatusPage'))
const MonthlyReportPage = lazy(() => import('./pages/MonthlyReportPage'))
const ExitPassPage = lazy(() => import('./pages/ExitPassPage'))

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

function PageFallback() {
  return (
    <div style={{ padding: 40, color: '#666' }}>
      페이지를 불러오는 중입니다...
    </div>
  )
}

function withPageBoundary(node: ReactNode) {
  return (
    <PageErrorBoundary>
      <Suspense fallback={<PageFallback />}>
        {node}
      </Suspense>
    </PageErrorBoundary>
  )
}

const router = createBrowserRouter([{
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: withPageBoundary(<LedgerPage />) },
      { path: 'ledger',  element: withPageBoundary(<LedgerPage />) },
      { path: 'master',  element: withPageBoundary(<MasterDataPage />) },
      { path: 'annual',  element: withPageBoundary(<AnnualStatusPage />) },
      { path: 'report',  element: withPageBoundary(<MonthlyReportPage />) },
      { path: 'exitpass',element: withPageBoundary(<ExitPassPage />) },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
