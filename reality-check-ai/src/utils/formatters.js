/**
 * Format a confidence score to display string
 */
export function formatConfidence(score) {
  return `${score.toFixed(1)}%`
}

/**
 * Format file size in bytes to human readable
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

/**
 * Get file extension from filename
 */
export function getFileExtension(filename) {
  return filename.split('.').pop().toLowerCase()
}

/**
 * Check if file type is valid for analysis
 */
export function isValidFileType(file) {
  const validTypes = [
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
    'image/jpeg',
    'image/png',
    'image/webp',
  ]
  return validTypes.includes(file.type)
}
