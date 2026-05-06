.PHONY: install backend frontend bench

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

bench:
	cd backend && python ../benchmarks/bench_suggestions.py

dev:
	@echo "Start backend in one terminal:  make backend"
	@echo "Start frontend in another:      make frontend"
	@echo "Then open http://localhost:5173"
