import { useState, useCallback } from 'react'
import Cropper from 'react-easy-crop'
import { Modal, Slider, Button, Space, Upload, InputNumber, Tooltip } from 'antd'
import { CloseOutlined, RotateLeftOutlined, RotateRightOutlined, UploadOutlined } from '@ant-design/icons'

interface Area {
  x: number
  y: number
  width: number
  height: number
}

interface Props {
  open: boolean
  onClose: () => void
  onDone: (file: File) => void
}

// ── 비율 localStorage 저장/로드 ───────────────────────────────────────────────

const ASPECT_KEY = 'photo_editor_aspect'

function loadAspect() {
  try {
    const s = localStorage.getItem(ASPECT_KEY)
    if (s) {
      const { w, h } = JSON.parse(s)
      if (w > 0 && h > 0) return { w: Number(w), h: Number(h) }
    }
  } catch { /* ignore */ }
  return { w: 3, h: 4 }
}

function saveAspect(w: number, h: number) {
  try { localStorage.setItem(ASPECT_KEY, JSON.stringify({ w, h })) } catch { /* ignore */ }
}

const PRESETS = [
  { label: '3:4', w: 3, h: 4 },
  { label: '1:1', w: 1, h: 1 },
  { label: '4:3', w: 4, h: 3 },
  { label: '9:16', w: 9, h: 16 },
  { label: '16:9', w: 16, h: 9 },
]

// ── 크롭 처리 ─────────────────────────────────────────────────────────────────

async function getCroppedFile(
  imageSrc: string,
  pixelCrop: Area,
  rotation: number,
  fileName: string
): Promise<File> {
  const image = await new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image()
    img.addEventListener('load', () => resolve(img))
    img.addEventListener('error', reject)
    img.src = imageSrc
  })

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')!

  const rad = (rotation * Math.PI) / 180
  const sin = Math.abs(Math.sin(rad))
  const cos = Math.abs(Math.cos(rad))
  const bboxW = image.width * cos + image.height * sin
  const bboxH = image.width * sin + image.height * cos

  canvas.width = pixelCrop.width
  canvas.height = pixelCrop.height

  ctx.translate(-pixelCrop.x, -pixelCrop.y)
  ctx.translate(bboxW / 2, bboxH / 2)
  ctx.rotate(rad)
  ctx.translate(-image.width / 2, -image.height / 2)
  ctx.drawImage(image, 0, 0)

  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (!blob) { reject(new Error('Canvas is empty')); return }
      resolve(new File([blob], fileName, { type: 'image/jpeg' }))
    }, 'image/jpeg', 0.92)
  })
}

// ── 컴포넌트 ──────────────────────────────────────────────────────────────────

export default function PhotoEditor({ open, onClose, onDone }: Props) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [fileName, setFileName] = useState('photo.jpg')
  const [crop, setCrop] = useState({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null)
  const [saving, setSaving] = useState(false)
  const [aspectW, setAspectW] = useState(() => loadAspect().w)
  const [aspectH, setAspectH] = useState(() => loadAspect().h)

  const aspect = aspectW / aspectH

  const onCropComplete = useCallback((_: Area, pixels: Area) => {
    setCroppedAreaPixels(pixels)
  }, [])

  const handleFile = (file: File) => {
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = () => setImageSrc(reader.result as string)
    reader.readAsDataURL(file)
    return false
  }

  const handleDone = async () => {
    if (!imageSrc || !croppedAreaPixels) return
    setSaving(true)
    try {
      const file = await getCroppedFile(imageSrc, croppedAreaPixels, rotation, fileName)
      onDone(file)
      handleClose()
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    setImageSrc(null)
    setCrop({ x: 0, y: 0 })
    setZoom(1)
    setRotation(0)
    setCroppedAreaPixels(null)
    onClose()
  }

  const applyPreset = (w: number, h: number) => {
    setAspectW(w); setAspectH(h)
    saveAspect(w, h)
    setCrop({ x: 0, y: 0 })
  }

  const handleCustomW = (v: number | null) => {
    if (v && v > 0) { setAspectW(v); saveAspect(v, aspectH); setCrop({ x: 0, y: 0 }) }
  }
  const handleCustomH = (v: number | null) => {
    if (v && v > 0) { setAspectH(v); saveAspect(aspectW, v); setCrop({ x: 0, y: 0 }) }
  }

  const isPresetActive = (w: number, h: number) => aspectW === w && aspectH === h

  return (
    <Modal
      open={open}
      footer={null}
      title={null}
      closable={false}
      width="100%"
      style={{ top: 0, padding: 0, margin: 0, maxWidth: '100vw' }}
      styles={{
        wrapper: { overflow: 'hidden' },
        body: { padding: 0 },
      }}
    >
      {/* 전체를 body 안에서 직접 flex 제어 — 100vh 고정 */}
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* ── 헤더 ── */}
        <div style={{
          flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 20px', height: 48,
          borderBottom: '1px solid #f0f0f0', background: '#fff',
        }}>
          <span style={{ fontWeight: 600, fontSize: 16 }}>사진 편집</span>
          <Button type="text" icon={<CloseOutlined />} onClick={handleClose} />
        </div>

        {!imageSrc ? (
          /* ── 업로드 단계 ── */
          <Upload.Dragger
            accept="image/*"
            beforeUpload={handleFile}
            showUploadList={false}
            style={{ flex: 1, border: 'none', borderRadius: 0 }}
          >
            <UploadOutlined style={{ fontSize: 48, color: '#1677ff' }} />
            <p style={{ marginTop: 16, fontSize: 16 }}>사진을 여기에 끌어다 놓거나 클릭하여 선택</p>
            <p style={{ color: '#aaa', fontSize: 13, marginTop: 4 }}>JPG, PNG 지원</p>
          </Upload.Dragger>
        ) : (
          <>
            {/* ── 크롭 영역 — flex:1 로 남은 공간 전부 ── */}
            <div style={{ flex: 1, position: 'relative', background: '#111', minHeight: 0 }}>
              <Cropper
                image={imageSrc}
                crop={crop}
                zoom={zoom}
                rotation={rotation}
                aspect={aspect}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={onCropComplete}
              />
            </div>

            {/* ── 컨트롤 바 ── */}
            <div style={{
              flexShrink: 0,
              background: '#1a1a1a',
              padding: '10px 20px',
              display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
            }}>
              <span style={{ color: '#aaa', fontSize: 13 }}>확대</span>
              <Slider style={{ flex: 2, minWidth: 80 }} min={1} max={3} step={0.05}
                value={zoom} onChange={setZoom} />

              <span style={{ color: '#aaa', fontSize: 13 }}>회전</span>
              <Slider style={{ flex: 2, minWidth: 80 }} min={-180} max={180} step={1}
                value={rotation} onChange={setRotation} />
              <Space>
                <Button size="small" icon={<RotateLeftOutlined />} onClick={() => setRotation(r => r - 90)} />
                <Button size="small" icon={<RotateRightOutlined />} onClick={() => setRotation(r => r + 90)} />
              </Space>

              <div style={{ width: 1, height: 20, background: '#444', flexShrink: 0 }} />

              <span style={{ color: '#aaa', fontSize: 13 }}>비율</span>
              <Space size={4}>
                {PRESETS.map(p => (
                  <Button key={p.label} size="small"
                    type={isPresetActive(p.w, p.h) ? 'primary' : 'default'}
                    onClick={() => applyPreset(p.w, p.h)}
                    style={{ minWidth: 42 }}>
                    {p.label}
                  </Button>
                ))}
                <Tooltip title="직접 입력">
                  <Space size={4} style={{ marginLeft: 4 }}>
                    <InputNumber size="small" min={1} max={99} value={aspectW}
                      style={{ width: 50 }} onChange={handleCustomW} />
                    <span style={{ color: '#aaa' }}>:</span>
                    <InputNumber size="small" min={1} max={99} value={aspectH}
                      style={{ width: 50 }} onChange={handleCustomH} />
                  </Space>
                </Tooltip>
              </Space>

              <span style={{ color: '#555', fontSize: 12, marginLeft: 'auto', whiteSpace: 'nowrap' }}>
                드래그: 위치 조정 · 휠: 확대/축소
              </span>
            </div>

            {/* ── 푸터 ── */}
            <div style={{
              flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 20px', background: '#fff',
              borderTop: '1px solid #f0f0f0',
            }}>
              <Upload beforeUpload={handleFile} accept="image/*" showUploadList={false}>
                <Button icon={<UploadOutlined />}>다른 사진 선택</Button>
              </Upload>
              <Space>
                <Button onClick={handleClose}>취소</Button>
                <Button type="primary" loading={saving} onClick={handleDone}>편집 완료</Button>
              </Space>
            </div>
          </>
        )}
      </div>
    </Modal>
  )
}
