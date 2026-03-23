import { useState } from 'react'
import { Select, Table, Typography, DatePicker } from 'antd'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { api } from '../api'

const { Text } = Typography

export default function AnnualStatusPage() {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [companyId, setCompanyId] = useState<number | undefined>()
  const [itemId, setItemId] = useState<number | undefined>()

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['annual', year, companyId, itemId],
    queryFn: () => api.getAnnualReport({ year, company_id: companyId, item_id: itemId }),
  })
  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: () => api.getItems() })
  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })

  const fmt = (n: number) => n.toLocaleString()

  const totalQty = rows.reduce((s, r) => s + r.quantity, 0)
  const totalAmt = rows.reduce((s, r) => s + r.total_amount, 0)

  const columns = [
    { title: '일자', dataIndex: 'date', key: 'date', width: 100 },
    { title: '품목', dataIndex: 'item_name', key: 'item_name' },
    { title: '업체', dataIndex: 'company_name', key: 'company_name' },
    { title: '처리량', dataIndex: 'quantity', key: 'quantity', align: 'right' as const },
    {
      title: '단가', dataIndex: 'unit_price', key: 'unit_price', align: 'right' as const,
      render: (v: number) => fmt(v)
    },
    {
      title: '금액', dataIndex: 'total_amount', key: 'total_amount', align: 'right' as const,
      render: (v: number) => <span style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v)}</span>
    },
    { title: '비고', dataIndex: 'note', key: 'note' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>연간처리 현황</h2>
      </div>

      <div style={{ background: '#fff', padding: '12px 16px', borderRadius: 8, marginBottom: 12, display: 'flex', gap: 12 }}>
        <DatePicker
          picker="year"
          defaultValue={dayjs(`${year}`)}
          onChange={(d) => d && setYear(d.year())}
        />
        <Select allowClear style={{ width: 200 }} placeholder="업체 필터"
          onChange={setCompanyId}
          options={companies.map(c => ({ value: c.id, label: c.name }))} />
        <Select allowClear style={{ width: 160 }} placeholder="품목 필터"
          onChange={setItemId}
          options={items.map(i => ({ value: i.id, label: i.name }))} />
      </div>

      <div style={{ marginBottom: 8, textAlign: 'right', color: '#666' }}>
        총 {rows.length}건 | 처리량 합계: <strong>{fmt(totalQty)}</strong> |
        금액 합계: <strong style={{ color: totalAmt < 0 ? '#cf1322' : '#1677ff' }}>{fmt(totalAmt)}</strong>원
      </div>

      <Table
        dataSource={rows.map((r, i) => ({ ...r, key: i }))}
        columns={columns}
        loading={isLoading}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: true }}
        style={{ background: '#fff', borderRadius: 8 }}
        summary={() => (
          <Table.Summary.Row style={{ fontWeight: 600, background: '#fafafa' }}>
            <Table.Summary.Cell index={0} colSpan={3}>합계</Table.Summary.Cell>
            <Table.Summary.Cell index={3} align="right">{fmt(totalQty)}</Table.Summary.Cell>
            <Table.Summary.Cell index={4} />
            <Table.Summary.Cell index={5} align="right">
              <Text type={totalAmt < 0 ? 'danger' : undefined}>{fmt(totalAmt)}</Text>
            </Table.Summary.Cell>
            <Table.Summary.Cell index={6} />
          </Table.Summary.Row>
        )}
      />
    </div>
  )
}
