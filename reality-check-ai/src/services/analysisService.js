import api from './api'

/**
 * Upload a video/image file for deepfake analysis
 * Returns { analysisId, status }
 */
export async function uploadForAnalysis(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/api/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    },
  })

  return response.data
}

/**
 * Poll analysis status by ID
 * Returns { status, currentStep, result }
 */
export async function getAnalysisStatus(analysisId) {
  const response = await api.get(`/api/status/${analysisId}`)
  return response.data
}

/**
 * Download analysis report as PDF
 */
export async function downloadReport(analysisId) {
  const response = await api.get(`/api/report/${analysisId}`, {
    responseType: 'blob',
  })

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = `reality-check-report-${analysisId}.pdf`
  link.click()
  window.URL.revokeObjectURL(url)
}
