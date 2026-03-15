//
import { useState, useEffect, useCallback } from "react";
import { PIPELINE_STEPS, FRAME_COUNT } from "../utils/constants";

export default function useAnalysis(file, onComplete) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepStatuses, setStepStatuses] = useState(
    PIPELINE_STEPS.map(() => "pending"),
  );
  const [analyzedFrames, setAnalyzedFrames] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const startAnalysis = useCallback(async () => {
    if (isRunning || !file) return;
    setIsRunning(true);
    setCurrentStep(0);
    setStepStatuses(PIPELINE_STEPS.map(() => "pending"));
    setAnalyzedFrames(0);

    // Animate pipeline steps while waiting for API
    let step = 0;
    const stepInterval = setInterval(() => {
      if (step < PIPELINE_STEPS.length) {
        setStepStatuses((prev) => {
          const next = [...prev];
          if (step > 0) next[step - 1] = "done";
          next[step] = "active";
          return next;
        });
        setCurrentStep(step);
        if (step === 2) {
          let f = 0;
          const fi = setInterval(() => {
            f++;
            setAnalyzedFrames(f);
            if (f >= FRAME_COUNT) clearInterval(fi);
          }, 55);
        }
        step++;
      }
    }, 1000);

    try {
      // Real API call
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      // Stop step animation
      clearInterval(stepInterval);
      setStepStatuses(PIPELINE_STEPS.map(() => "done"));
      setCurrentStep(-1);
      setAnalyzedFrames(FRAME_COUNT);
      setIsRunning(false);

      onComplete({
        isFake: result.is_fake,
        confidence: result.confidence,
        frames: result.frames_analyzed,
        facesDetected: result.faces_detected,
        attentionWeights: result.attention_weights,
        processingTime: result.processing_time_ms,
      });
    } catch (error) {
      console.error("Analysis failed:", error);
      clearInterval(stepInterval);
      setStepStatuses(PIPELINE_STEPS.map(() => "done"));
      setIsRunning(false);
      onComplete({
        isFake: false,
        confidence: 0,
        frames: 0,
        facesDetected: 0,
        error: "Failed to connect to backend",
      });
    }
  }, [file, isRunning, onComplete]);

  useEffect(() => {
    if (file && !isRunning) {
      startAnalysis();
    }
  }, [file]);

  return {
    currentStep,
    stepStatuses,
    analyzedFrames,
    isRunning,
  };
}