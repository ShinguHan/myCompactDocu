import { Component } from 'react'
import type { ReactNode } from 'react'
import { HashRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  BookOutlined, DatabaseOutlined, BarChartOutlined,
  FileTextOutlined, PrinterOutlined,
} from '@ant-design/icons'

import LedgerPage from './pages/LedgerPage'
import MasterDataPage from './pages/MasterDataPage'
import AnnualStatusPage from './pages/AnnualStatusPage'
import MonthlyReportPage from './pages/MonthlyReportPage'
import ExitPassPage from './pages/ExitPassPage'

const { Sider, Content } = Layout

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
  { key: '/ledger', icon: <BookOutlined />, label: '입출고대장' },
  { key: '/master', icon: <DatabaseOutlined />, label: '기준정보' },
  { key: '/annual', icon: <BarChartOutlined />, label: '연간현황' },
  { key: '/report', icon: <FileTextOutlined />, label: '월말보고서' },
  { key: '/exitpass', icon: <PrinterOutlined />, label: '반출증' },
]

function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={180} theme="dark" style={{ position: 'fixed', height: '100vh', zIndex: 100 }}>
        <div style={{
          height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: 15, borderBottom: '1px solid #2d2d2d'
        }}>
          부산물·폐기물 관리
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={NAV_ITEMS}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>
      <Layout style={{ marginLeft: 180 }}>
        <Content style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/ledger" replace />} />
            <Route path="/ledger" element={<PageErrorBoundary><LedgerPage /></PageErrorBoundary>} />
            <Route path="/master" element={<PageErrorBoundary><MasterDataPage /></PageErrorBoundary>} />
            <Route path="/annual" element={<PageErrorBoundary><AnnualStatusPage /></PageErrorBoundary>} />
            <Route path="/report" element={<PageErrorBoundary><MonthlyReportPage /></PageErrorBoundary>} />
            <Route path="/exitpass" element={<PageErrorBoundary><ExitPassPage /></PageErrorBoundary>} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <HashRouter>
      <AppLayout />
    </HashRouter>
  )
}
