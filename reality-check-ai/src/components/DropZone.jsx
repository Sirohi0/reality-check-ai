import { COLORS, ACCEPTED_FILE_TYPES } from '../utils/constants'
import useFileUpload from '../hooks/useFileUpload'

export default function DropZone({ onFileSelect }) {
  const {
    isDragOver,
    error,
    fileInputRef,
    onDragOver,
    onDragLeave,
    onDrop,
    onFileChange,
    openFilePicker,
  } = useFileUpload()

  const handleDrop = (e) => {
    const file = onDrop(e)
    if (file) onFileSelect(file)
  }

  const handleChange = (e) => {
    const file = onFileChange(e)
    if (file) onFileSelect(file)
  }

  return (
    <div style={{ width: '100%', maxWidth: 680 }}>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={handleDrop}
        onClick={openFilePicker}
        style={{
          border: `2px dashed ${isDragOver ? COLORS.accent : 'rgba(0,229,160,0.25)'}`,
          borderRadius: 20,
          padding: '56px 40px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragOver ? COLORS.accentDim : 'rgba(255,255,255,0.01)',
          transition: 'all 0.3s ease',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FILE_TYPES}
          style={{ display: 'none' }}
          onChange={handleChange}
        />

        {/* Upload icon */}
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: COLORS.accentDim,
            border: `2px solid ${COLORS.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            fontSize: 26,
            color: COLORS.accent,
          }}
        >
          ↑
        </div>

        <div
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 20,
            fontWeight: 700,
            color: COLORS.text,
            marginBottom: 4,
          }}
        >
          Drag & drop your file here
        </div>
        <div
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 13,
            color: COLORS.textDim,
            marginBottom: 24,
          }}
        >
          or click to browse
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <button
            onClick={(e) => {
              e.stopPropagation()
              openFilePicker()
            }}
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: 14,
              fontWeight: 600,
              color: COLORS.accent,
              background: 'transparent',
              border: `1.5px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: '10px 24px',
              cursor: 'pointer',
            }}
          >
            Browse Files
          </button>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
              color: COLORS.textDim,
              padding: '10px 20px',
              borderRadius: 8,
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${COLORS.borderSubtle}`,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            JPG · PNG · MP4 · MOV · AVI (Max 100MB)
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 13,
            color: COLORS.danger,
            textAlign: 'center',
            marginTop: 12,
            padding: '8px 16px',
            borderRadius: 8,
            background: COLORS.dangerDim,
          }}
        >
          {error}
        </div>
      )}
    </div>
  )
}
