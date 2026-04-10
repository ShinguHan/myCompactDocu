import { useState } from 'react'
import {
  Table, Button, Modal, DatePicker, Select, Checkbox, Space,
  message, Tag, Popconfirm, Steps, Typography,
} from 'antd'
import {
  PlusOutlined, DownloadOutlined, DeleteOutlined, CameraOutlined, SearchOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { api } from '../api'
import type { ExitPass, ExitPassTransaction } from '../types'
import PhotoEditor from '../components/PhotoEditor'

const { Text } = Typography

const fmt = (n: number) => n.toLocaleString()
const compareText = (a?: string | null, b?: string | null) => (a || '').localeCompare(b || '', 'ko')

function CreateExitPassModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [step, setStep] = useState(0)
  const [date, setDate] = useState<string>('')
  const [companyId, setCompanyId] = useState<number | undefined>()
  const [selectedTxIds, setSelectedTxIds] = useState<number[]>([])
  const [photo, setPhoto] = useState<File | null>(null)
  const [createdId, setCreatedId] = useState<number | null>(null)
  const [photoEditorOpen, setPhotoEditorOpen] = useState(false)

  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })
  const { data: groups = [] } = useQuery({
    queryKey: ['transactions-grouped', date],
    queryFn: () => api.getGroupedTransactions({ start: date, end: date }),
    enabled: !!date,
  })

  const companyGroups = groups.filter(g => g.company_id === companyId)

  const create = useMutation({
    mutationFn: () => api.createExitPass({ date, company_id: companyId!, transaction_ids: selectedTxIds }),
    onSuccess: async (ep) => {
      setCreatedId(ep.id)
      if (photo) {
        await api.uploadExitPassPhoto(ep.id, photo)
      }
      qc.invalidateQueries({ queryKey: ['exit-passes'] })
      setStep(2)
    },
    onError: (e: any) => message.error(e.message),
  })

  const reset = () => {
    setStep(0); setDate(''); setCompanyId(undefined)
    setSelectedTxIds([]); setPhoto(null); setCreatedId(null)
    onClose()
  }

  const handleDownload = async () => {
    if (!createdId) return
    try {
      const blob = await api.downloadExitPass(createdId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `반출증_${date}.xlsx`; a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) { message.error(e.message) }
  }

  const steps = [
    {
      title: '날짜/업체 선택',
      content: (
        <Space direction="vertical" style={{ width: '100%', marginTop: 16 }}>
          <div>
            <label>반출일자</label>
            <DatePicker style={{ width: '100%', marginTop: 4 }}
              onChange={(d) => d && setDate(d.format('YYYY-MM-DD'))} />
          </div>
          <div>
            <label>업체</label>
            <Select style={{ width: '100%', marginTop: 4 }} placeholder="업체 선택"
              onChange={setCompanyId} options={companies.map(c => ({ value: c.id, label: c.name }))} />
          </div>
        </Space>
      ),
    },
    {
      title: '품목 선택',
      content: (
        <div style={{ marginTop: 16 }}>
          {companyGroups.length === 0 && (
            <Text type="secondary">해당 날짜/업체의 거래 내역이 없습니다</Text>
          )}
          {companyGroups.map((g: any) => (
            <div key={g.date + g.company_id}>
              {g.transactions.map((tx: any) => (
                <div key={tx.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <Checkbox
                    checked={selectedTxIds.includes(tx.id)}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedTxIds(prev => [...prev, tx.id])
                      else setSelectedTxIds(prev => prev.filter(id => id !== tx.id))
                    }}
                  >
                    <Space>
                      <span>{tx.item_name}</span>
                      <Text type="secondary">{tx.quantity.toLocaleString()} / {tx.total_amount.toLocaleString()}원</Text>
                    </Space>
                  </Checkbox>
                </div>
              ))}
            </div>
          ))}
          <div style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 6, fontWeight: 500 }}>반출 사진 (선택)</div>
            <Space>
              <Button icon={<CameraOutlined />} onClick={() => setPhotoEditorOpen(true)}>
                {photo ? '사진 다시 편집' : '사진 편집 후 첨부'}
              </Button>
              {photo && (
                <Text type="secondary" style={{ fontSize: 13 }}>
                  {photo.name}
                </Text>
              )}
            </Space>
            {photo && (
              <div style={{ marginTop: 8 }}>
                <img
                  src={URL.createObjectURL(photo)}
                  alt="preview"
                  style={{ maxWidth: '100%', maxHeight: 160, borderRadius: 6, border: '1px solid #eee' }}
                />
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      title: '완료',
      content: (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <Text>반출증이 생성되었습니다</Text>
          <div style={{ marginTop: 16 }}>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
              엑셀 다운로드
            </Button>
          </div>
        </div>
      ),
    },
  ]

  const canNext = step === 0 ? (!!date && !!companyId) : step === 1 ? selectedTxIds.length > 0 : false

  return (
    <>
      <Modal
        title="반출증 생성"
        open={open}
        onCancel={reset}
        width={560}
        footer={
          step < 2 ? [
            <Button key="cancel" onClick={reset}>취소</Button>,
            step === 1 && <Button key="back" onClick={() => setStep(0)}>이전</Button>,
            <Button key="next" type="primary" disabled={!canNext}
              loading={create.isPending}
              onClick={() => step === 0 ? setStep(1) : create.mutate()}>
              {step === 0 ? '다음' : '반출증 생성'}
            </Button>,
          ] : [
            <Button key="close" type="primary" onClick={reset}>닫기</Button>,
          ]
        }
      >
        <Steps current={step} items={steps.map(s => ({ title: s.title }))} style={{ marginBottom: 16 }} />
        {steps[step].content}
      </Modal>

      <PhotoEditor
        open={photoEditorOpen}
        onClose={() => setPhotoEditorOpen(false)}
        onDone={(file) => { setPhoto(file); setPhotoEditorOpen(false) }}
      />
    </>
  )
}

const { RangePicker } = DatePicker

export default function ExitPassPage() {
  const qc = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [photoEditTarget, setPhotoEditTarget] = useState<ExitPass | null>(null)
  const [filters, setFilters] = useState<{ company_id?: number; start?: string; end?: string }>({})

  const { data: companies = [] } = useQuery({ queryKey: ['companies'], queryFn: api.getCompanies })

  const { data: exitPasses = [], isLoading } = useQuery({
    queryKey: ['exit-passes', filters],
    queryFn: () => api.getExitPasses(filters),
  })

  const remove = useMutation({
    mutationFn: api.deleteExitPass,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['exit-passes'] }); message.success('삭제되었습니다') },
    onError: (e: any) => message.error(e.message),
  })

  const handleDownload = async (ep: ExitPass) => {
    try {
      const blob = await api.downloadExitPass(ep.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `반출증_${ep.date}_${ep.company.name}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) { message.error(e.message) }
  }

  const handlePhotoEditDone = async (file: File) => {
    if (!photoEditTarget) return
    try {
      await api.uploadExitPassPhoto(photoEditTarget.id, file)
      qc.invalidateQueries({ queryKey: ['exit-passes'] })
      message.success('사진이 업데이트되었습니다')
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setPhotoEditTarget(null)
    }
  }

  const columns = [
    {
      title: '반출증 번호',
      dataIndex: 'number',
      key: 'number',
      width: 120,
      sorter: (a: ExitPass, b: ExitPass) => a.number - b.number,
      render: (v: number) => String(v).padStart(4, '0'),
    },
    {
      title: '반출일',
      dataIndex: 'date',
      key: 'date',
      width: 110,
      sorter: (a: ExitPass, b: ExitPass) => a.date.localeCompare(b.date),
    },
    {
      title: '업체',
      key: 'company',
      sorter: (a: ExitPass, b: ExitPass) => compareText(a.company?.name, b.company?.name),
      render: (_: any, r: ExitPass) => r.company?.name,
    },
    { title: '품목 수', key: 'items',
      sorter: (a: ExitPass, b: ExitPass) => (a.transactions?.length || 0) - (b.transactions?.length || 0),
      render: (_: any, r: ExitPass) => `${r.transactions?.length || 0}건` },
    { title: '사진', key: 'photo',
      sorter: (a: ExitPass, b: ExitPass) => Number(!!a.photo_path) - Number(!!b.photo_path),
      render: (_: any, r: ExitPass) =>
        r.photo_path
          ? <Tag color="green">있음</Tag>
          : <Tag color="default">없음</Tag>
    },
    { title: '생성일시', dataIndex: 'created_at', key: 'created_at',
      defaultSortOrder: 'descend' as const,
      sorter: (a: ExitPass, b: ExitPass) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf(),
      render: (v: string) => dayjs(v).format('MM/DD HH:mm') },
    {
      title: '', key: 'actions', width: 160,
      render: (_: any, record: ExitPass) => (
        <Space>
          <Button size="small" icon={<CameraOutlined />} onClick={() => setPhotoEditTarget(record)}>
            사진
          </Button>
          <Button size="small" icon={<DownloadOutlined />} onClick={() => handleDownload(record)}>
            출력
          </Button>
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
        <h2>반출증 발행 이력</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          반출증 생성
        </Button>
      </div>

      {/* 필터 */}
      <div style={{ background: '#fff', padding: '12px 16px', borderRadius: 8, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <SearchOutlined style={{ color: '#bbb' }} />
        <RangePicker
          onChange={(dates) => setFilters(f => ({
            ...f,
            start: dates?.[0]?.format('YYYY-MM-DD'),
            end: dates?.[1]?.format('YYYY-MM-DD'),
          }))}
        />
        <Select
          allowClear
          showSearch
          placeholder="업체 필터"
          style={{ width: 200 }}
          optionFilterProp="label"
          options={companies.map(c => ({ value: c.id, label: c.name }))}
          onChange={(v) => setFilters(f => ({ ...f, company_id: v }))}
        />
        <span style={{ color: '#888', fontSize: 13 }}>총 {exitPasses.length}건</span>
      </div>

      <Table
        dataSource={exitPasses}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        size="small"
        style={{ background: '#fff', borderRadius: 8 }}
        pagination={{ pageSize: 30 }}
        expandable={{
          expandedRowRender: (record: ExitPass) => (
            <Table
              size="small"
              pagination={false}
              dataSource={record.transactions.map(t => ({ ...t, key: t.id }))}
              columns={[
                { title: '품목', render: (_: any, r: ExitPassTransaction) => r.transaction.item?.name },
                { title: '처리량', align: 'right' as const,
                  render: (_: any, r: ExitPassTransaction) => r.transaction.quantity.toLocaleString() },
                { title: '단가', align: 'right' as const,
                  render: (_: any, r: ExitPassTransaction) => `${fmt(r.transaction.unit_price)}원` },
                { title: '금액', align: 'right' as const,
                  render: (_: any, r: ExitPassTransaction) => (
                    <span style={{ color: r.transaction.total_amount < 0 ? '#cf1322' : undefined }}>
                      {fmt(r.transaction.total_amount)}원
                    </span>
                  )},
              ]}
              summary={() => {
                const total = record.transactions.reduce((s, t) => s + t.transaction.total_amount, 0)
                return (
                  <Table.Summary.Row style={{ fontWeight: 600 }}>
                    <Table.Summary.Cell index={0} colSpan={3}>합계</Table.Summary.Cell>
                    <Table.Summary.Cell index={3} align="right">
                      <span style={{ color: total < 0 ? '#cf1322' : '#1677ff' }}>{fmt(total)}원</span>
                    </Table.Summary.Cell>
                  </Table.Summary.Row>
                )
              }}
            />
          ),
          rowExpandable: (record: ExitPass) => record.transactions.length > 0,
        }}
      />

      <CreateExitPassModal open={createOpen} onClose={() => setCreateOpen(false)} />

      <PhotoEditor
        open={!!photoEditTarget}
        onClose={() => setPhotoEditTarget(null)}
        onDone={handlePhotoEditDone}
      />
    </div>
  )
}
