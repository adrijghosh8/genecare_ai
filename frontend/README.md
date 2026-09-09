# GeneCare AI Frontend

A simple, maintainable frontend for GeneCare AI built with **HTML, CSS and vanilla JavaScript**.

## Pages

- `index.html` — landing page
- `analyze.html` — select an active screening model and enter inputs
- `results.html` — model estimate and SHAP feature contributions
- `diseases.html` — condition library
- `disease-detail.html` — condition information
- `about.html` — architecture and technology

## Run locally

Requires Node.js.

```bash
npm install
npm run dev
```

Then open `http://localhost:5173`.

## FastAPI connection

The frontend sends predictions to:

- `POST http://localhost:8000/predict/heart`
- `POST http://localhost:8000/predict/diabetes`

If the backend runs somewhere else, set `window.GENECARE_API_BASE_URL` before `js/api.js` is loaded.

The frontend does not fabricate predictions. Results are displayed only after the FastAPI service responds.

## Design principles

- No React, Tailwind, TypeScript or UI framework
- Minimal monochrome visual system
- Accessible semantic HTML and keyboard focus states
- Responsive layout
- SHAP values are displayed as signed contributions, not percentages
- Breast Cancer remains clearly marked as in development
- Health outputs are described as screening estimates, not diagnoses
