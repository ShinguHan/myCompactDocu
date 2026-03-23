import { useState } from 'react'
import { DatePicker, Table, Typography, Space, Button, Tag, Divider, Spin, Segmented, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { DownloadOutlined, BarChartOutlined, LineChartOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import type { ReportRow, MonthlyTrendItem } from '../types'

const { Text, Title } = Typography

// ── 연간 트렌드 차트 ─────────────────────────────────────────────────────────

const MONTH_LABELS = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']

function fmtAmt(v: number) {
  if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}백만`
  if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}천`
  return String(v)
}

type ChartType = 'bar' | 'line'

function TrendChart({ year }: { year: number }) {
  const [chartType, setChartType] = useState<ChartType>('bar')

  const { data: trend = [], isLoading } = useQuery({
    queryKey: ['monthly-trend', year],
    queryFn: () => api.getMonthlyTrend(year),
  })

  const chartData = trend.map((d: MonthlyTrendItem) => ({
    month: MONTH_LABELS[d.month - 1],
    부산물: d.byproduct,
    폐기물: Math.abs(d.waste),
  }))

  const commonProps = {
    data: chartData,
    margin: { top: 4, right: 16, left: 0, bottom: 0 },
  }

  const axes = (
    <>
      <CartesianGrid strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="month" tick={{ fontSize: 12 }} tickLine={false} />
      <YAxis tickFormatter={fmtAmt} tick={{ fontSize: 11 }}
        axisLine={false} tickLine={false} width={56} />
      <Tooltip
        formatter={(value: number, name: string) => [`${value.toLocaleString()}원`, name]}
        labelStyle={{ fontWeight: 600 }}
      />
      <Legend wrapperStyle={{ fontSize: 13 }} />
    </>
  )

  if (isLoading) return <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>

  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: '16px 16px 8px', marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Title level={5} style={{ margin: 0 }}>{year}년 월별 추이</Title>
        <Segmented
          size="small"
          value={chartType}
          onChange={(v) => setChartType(v as ChartType)}
          options={[
            { value: 'bar', icon: <BarChartOutlined /> , label: 'Bar' },
            { value: 'line', icon: <LineChartOutlined />, label: 'Line' },
          ]}
        />
      </div>
      <ResponsiveContainer width="100%" height={220}>
        {chartType === 'bar' ? (
          <BarChart {...commonProps}>
            {axes}
            <Bar dataKey="부산물" fill="#1677ff" radius={[3, 3, 0, 0]} />
            <Bar dataKey="폐기물" fill="#fa8c16" radius={[3, 3, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart {...commonProps}>
            {axes}
            <Line type="monotone" dataKey="부산물" stroke="#1677ff"
              strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="폐기물" stroke="#fa8c16"
              strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        )}
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', fontSize: 12, color: '#aaa', marginTop: 4 }}>
        * 폐기물 금액은 절대값으로 표시 (실제 음수)
      </div>
    </div>
  )
}

// ── 월별 상세 테이블 ─────────────────────────────────────────────────────────

function ReportTable({ title, rows, totalCurr, totalPrev, color }: {
  title: string
  rows: ReportRow[]
  totalCurr: number
  totalPrev: number
  color: string
}) {
  const fmt = (n: number) => n.toLocaleString()

  type RowType = ReportRow & { key: number }
  const columns: ColumnsType<RowType> = [
    { title: '업체명', dataIndex: 'company_name', key: 'company',
      onCell: (_: RowType, idx?: number) => {
        if (idx === undefined || idx === 0) return {}
        if (rows[idx - 1].company_name === rows[idx].company_name) return { rowSpan: 0 }
        const span = rows.filter((r, i) => i >= idx && r.company_name === rows[idx].company_name).length
        return { rowSpan: span }
      }
    },
    { title: '품명', dataIndex: 'item_name', key: 'item' },
    { title: '단가', dataIndex: 'unit_price', key: 'unit_price', align: 'right' as const,
      render: (v: number) => v ? fmt(v) : '-' },
    { title: '당월 처리량', dataIndex: 'current_quantity', key: 'curr_qty', align: 'right' as const },
    { title: '당월 금액', dataIndex: 'current_amount', key: 'curr_amt', align: 'right' as const,
      render: (v: number) => <span style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v)}</span> },
    { title: '전월 금액', dataIndex: 'prev_amount', key: 'prev_amt', align: 'right' as const,
      render: (v: number) => <span style={{ color: v < 0 ? '#cf1322' : '#888' }}>{fmt(v)}</span> },
    { title: '비고', dataIndex: 'note', key: 'note' },
  ]

  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <Tag color={color} style={{ fontSize: 14, padding: '2px 12px' }}>{title}</Tag>
        <Text>당월: <strong>{fmt(totalCurr)}</strong>원</Text>
        <Text type="secondary">전월: {fmt(totalPrev)}원</Text>
        {totalCurr !== 0 && totalPrev !== 0 && (
          <Text type={totalCurr > totalPrev ? 'success' : 'danger'}>
            ({totalCurr > totalPrev ? '▲' : '▼'} {fmt(Math.abs(totalCurr - totalPrev))}원)
          </Text>
        )}
      </div>
      <Table
        dataSource={rows.map((r, i) => ({ ...r, key: i }))}
        columns={columns}
        size="small"
        pagination={false}
        style={{ background: '#fff', borderRadius: 8 }}
        summary={() => (
          <Table.Summary.Row style={{ fontWeight: 600, background: '#fafafa' }}>
            <Table.Summary.Cell index={0} colSpan={3}>소계</Table.Summary.Cell>
            <Table.Summary.Cell index={3} align="right">
              {fmt(rows.reduce((s, r) => s + r.current_quantity, 0))}
            </Table.Summary.Cell>
            <Table.Summary.Cell index={4} align="right">{fmt(totalCurr)}</Table.Summary.Cell>
            <Table.Summary.Cell index={5} align="right">{fmt(totalPrev)}</Table.Summary.Cell>
            <Table.Summary.Cell index={6} />
          </Table.Summary.Row>
        )}
      />
    </div>
  )
}

// ── 메인 페이지 ──────────────────────────────────────────────────────────────

export default function MonthlyReportPage() {
  const now = dayjs()
  const [year, setYear] = useState(now.year())
  const [month, setMonth] = useState(now.month() + 1)
  const [downloading, setDownloading] = useState(false)

  const { data: report, isLoading } = useQuery({
    queryKey: ['monthly', year, month],
    queryFn: () => api.getMonthlyReport(year, month),
    enabled: !!year && !!month,
  })

  const handleMonthChange = (d: dayjs.Dayjs | null) => {
    if (!d) return
    setYear(d.year())
    setMonth(d.month() + 1)
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const blob = await api.downloadMonthlyReport(year, month)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `월말보고서_${year}년${String(month).padStart(2, '0')}월.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      message.error('엑셀 생성에 실패했습니다')
    } finally {
      setDownloading(false)
    }
  }

  const fmt = (n: number) => n.toLocaleString()

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>월말 결산보고서</h2>
        <Space>
          <DatePicker picker="month" defaultValue={now}
            onChange={handleMonthChange} format="YYYY년 MM월" />
          <Button icon={<DownloadOutlined />} loading={downloading} onClick={handleDownload}>
            엑셀 출력
          </Button>
        </Space>
      </div>

      {/* 연간 트렌드 차트 */}
      <TrendChart year={year} />

      {isLoading && <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>}

      {report && !isLoading && (
        <>
          {/* 요약 */}
          <div style={{ background: '#fff', padding: 16, borderRadius: 8, marginBottom: 24 }}>
            <Title level={5}>{year}년 {month}월 매각 및 처리 현황 요약</Title>
            <Table
              size="small"
              pagination={false}
              dataSource={[
                {
                  key: '매각', 구분: '매각 (부산물)',
                  당월금액: report.total_current_byproduct,
                  전월금액: report.total_prev_byproduct,
                },
                {
                  key: '처리', 구분: '처리 (폐기물)',
                  당월금액: report.total_current_waste,
                  전월금액: report.total_prev_waste,
                },
                {
                  key: '이익', 구분: '이익 (매각 - 처리)',
                  당월금액: report.total_current_byproduct + report.total_current_waste,
                  전월금액: report.total_prev_byproduct + report.total_prev_waste,
                },
              ]}
              columns={[
                { title: '구분', dataIndex: '구분' },
                { title: '당월 금액', dataIndex: '당월금액', align: 'right' as const,
                  render: (v: number) => <Text style={{ color: v < 0 ? '#cf1322' : '#1677ff', fontWeight: 600 }}>{fmt(v)}</Text> },
                { title: '전월 금액', dataIndex: '전월금액', align: 'right' as const,
                  render: (v: number) => <Text type="secondary">{fmt(v)}</Text> },
              ]}
              style={{ maxWidth: 500 }}
            />
          </div>

          <Divider>부산물 매각 세부현황</Divider>
          <ReportTable
            title="부산물 매각"
            rows={report.byproducts}
            totalCurr={report.total_current_byproduct}
            totalPrev={report.total_prev_byproduct}
            color="blue"
          />

          <Divider>폐기물 처리 세부현황</Divider>
          <ReportTable
            title="폐기물 처리"
            rows={report.wastes}
            totalCurr={report.total_current_waste}
            totalPrev={report.total_prev_waste}
            color="orange"
          />
        </>
      )}
    </div>
  )
}
