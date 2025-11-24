.PHONY: help install check init run clean test

help:
	@echo "AI Content Bot - Available commands:"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make check      - Check setup and configuration"
	@echo "  make init       - Initialize database"
	@echo "  make run        - Run the bot"
	@echo "  make clean      - Clean temporary files"
	@echo "  make test       - Run tests"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

check:
	@echo "🔍 Checking setup..."
	python check_setup.py

init:
	@echo "🗄️  Initializing database..."
	python init_db.py

run:
	@echo "🚀 Starting bot..."
	python run.py

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "✅ Cleaned!"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v
