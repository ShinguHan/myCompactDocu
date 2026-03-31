import { useState, useMemo, useEffect } from 'react'
import { Tabs, Table, Button, Modal, Form, Input, Select, InputNumber,
  DatePicker, Tag, Space, Popconfirm, message, Typography } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  ArrowUpOutlined, ArrowDownOutlined, LinkOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { api } from '../api'
import type { Item, Company, Contract, ItemCompany } from '../types'

const { Option } = Select


const SECTION_STYLE: React.CSSProperties = {
  paddingTop: 16,
}

const FILTER_BAR: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  alignItems: 'center',
  marginBottom: 12,
  flexWrap: 'wrap',
}

// ── 품목 섹션 ────────────────────────────────────────────────────────────────

function ItemsSection() {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const [editing, setEditing] = useState<Item | null>(null)
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>()
  const [linkItem, setLinkItem] = useState<Item | null>(null)
  const [linkOpen, setLinkOpen] = useState(false)
  const [linkSelected, setLinkSelected] = useState<number[]>([])

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.getItems(),
  })
  const { data: companies = [] } = useQuery({
    queryKey: ['companies'],
    queryFn: api.getCompanies,
  })
  const { data: linkedICs = [] } = useQuery<ItemCompany[]>({
    queryKey: ['item-companies', linkItem?.id],
    queryFn: () => api.getItemCompanies({ item_id: linkItem!.id }),
    enabled: linkItem !== null,
  })

  useEffect(() => {
    setLinkSelected(linkedICs.map(ic => ic.company_id))
  }, [linkedICs])

  const saveLinks = useMutation({
    mutationFn: async (selectedIds: number[]) => {
      if (!linkItem) return
      const currentIds = linkedICs.map(ic => ic.company_id)
      const toDelete = linkedICs.filter(ic => !selectedIds.includes(ic.company_id))
      const toAdd = selectedIds.filter(id => !currentIds.includes(id))
      await Promise.all(toDelete.map(ic => api.deleteItemCompany(ic.id)))
      await Promise.all(toAdd.map((id, idx) =>
        api.createItemCompany({ item_id: linkItem.id, company_id: id, sort_order: currentIds.length + idx + 1 })
      ))
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['item-companies'] })
      setLinkOpen(false); setLinkItem(null)
      message.success('업체 연결이 저장되었습니다')
    },
    onError: (e: any) => message.error(e.message),
  })

  const filtered = useMemo(() => items.filter(item => {
    const matchSearch = !search ||
      item.name.includes(search) ||
      (item.report_name ?? '').includes(search)
    const matchCat = !categoryFilter || item.category === categoryFilter
    return matchSearch && matchCat
  }), [items, search, categoryFilter])

  const save = useMutation({
    mutationFn: (values: any) =>
      editing ? api.updateItem(editing.id, values) : api.createItem(values),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['items'] })
      setOpen(false); form.resetFields(); setEditing(null)
      message.success('저장되었습니다')
    },
    onError: (e: any) => message.error(e.message),
  })

  const remove = useMutation({
    mutationFn: api.deleteItem,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['items'] }); message.success('삭제되었습니다') },
    onError: (e: any) => message.error(e.message),
  })

  const columns = [
    { title: '품목명', dataIndex: 'name', key: 'name' },
    { title: '보고서 표기명', dataIndex: 'report_name', key: 'report_name',
      render: (v: string | null) => v || <span style={{ color: '#bbb' }}>-</span> },
    { title: '단위', dataIndex: 'unit', key: 'unit', width: 90 },
    { title: '구분', dataIndex: 'category', key: 'category', width: 90,
      render: (v: string) => <Tag color={v === '부산물' ? 'blue' : 'orange'}>{v}</Tag> },
    {
      title: '', key: 'actions', width: 120,
      render: (_: any, record: Item) => (
        <Space size={4}>
          <Button size="small" icon={<LinkOutlined />} title="업체 연결"
            onClick={() => { setLinkItem(record); setLinkOpen(true) }} />
          <Button size="small" icon={<EditOutlined />} onClick={() => {
            setEditing(record); form.setFieldsValue(record); setOpen(true)
          }} />
          <Popconfirm title="삭제하시겠습니까?" onConfirm={() => remove.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={SECTION_STYLE}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#888', fontSize: 13 }}>총 {filtered.length}개</span>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setEditing(null); setOpen(true) }}>
          추가
        </Button>
      </div>

      <div style={FILTER_BAR}>
        <Input
          prefix={<SearchOutlined style={{ color: '#bbb' }} />}
          placeholder="품목명 검색"
          style={{ width: 200 }}
          value={search}
          onChange={e => setSearch(e.target.value)}
          allowClear
        />
        <Select
          allowClear placeholder="구분 필터" style={{ width: 120 }}
          value={categoryFilter} onChange={setCategoryFilter}
        >
          <Option value="부산물">부산물</Option>
          <Option value="폐기물">폐기물</Option>
        </Select>
      </div>

      <Table
        dataSource={filtered} columns={columns} rowKey="id"
        loading={isLoading} size="small" pagination={false}
      />

      <Modal title={editing ? '품목 수정' : '품목 추가'} open={open}
        onOk={() => form.submit()} onCancel={() => setOpen(false)} confirmLoading={save.isPending}>
        <Form form={form} layout="vertical" onFinish={save.mutate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="품목명" rules={[{ required: true }]}>
            <Input placeholder="예: PE_SCRAP" />
          </Form.Item>
          <Form.Item name="report_name" label="보고서 표기명">
            <Input placeholder="다를 경우 입력 (예: PE SCRAP)" />
          </Form.Item>
          <Form.Item name="unit" label="단위" initialValue="원/kg" rules={[{ required: true }]}>
            <Select>
              <Option value="원/kg">원/kg</Option>
              <Option value="원/EA">원/EA</Option>
              <Option value="원/대">원/대</Option>
            </Select>
          </Form.Item>
          <Form.Item name="category" label="구분" rules={[{ required: true }]}>
            <Select>
              <Option value="부산물">부산물</Option>
              <Option value="폐기물">폐기물</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`업체 연결 — ${linkItem?.name}`}
        open={linkOpen}
        onOk={() => saveLinks.mutate(linkSelected)}
        onCancel={() => { setLinkOpen(false); setLinkItem(null) }}
        confirmLoading={saveLinks.isPending}
      >
        <div style={{ marginBottom: 8, color: '#888', fontSize: 13 }}>
          이 품목을 처리하는 업체를 선택하세요. 입출고 대장 입력 시 선택한 업체만 표시됩니다.
        </div>
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="업체 선택"
          value={linkSelected}
          onChange={setLinkSelected}
          options={companies.map(c => ({ value: c.id, label: c.name }))}
          optionFilterProp="label"
        />
      </Modal>
    </div>
  )
}

// ── 업체 섹션 ────────────────────────────────────────────────────────────────

function CompaniesSection() {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const [editing, setEditing] = useState<Company | null>(null)
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  const { data: companies = [], isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: api.getCompanies,
  })

  const filtered = useMemo(() =>
    companies.filter(c => !search || c.name.includes(search)),
    [companies, search]
  )

  const save = useMutation({
    mutationFn: (values: any) =>
      editing ? api.updateCompany(editing.id, values) : api.createCompany(values),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['companies'] })
      setOpen(false); form.resetFields(); setEditing(null)
      message.success('저장되었습니다')
    },
    onError: (e: any) => message.error(e.message),
  })

  const remove = useMutation({
    mutationFn: api.deleteCompany,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['companies'] }); message.success('삭제되었습니다') },
    onError: (e: any) => message.error(e.message),
  })

  const columns = [
    { title: '업체명', dataIndex: 'name', key: 'name' },
    {
      title: '', key: 'actions', width: 80,
      render: (_: any, record: Company) => (
        <Space size={4}>
          <Button size="small" icon={<EditOutlined />} onClick={() => {
            setEditing(record); form.setFieldsValue(record); setOpen(true)
          }} />
          <Popconfirm title="삭제하시겠습니까?" onConfirm={() => remove.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={SECTION_STYLE}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#888', fontSize: 13 }}>총 {filtered.length}개</span>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setEditing(null); setOpen(true) }}>
          추가
        </Button>
      </div>

      <div style={FILTER_BAR}>
        <Input
          prefix={<SearchOutlined style={{ color: '#bbb' }} />}
          placeholder="업체명 검색"
          style={{ width: 200 }}
          value={search}
          onChange={e => setSearch(e.target.value)}
          allowClear
        />
      </div>

      <Table
        dataSource={filtered} columns={columns} rowKey="id"
        loading={isLoading} size="small" pagination={false}
      />

      <Modal title={editing ? '업체 수정' : '업체 추가'} open={open}
        onOk={() => form.submit()} onCancel={() => setOpen(false)} confirmLoading={save.isPending}>
        <Form form={form} layout="vertical" onFinish={save.mutate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="업체명" rules={[{ required: true }]}>
            <Input placeholder="예: 에이슨텍코퍼레이션" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ── 계약단가 섹션 ─────────────────────────────────────────────────────────────

function ContractsSection() {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const [editing, setEditing] = useState<Contract | null>(null)
  const [open, setOpen] = useState(false)
  const [itemFilter, setItemFilter] = useState<number | undefined>()
  const [companyFilter, setCompanyFilter] = useState<number | undefined>()
  const [view, setView] = useState<'current' | 'history'>('current')

  const { data: contracts = [], isLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => api.getContracts(),
  })
  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: () => api.getItems() })
  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })

  // 현재 단가: 각 품목+업체 조합의 최신 계약
  const currentContracts = useMemo(() => {
    const map = new Map<string, Contract>()
    contracts.forEach(c => {
      const key = `${c.item_id}_${c.company_id}`
      const existing = map.get(key)
      if (!existing || c.effective_date > existing.effective_date) map.set(key, c)
    })
    return Array.from(map.values())
  }, [contracts])

  // 변경 이력: 전체 계약을 날짜 내림차순 + 이전 단가 계산
  const historyContracts = useMemo(() => {
    const sorted = [...contracts].sort((a, b) => b.effective_date.localeCompare(a.effective_date))
    return sorted.map(c => {
      const prev = contracts
        .filter(x => x.item_id === c.item_id && x.company_id === c.company_id && x.effective_date < c.effective_date)
        .sort((a, b) => b.effective_date.localeCompare(a.effective_date))[0]
      return { ...c, prev_price: prev?.unit_price }
    })
  }, [contracts])

  const applyFilter = <T extends Contract>(list: T[]) => list.filter(c => {
    const matchItem = !itemFilter || c.item_id === itemFilter
    const matchCompany = !companyFilter || c.company_id === companyFilter
    return matchItem && matchCompany
  })

  const save = useMutation({
    mutationFn: (values: any) => {
      const payload = { ...values, effective_date: values.effective_date.format('YYYY-MM-DD') }
      return editing ? api.updateContract(editing.id, payload) : api.createContract(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['contracts'] })
      setOpen(false); form.resetFields(); setEditing(null)
      message.success('저장되었습니다')
    },
    onError: (e: any) => message.error(e.message),
  })

  const remove = useMutation({
    mutationFn: api.deleteContract,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['contracts'] }); message.success('삭제되었습니다') },
    onError: (e: any) => message.error(e.message),
  })

  const fmt = (n: number) => n.toLocaleString()

  const baseColumns = [
    { title: '품목', key: 'item', render: (_: any, r: Contract) => r.item?.name },
    { title: '업체', key: 'company', render: (_: any, r: Contract) => r.company?.name },
    { title: '단가', key: 'unit_price',
      render: (_: any, r: Contract) => `${fmt(r.unit_price)} ${r.item?.unit || ''}` },
    { title: '유형', dataIndex: 'unit_type', key: 'unit_type', width: 90,
      render: (v: string) => <Tag color={v === 'per_unit' ? 'geekblue' : 'purple'}>{v === 'per_unit' ? '단가×수량' : '고정금액'}</Tag> },
    { title: '적용일', dataIndex: 'effective_date', key: 'effective_date', width: 110 },
    { title: '비고', dataIndex: 'note', key: 'note' },
    {
      title: '', key: 'actions', width: 80,
      render: (_: any, record: Contract) => (
        <Space size={4}>
          <Button size="small" icon={<EditOutlined />} onClick={() => {
            setEditing(record)
            form.setFieldsValue({ ...record, effective_date: dayjs(record.effective_date) })
            setOpen(true)
          }} />
          <Popconfirm title="삭제하시겠습니까?" onConfirm={() => remove.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const historyColumns = [
    { title: '적용일', dataIndex: 'effective_date', key: 'effective_date', width: 110 },
    { title: '품목', key: 'item', render: (_: any, r: any) => r.item?.name },
    { title: '업체', key: 'company', render: (_: any, r: any) => r.company?.name },
    { title: '단가', key: 'unit_price',
      render: (_: any, r: any) => `${fmt(r.unit_price)} ${r.item?.unit || ''}` },
    {
      title: '변경', key: 'change',
      render: (_: any, r: any) => {
        if (r.prev_price == null) return <Tag color="default">최초 등록</Tag>
        const diff = r.unit_price - r.prev_price
        if (diff === 0) return <Typography.Text type="secondary">변동 없음</Typography.Text>
        return (
          <Space size={4}>
            {diff > 0
              ? <Tag color="red" icon={<ArrowUpOutlined />}>{fmt(Math.abs(diff))}</Tag>
              : <Tag color="blue" icon={<ArrowDownOutlined />}>{fmt(Math.abs(diff))}</Tag>
            }
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {fmt(r.prev_price)} → {fmt(r.unit_price)}
            </Typography.Text>
          </Space>
        )
      },
    },
    { title: '비고', dataIndex: 'note', key: 'note' },
  ]

  const filteredCurrent = applyFilter(currentContracts)
  const filteredHistory = applyFilter(historyContracts)

  return (
    <div style={SECTION_STYLE}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#888', fontSize: 13 }}>
          {view === 'current' ? `현재 단가 ${filteredCurrent.length}건` : `이력 ${filteredHistory.length}건`}
        </span>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setEditing(null); setOpen(true) }}>
          추가
        </Button>
      </div>

      <div style={FILTER_BAR}>
        <Select
          allowClear showSearch placeholder="품목 필터" style={{ width: 180 }}
          optionFilterProp="label" value={itemFilter} onChange={setItemFilter}
          options={items.map(i => ({ value: i.id, label: i.name }))}
        />
        <Select
          allowClear showSearch placeholder="업체 필터" style={{ width: 200 }}
          optionFilterProp="label" value={companyFilter} onChange={setCompanyFilter}
          options={companies.map(c => ({ value: c.id, label: c.name }))}
        />
        {(itemFilter || companyFilter) && (
          <Button size="small" onClick={() => { setItemFilter(undefined); setCompanyFilter(undefined) }}>
            필터 초기화
          </Button>
        )}
      </div>

      <Tabs
        size="small"
        activeKey={view}
        onChange={(k) => setView(k as 'current' | 'history')}
        items={[
          {
            key: 'current',
            label: '현재 단가',
            children: (
              <Table
                dataSource={filteredCurrent} columns={baseColumns} rowKey="id"
                loading={isLoading} size="small" pagination={false}
              />
            ),
          },
          {
            key: 'history',
            label: '변경 이력',
            children: (
              <Table
                dataSource={filteredHistory} columns={historyColumns} rowKey="id"
                loading={isLoading} size="small" pagination={{ pageSize: 30 }}
              />
            ),
          },
        ]}
      />

      <Modal title={editing ? '계약단가 수정' : '계약단가 추가'} open={open}
        onOk={() => form.submit()} onCancel={() => setOpen(false)} confirmLoading={save.isPending}>
        <Form form={form} layout="vertical" onFinish={save.mutate} style={{ marginTop: 16 }}>
          <Form.Item name="item_id" label="품목" rules={[{ required: true }]}>
            <Select showSearch placeholder="품목 선택" optionFilterProp="label"
              options={items.map(i => ({ value: i.id, label: i.name }))} />
          </Form.Item>
          <Form.Item name="company_id" label="업체" rules={[{ required: true }]}>
            <Select showSearch placeholder="업체 선택" optionFilterProp="label"
              options={companies.map(c => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="unit_price" label="단가" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={-9999999} />
          </Form.Item>
          <Form.Item name="unit_type" label="단가 유형" initialValue="per_unit">
            <Select>
              <Option value="per_unit">단가 × 수량</Option>
              <Option value="fixed">고정금액</Option>
            </Select>
          </Form.Item>
          <Form.Item name="effective_date" label="적용일" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="note" label="비고">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ── 메인 페이지 ──────────────────────────────────────────────────────────────

export default function MasterDataPage() {
  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: 20 }}>
      <h2 style={{ marginBottom: 16 }}>기준정보</h2>
      <Tabs
        items={[
          { key: 'items', label: '품목', children: <ItemsSection /> },
          { key: 'companies', label: '업체', children: <CompaniesSection /> },
          { key: 'contracts', label: '계약단가', children: <ContractsSection /> },
        ]}
      />
    </div>
  )
}
