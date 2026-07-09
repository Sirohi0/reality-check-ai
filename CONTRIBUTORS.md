# Contributors

Reality Check AI was built as a two-person collaboration. Ownership split below reflects who drove each half of the stack.

## Sanchit Sirohi
- Frontend application (`reality-check-ai/`) — React + Vite + Tailwind, all pages/components/hooks
- API integration layer (`services/`, Axios client, Firebase auth wiring)
- Backend application/API layer (`deepfake-backend/backend/`) — FastAPI app, routers, request/response schemas
- Deployment tooling — Docker, docker-compose, nginx config, CI/CD (in progress)

## Saanann Roy
- Model architecture & training pipeline (`deepfake-backend/training/`) — EfficientNetV2-B3 + Temporal Attention BiLSTM
- Dataset preprocessing (`deepfake-backend/preprocessing/`)
- Training run, hyperparameter tuning, checkpoint selection (Celeb-DF v2)

---

Both contributors worked in the same repository; the split above describes primary ownership areas, not exclusive involvement — there was overlap and review across both halves.
