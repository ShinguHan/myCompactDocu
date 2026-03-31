import { useState } from 'react'
import {
  Table, Button, DatePicker, Select, InputNumber, Input, Space,
  Form, Modal, Popconfirm, message, Tag, Upload, Alert, Divider, Typography,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined,
  UploadOutlined, SaveOutlined, PrinterOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import dayjs from 'dayjs'
import { api } from '../api'
import type { Transaction, ImportPreviewRow } from '../types'
import PhotoEditor from '../components/PhotoEditor'

const { RangePicker } = DatePicker
const { Text } = Typography

// ── 입력 폼 (배치 입력) ──────────────────────────────────────────────────────

function BatchEntryForm({ onSaved }: { onSaved: () => void }) {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const [rows, setRows] = useState<any[]>([])
  const [selectedItemId, setSelectedItemId] = useState<number | undefined>()

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: () => api.getItems() })
  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })
  const { data: itemCompanies = [] } = useQuery({
    queryKey: ['item-companies', selectedItemId],
    queryFn: () => api.getItemCompanies({ item_id: selectedItemId }),
    enabled: selectedItemId !== undefined,
  })
  const { data: itemContracts = [] } = useQuery({
    queryKey: ['contracts', selectedItemId],
    queryFn: () => api.getContracts({ item_id: selectedItemId }),
    enabled: selectedItemId !== undefined,
  })

  const filteredCompanies = selectedItemId !== undefined
    ? companies.filter(c =>
        itemCompanies.some(ic => ic.company_id === c.id) ||
        itemContracts.some(ct => ct.company_id === c.id)
      )
    : companies

  const save = useMutation({
    mutationFn: () => api.batchCreateTransactions(rows),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      setRows([])
      form.resetFields()
      message.success(`${rows.length}건 저장되었습니다`)
      onSaved()
    },
    onError: (e: any) => message.error(e.message),
  })

  const addRow = async () => {
    try {
      const values = await form.validateFields()
      const date = values.date.format('YYYY-MM-DD')
      const qty = values.quantity
      const unitPrice = values.unit_price
      const totalAmount = values.unit_type === 'fixed' ? unitPrice : qty * unitPrice

      setRows(prev => [...prev, {
        date, item_id: values.item_id, company_id: values.company_id,
        quantity: qty, unit_price: unitPrice, total_amount: totalAmount,
        note: values.note || null,
        _item_name: items.find(i => i.id === values.item_id)?.name,
        _company_name: companies.find(c => c.id === values.company_id)?.name,
      }])
      form.setFieldsValue({ item_id: undefined, company_id: undefined, quantity: undefined, unit_price: undefined, note: undefined })
    } catch { /* validation error */ }
  }

  const onItemChange = async (itemId: number) => {
    setSelectedItemId(itemId)
    form.setFieldsValue({ company_id: undefined })
    const dateVal = form.getFieldValue('date')
    if (!itemId || !dateVal) return
    const companyId = form.getFieldValue('company_id')
    if (!companyId) return
    const contract = await api.getActiveContract(itemId, companyId, dateVal.format('YYYY-MM-DD'))
    if (contract) form.setFieldsValue({ unit_price: contract.unit_price })
  }

  const onCompanyChange = async (companyId: number) => {
    const itemId = form.getFieldValue('item_id')
    const dateVal = form.getFieldValue('date')
    if (!itemId || !companyId || !dateVal) return
    const contract = await api.getActiveContract(itemId, companyId, dateVal.format('YYYY-MM-DD'))
    if (contract) form.setFieldsValue({ unit_price: contract.unit_price })
  }

  return (
    <div style={{ background: '#fff', padding: 16, borderRadius: 8, marginBottom: 16 }}>
      <Form form={form} layout="inline" style={{ gap: 8, flexWrap: 'wrap' }}>
        <Form.Item name="date" label="일자" rules={[{ required: true, message: '일자 필수' }]}>
          <DatePicker />
        </Form.Item>
        <Form.Item name="item_id" label="품목" rules={[{ required: true, message: '품목 필수' }]}>
          <Select showSearch style={{ width: 160 }} placeholder="품목"
            optionFilterProp="label" onChange={onItemChange}
            options={items.map(i => ({ value: i.id, label: i.name }))} />
        </Form.Item>
        <Form.Item name="company_id" label="업체" rules={[{ required: true, message: '업체 필수' }]}>
          <Select showSearch style={{ width: 200 }} placeholder="업체"
            optionFilterProp="label" onChange={onCompanyChange}
            options={filteredCompanies.map(c => ({ value: c.id, label: c.name }))} />
        </Form.Item>
        <Form.Item name="quantity" label="처리량" rules={[{ required: true, message: '처리량 필수' }]}>
          <InputNumber style={{ width: 120 }} placeholder="수량" />
        </Form.Item>
        <Form.Item name="unit_price" label="단가" rules={[{ required: true, message: '단가 필수' }]}>
          <InputNumber style={{ width: 120 }} placeholder="단가" />
        </Form.Item>
        <Form.Item name="note" label="비고">
          <Input style={{ width: 160 }} placeholder="비고" />
        </Form.Item>
        <Form.Item>
          <Button icon={<PlusOutlined />} onClick={addRow}>행 추가</Button>
        </Form.Item>
      </Form>

      {rows.length > 0 && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <Table
            size="small"
            dataSource={rows.map((r, i) => ({ ...r, key: i }))}
            columns={[
              { title: '일자', dataIndex: 'date', width: 100 },
              { title: '품목', dataIndex: '_item_name' },
              { title: '업체', dataIndex: '_company_name' },
              { title: '처리량', dataIndex: 'quantity', align: 'right' as const },
              { title: '단가', dataIndex: 'unit_price', align: 'right' as const,
                render: (v: number) => v.toLocaleString() },
              { title: '금액', dataIndex: 'total_amount', align: 'right' as const,
                render: (v: number) => v.toLocaleString() },
              { title: '비고', dataIndex: 'note' },
              { title: '', key: 'del', width: 40,
                render: (_: any, __: any, idx: number) => (
                  <Button size="small" danger icon={<DeleteOutlined />}
                    onClick={() => setRows(r => r.filter((_, i) => i !== idx))} />
                ) },
            ]}
            pagination={false}
          />
          <div style={{ marginTop: 12, textAlign: 'right' }}>
            <Text type="secondary" style={{ marginRight: 16 }}>
              총 {rows.length}건 / 합계: {rows.reduce((s, r) => s + r.total_amount, 0).toLocaleString()}원
            </Text>
            <Button type="primary" icon={<SaveOutlined />}
              loading={save.isPending} onClick={() => save.mutate()}>
              저장
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

// ── 엑셀 임포트 모달 ─────────────────────────────────────────────────────────

function ImportModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [preview, setPreview] = useState<{ rows: ImportPreviewRow[]; new_count: number; duplicate_count: number; unknown_items: string[] } | null>(null)
  const [_uploading, setUploading] = useState(false)

  const doImport = async () => {
    message.info('임포트 기능은 기준정보 등록 후 사용 가능합니다')
  }

  const handleFile = async (file: File) => {
    setUploading(true)
    try {
      const result = await api.importPreview(file)
      setPreview(result)
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setUploading(false)
    }
    return false
  }

  return (
    <Modal title="엑셀 임포트" open={open} onCancel={onClose}
      footer={preview ? [
        <Button key="cancel" onClick={onClose}>취소</Button>,
        <Button key="ok" type="primary" onClick={doImport}>
          신규 {preview.new_count}건 저장
        </Button>,
      ] : null}
      width={900}
    >
      {!preview ? (
        <Upload.Dragger beforeUpload={handleFile} accept=".xlsx,.xls" showUploadList={false}>
          <p><UploadOutlined style={{ fontSize: 32 }} /></p>
          <p>엑셀 파일을 여기에 끌어다 놓거나 클릭하여 선택하세요</p>
          <p style={{ color: '#aaa', fontSize: 12 }}>'폐기물, 부산물 입출고대장' 시트가 포함된 파일</p>
        </Upload.Dragger>
      ) : (
        <>
          <Space style={{ marginBottom: 12 }}>
            <Tag color="green">신규 {preview.new_count}건</Tag>
            <Tag color="orange">중복 {preview.duplicate_count}건 (건너뜀)</Tag>
            {preview.unknown_items.length > 0 && (
              <Alert type="warning" showIcon
                message={`미등록 품목: ${preview.unknown_items.join(', ')}`} />
            )}
          </Space>
          <Table
            size="small"
            dataSource={preview.rows.map((r, i) => ({ ...r, key: i }))}
            columns={[
              { title: '일자', dataIndex: 'date', width: 100 },
              { title: '품목', dataIndex: 'item_name' },
              { title: '업체', dataIndex: 'company_name' },
              { title: '수량', dataIndex: 'quantity', align: 'right' as const },
              { title: '금액', dataIndex: 'total_amount', align: 'right' as const,
                render: (v: number) => v.toLocaleString() },
              { title: '상태', dataIndex: 'is_duplicate',
                render: (v: boolean) => v ? <Tag color="orange">중복</Tag> : <Tag color="green">신규</Tag> },
            ]}
            pagination={{ pageSize: 20 }}
            scroll={{ y: 400 }}
          />
        </>
      )}
    </Modal>
  )
}

// ── 빠른 반출증 생성 모달 ────────────────────────────────────────────────────

function QuickExitPassModal({
  open,
  selectedTxs,
  onClose,
}: {
  open: boolean
  selectedTxs: Transaction[]
  onClose: () => void
}) {
  const qc = useQueryClient()
  const [photo, setPhoto] = useState<File | null>(null)
  const [done, setDone] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [photoEditorOpen, setPhotoEditorOpen] = useState(false)

  // 선택된 행들은 모두 같은 날짜+업체여야 함 (UI에서 검증)
  const date = selectedTxs[0]?.date ?? ''
  const company = selectedTxs[0]?.company
  const txIds = selectedTxs.map(t => t.id)

  const create = useMutation({
    mutationFn: async () => {
      const ep = await api.createExitPass({ date, company_id: company!.id, transaction_ids: txIds })
      if (photo) await api.uploadExitPassPhoto(ep.id, photo)
      const blob = await api.downloadExitPass(ep.id)
      const url = URL.createObjectURL(blob)
      setDownloadUrl(url)
      return ep
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exit-passes'] })
      setDone(true)
    },
    onError: (e: any) => message.error(e.message),
  })

  const handleClose = () => {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl)
    setDone(false); setPhoto(null); setDownloadUrl(null); setPhotoEditorOpen(false)
    onClose()
  }

  const fmt = (n: number) => n.toLocaleString()

  return (
    <>
    <Modal
      title="반출증 바로 출력"
      open={open}
      onCancel={handleClose}
      width={560}
      footer={
        done ? (
          <Space>
            <Button type="primary" href={downloadUrl!} download={`반출증_${date}_${company?.name}.xlsx`}>
              엑셀 다운로드
            </Button>
            <Button onClick={handleClose}>닫기</Button>
          </Space>
        ) : (
          <Space>
            <Button onClick={handleClose}>취소</Button>
            <Button type="primary" loading={create.isPending} onClick={() => create.mutate()}>
              반출증 생성 및 출력
            </Button>
          </Space>
        )
      }
    >
      {!done ? (
        <>
          <div style={{ background: '#f6f8fa', borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <div style={{ marginBottom: 8, color: '#666', fontSize: 13 }}>
              <strong>{date}</strong> · <strong>{company?.name}</strong>
            </div>
            <Table
              size="small"
              pagination={false}
              dataSource={selectedTxs.map(t => ({ ...t, key: t.id }))}
              columns={[
                { title: '품목', render: (_: any, r: Transaction) => r.item?.name },
                { title: '처리량', dataIndex: 'quantity', align: 'right' as const },
                { title: '단가', dataIndex: 'unit_price', align: 'right' as const,
                  render: (v: number) => fmt(v) },
                { title: '금액', dataIndex: 'total_amount', align: 'right' as const,
                  render: (v: number) => <span style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v)}</span> },
              ]}
            />
          </div>
          <div>
            <div style={{ marginBottom: 6, fontWeight: 500 }}>반출 사진 첨부 (선택)</div>
            <Space>
              <Button icon={<UploadOutlined />} onClick={() => setPhotoEditorOpen(true)}>
                {photo ? '사진 다시 편집' : '사진 편집 후 첨부'}
              </Button>
              {photo && <span style={{ color: '#666', fontSize: 13 }}>{photo.name}</span>}
            </Space>
            {photo && (
              <div style={{ marginTop: 8 }}>
                <img
                  src={URL.createObjectURL(photo)}
                  alt="preview"
                  style={{ maxWidth: '100%', maxHeight: 140, borderRadius: 6, border: '1px solid #eee' }}
                />
              </div>
            )}
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <div>반출증이 생성되었습니다. 아래 버튼으로 다운로드하세요.</div>
        </div>
      )}
    </Modal>

    <PhotoEditor
      open={photoEditorOpen}
      onClose={() => setPhotoEditorOpen(false)}
      onDone={(file) => { setPhoto(file); setPhotoEditorOpen(false) }}
    />
    </>
  )
}

// ── 메인 페이지 ──────────────────────────────────────────────────────────────

export default function LedgerPage() {
  const qc = useQueryClient()
  const [form] = Form.useForm()
  const currentYear = dayjs().year()
  const [selectedYear, setSelectedYear] = useState<number>(currentYear)
  const [filters, setFilters] = useState<{ start?: string; end?: string; company_id?: number; item_id?: number }>({
    start: `${currentYear}-01-01`,
    end: `${currentYear}-12-31`,
  })
  const [editingTx, setEditingTx] = useState<Transaction | null>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [editItemId, setEditItemId] = useState<number | undefined>()
  const [importOpen, setImportOpen] = useState(false)
  const [showEntry, setShowEntry] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [quickExitOpen, setQuickExitOpen] = useState(false)

  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => api.getTransactions({ ...filters, size: 500 }),
  })
  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: () => api.getItems() })
  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })
  const { data: editItemCompanies = [] } = useQuery({
    queryKey: ['item-companies', editItemId],
    queryFn: () => api.getItemCompanies({ item_id: editItemId }),
    enabled: editItemId !== undefined,
  })
  const { data: editItemContracts = [] } = useQuery({
    queryKey: ['contracts', editItemId],
    queryFn: () => api.getContracts({ item_id: editItemId }),
    enabled: editItemId !== undefined,
  })
  const editFilteredCompanies = editItemId !== undefined
    ? companies.filter(c =>
        editItemCompanies.some(ic => ic.company_id === c.id) ||
        editItemContracts.some(ct => ct.company_id === c.id)
      )
    : companies

  const remove = useMutation({
    mutationFn: api.deleteTransaction,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['transactions'] }); message.success('삭제되었습니다') },
    onError: (e: any) => message.error(e.message),
  })

  const update = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) => {
      const payload = { ...values, date: values.date.format('YYYY-MM-DD') }
      payload.total_amount = payload.quantity * payload.unit_price
      return api.updateTransaction(id, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      setEditOpen(false); setEditingTx(null)
      message.success('수정되었습니다')
    },
    onError: (e: any) => message.error(e.message),
  })

  const fmt = (n: number) => n.toLocaleString()
  const totalAmt = transactions.reduce((s, t) => s + t.total_amount, 0)

  const selectedTxs = transactions.filter(t => selectedRowKeys.includes(t.id))

  // 선택된 행들의 날짜+업체 일치 여부 검증
  const selectionValid = selectedTxs.length > 0 && (() => {
    const first = selectedTxs[0]
    return selectedTxs.every(t => t.date === first.date && t.company_id === first.company_id)
  })()

  const handleQuickExit = () => {
    if (!selectionValid) {
      message.warning('같은 날짜, 같은 업체의 행만 선택해 주세요')
      return
    }
    setQuickExitOpen(true)
  }

  const columns = [
    { title: '일자', dataIndex: 'date', key: 'date', width: 100,
      sorter: (a: Transaction, b: Transaction) => a.date.localeCompare(b.date) },
    { title: '품목', key: 'item', render: (_: any, r: Transaction) => r.item?.name },
    { title: '업체', key: 'company', render: (_: any, r: Transaction) => r.company?.name },
    { title: '처리량', dataIndex: 'quantity', key: 'quantity', align: 'right' as const },
    { title: '단가', dataIndex: 'unit_price', key: 'unit_price', align: 'right' as const,
      render: (v: number) => fmt(v) },
    { title: '금액', dataIndex: 'total_amount', key: 'total_amount', align: 'right' as const,
      render: (v: number) => <span style={{ color: v < 0 ? '#cf1322' : undefined }}>{fmt(v)}</span> },
    { title: '비고', dataIndex: 'note', key: 'note' },
    {
      title: '', key: 'actions', width: 80,
      render: (_: any, record: Transaction) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => {
            setEditingTx(record)
            setEditItemId(record.item_id)
            form.setFieldsValue({ ...record, date: dayjs(record.date) })
            setEditOpen(true)
          }} />
          <Popconfirm title="삭제하시겠습니까?" onConfirm={() => remove.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>입출고대장</h2>
        <Space>
          <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>엑셀 임포트</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowEntry(v => !v)}>
            {showEntry ? '입력 접기' : '데이터 입력'}
          </Button>
        </Space>
      </div>

      {showEntry && <BatchEntryForm onSaved={() => setShowEntry(false)} />}

      {/* 필터 */}
      <div style={{ background: '#fff', padding: '12px 16px', borderRadius: 8, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          value={selectedYear}
          style={{ width: 90 }}
          onChange={(year: number) => {
            setSelectedYear(year)
            setFilters(f => ({ ...f, start: `${year}-01-01`, end: `${year}-12-31` }))
          }}
          options={Array.from({ length: 5 }, (_, i) => currentYear - i).map(y => ({ value: y, label: `${y}년` }))}
        />
        <RangePicker onChange={(dates) => setFilters(f => ({
          ...f,
          start: dates?.[0]?.format('YYYY-MM-DD'),
          end: dates?.[1]?.format('YYYY-MM-DD'),
        }))} />
        <Select allowClear style={{ width: 200 }} placeholder="업체 필터"
          onChange={(v) => setFilters(f => ({ ...f, company_id: v }))}
          options={companies.map(c => ({ value: c.id, label: c.name }))} />
        <Select allowClear style={{ width: 160 }} placeholder="품목 필터"
          onChange={(v) => setFilters(f => ({ ...f, item_id: v }))}
          options={items.map(i => ({ value: i.id, label: i.name }))} />
      </div>

      {/* 선택 시 반출증 툴바 */}
      {selectedRowKeys.length > 0 && (
        <div style={{
          background: '#e6f4ff', border: '1px solid #91caff', borderRadius: 8,
          padding: '10px 16px', marginBottom: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ color: '#0958d9' }}>
            <strong>{selectedRowKeys.length}건</strong> 선택됨
            {selectedTxs.length > 0 && (
              <span style={{ marginLeft: 12, color: '#666', fontSize: 13 }}>
                합계: {fmt(selectedTxs.reduce((s, t) => s + t.total_amount, 0))}원
              </span>
            )}
            {!selectionValid && (
              <span style={{ marginLeft: 12, color: '#ff7875', fontSize: 13 }}>
                ⚠ 같은 날짜·업체만 선택해야 반출증 출력 가능
              </span>
            )}
          </span>
          <Space>
            <Button size="small" onClick={() => setSelectedRowKeys([])}>선택 해제</Button>
            <Button
              size="small" type="primary"
              icon={<PrinterOutlined />}
              disabled={!selectionValid}
              onClick={handleQuickExit}
            >
              반출증 출력
            </Button>
          </Space>
        </div>
      )}

      {/* 합계 */}
      <div style={{ marginBottom: 8, textAlign: 'right', color: '#666', fontSize: 13 }}>
        총 {transactions.length}건 | 합계: <strong>{fmt(totalAmt)}</strong>원
      </div>

      <Table
        dataSource={transactions}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: true }}
        scroll={{ x: 'max-content' }}
        style={{ background: '#fff', borderRadius: 8 }}
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys as number[]),
        }}
      />

      {/* 수정 모달 */}
      <Modal title="거래 수정" open={editOpen}
        onOk={() => form.submit()} onCancel={() => setEditOpen(false)}
        confirmLoading={update.isPending}>
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}
          onFinish={(values) => editingTx && update.mutate({ id: editingTx.id, values })}>
          <Form.Item name="date" label="일자" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="item_id" label="품목" rules={[{ required: true }]}>
            <Select options={items.map(i => ({ value: i.id, label: i.name }))}
              onChange={(id: number) => { setEditItemId(id); form.setFieldsValue({ company_id: undefined }) }} />
          </Form.Item>
          <Form.Item name="company_id" label="업체" rules={[{ required: true }]}>
            <Select options={editFilteredCompanies.map(c => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="quantity" label="처리량" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit_price" label="단가" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="note" label="비고">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <ImportModal open={importOpen} onClose={() => setImportOpen(false)} />

      {quickExitOpen && selectedTxs.length > 0 && (
        <QuickExitPassModal
          open={quickExitOpen}
          selectedTxs={selectedTxs}
          onClose={() => { setQuickExitOpen(false); setSelectedRowKeys([]) }}
        />
      )}
    </div>
  )
}
