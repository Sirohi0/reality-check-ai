import { useNavigate } from 'react-router-dom'
import { COLORS } from '../utils/constants'
import DropZone from '../components/DropZone'
import InfoCard from '../components/InfoCard'

export default function UploadPage({ onFileSelect }) {
  const navigate = useNavigate()

  const handleFileSelect = (file) => {
    onFileSelect(file)
    navigate('/analysis')
  }

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '60px 48px',
      }}
    >
      {/* Headline */}
      <h1
        className="animate-fade-in-up"
        style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 46,
          fontWeight: 800,
          fontStyle: 'italic',
          color: COLORS.text,
          textAlign: 'center',
          marginBottom: 12,
        }}
      >
        Upload Your Media
      </h1>
      <p
        className="animate-fade-in-up-delay-1"
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 15,
          color: COLORS.textMuted,
          textAlign: 'center',
          marginBottom: 40,
        }}
      >
        Drop an image or video to check if it's AI-generated or deepfaked
      </p>

      {/* Drop Zone */}
      <div className="animate-fade-in-up-delay-2">
        <DropZone onFileSelect={handleFileSelect} />
      </div>

      {/* Info Cards */}
      <div
        className="animate-fade-in-up-delay-3"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
          maxWidth: 680,
          width: '100%',
          marginTop: 32,
        }}
      >
        <InfoCard icon="🔍" title="What We Check" titleColor={COLORS.accent}>
          Face swap detection · GAN artifacts · Metadata anomalies · Compression
          inconsistencies · Lighting/shadow analysis
        </InfoCard>

        <InfoCard icon="🔒" title="Privacy & Security" titleColor="#f0a030">
          Your files are encrypted during upload. All data is permanently
          deleted after analysis. We never store your media.
        </InfoCard>
      </div>

      {/* Start Analysis CTA */}
      <button
        className="animate-fade-in-up-delay-4"
        onClick={() => navigate('/analysis')}
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 20,
          fontWeight: 700,
          color: COLORS.bgDark,
          background: COLORS.accent,
          border: 'none',
          borderRadius: 12,
          padding: '18px 80px',
          cursor: 'pointer',
          marginTop: 36,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          boxShadow: '0 6px 30px rgba(0,229,160,0.3)',
          transition: 'transform 0.2s',
        }}
        onMouseEnter={(e) =>
          (e.target.style.transform = 'translateY(-2px)')
        }
        onMouseLeave={(e) =>
          (e.target.style.transform = 'translateY(0)')
        }
      >
        Start Analysis →
      </button>
    </div>
  )
}
