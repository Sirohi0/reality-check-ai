import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { COLORS } from './utils/constants'

import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import UploadPage from './pages/UploadPage'
import AnalysisPage from './pages/AnalysisPage'
import ResultPage from './pages/ResultPage'

export default function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [result, setResult] = useState(null)

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file)
    setResult(null)
  }, [])

  const handleResult = useCallback((res) => {
    setResult(res)
  }, [])

  const handleReset = useCallback(() => {
    setSelectedFile(null)
    setResult(null)
  }, [])

  return (
    <BrowserRouter>
      <div style={{ background: COLORS.bg, minHeight: '100vh', color: COLORS.text }}>
        <Navbar />

        <Routes>
          <Route path="/" element={<LandingPage />} />

          <Route
            path="/upload"
            element={<UploadPage onFileSelect={handleFileSelect} />}
          />

          <Route
            path="/analysis"
            element={
              <AnalysisPage
                file={selectedFile}
                onResult={handleResult}
              />
            }
          />

          <Route
            path="/result"
            element={
              <ResultPage
                result={result}
                onReset={handleReset}
              />
            }
          />

          {/* Placeholder routes */}
          <Route
            path="/faq"
            element={<PlaceholderPage title="FAQ" />}
          />
          <Route
            path="/about"
            element={<PlaceholderPage title="About" />}
          />
          <Route
            path="/signin"
            element={<PlaceholderPage title="Sign In" />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

function PlaceholderPage({ title }) {
  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        padding: 48,
      }}
    >
      <h1
        style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 42,
          fontWeight: 800,
          fontStyle: 'italic',
          color: COLORS.text,
        }}
      >
        {title}
      </h1>
      <p
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: 15,
          color: COLORS.textMuted,
        }}
      >
        This page is under construction.
      </p>
    </div>
  )
}
