.PHONY: api web test sample compose

api:
	cd api && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm run dev

test:
	cd api && pytest -q
	cd web && npm test && npm run typecheck

sample:
	python api/scripts/make_sample_pdf.py

compose:
	docker compose up --build
