import { useState, useRef, useCallback } from 'react'
import { isValidFileType } from '../utils/formatters'
import { MAX_FILE_SIZE_MB } from '../utils/constants'

/**
 * Handles drag & drop, file validation, and selection state
 */
export default function useFileUpload() {
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  const validateFile = useCallback((file) => {
    if (!file) {
      setError('No file selected')
      return false
    }

    if (!isValidFileType(file)) {
      setError('Invalid file type. Please upload MP4, MOV, AVI, WebM, JPG, or PNG.')
      return false
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE_MB}MB.`)
      return false
    }

    setError(null)
    return true
  }, [])

  const handleFile = useCallback(
    (file) => {
      if (validateFile(file)) {
        setSelectedFile(file)
        return file
      }
      return null
    },
    [validateFile]
  )

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const onDragLeave = useCallback(() => {
    setIsDragOver(false)
  }, [])

  const onDrop = useCallback(
    (e) => {
      e.preventDefault()
      setIsDragOver(false)
      return handleFile(e.dataTransfer.files[0])
    },
    [handleFile]
  )

  const onFileChange = useCallback(
    (e) => {
      return handleFile(e.target.files[0])
    },
    [handleFile]
  )

  const openFilePicker = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const reset = useCallback(() => {
    setSelectedFile(null)
    setError(null)
    setIsDragOver(false)
  }, [])

  return {
    isDragOver,
    error,
    selectedFile,
    fileInputRef,
    onDragOver,
    onDragLeave,
    onDrop,
    onFileChange,
    openFilePicker,
    reset,
  }
}
