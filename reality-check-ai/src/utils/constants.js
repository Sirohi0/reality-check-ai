/* ═══════════════════════════════════════════════
   Design tokens matching Figma
   ═══════════════════════════════════════════════ */

export const COLORS = {
  bg: '#0d1520',
  bgDark: '#0a1018',
  surface: '#111d2e',
  surfaceLight: '#162236',

  accent: '#00e5a0',
  accentDim: 'rgba(0,229,160,0.12)',

  danger: '#ff4d6a',
  dangerDim: 'rgba(255,77,106,0.12)',

  border: 'rgba(0,229,160,0.15)',
  borderSubtle: 'rgba(255,255,255,0.06)',

  text: '#ffffff',
  textMuted: 'rgba(255,255,255,0.5)',
  textDim: 'rgba(255,255,255,0.3)',
}

export const PIPELINE_STEPS = [
  {
    id: 'extract',
    label: 'Frame Extraction',
    detail: 'Sampling 30 frames via FFmpeg',
    icon: '🎞️',
  },
  {
    id: 'detect',
    label: 'Face Detection',
    detail: 'RetinaFace isolating facial regions',
    icon: '👁️',
  },
  {
    id: 'spatial',
    label: 'Spatial Analysis',
    detail: 'EfficientNet-B4 feature extraction',
    icon: '🧠',
  },
  {
    id: 'temporal',
    label: 'Temporal Attention',
    detail: 'LSTM analyzing frame consistency',
    icon: '⏱️',
  },
  {
    id: 'classify',
    label: 'Classification',
    detail: 'Sigmoid confidence scoring',
    icon: '📊',
  },
]

export const TRUST_BADGES = [
  { icon: '🔒', text: '256-bit Encrypted Uploads' },
  { icon: '🗑️', text: 'Files Deleted After Analysis' },
  { icon: '🛡️', text: 'GDPR Compliant' },
  { icon: '⚡', text: 'Results in Under 10 Seconds' },
]

export const ACCEPTED_FILE_TYPES = 'video/*,image/*'
export const MAX_FILE_SIZE_MB = 100
export const FRAME_COUNT = 30
