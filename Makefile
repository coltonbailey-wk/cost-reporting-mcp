.PHONY: help start stop install lint format check clean test

help:
	@echo "Available commands:"
	@echo "  make start    - Start the AWS Cost Explorer MCP server"
	@echo "  make stop     - Stop the running server"
	@echo "  make install  - Install Python dependencies"
	@echo "  make lint     - Run linting checks (ruff)"
	@echo "  make format   - Format code (ruff)"
	@echo "  make check    - Run lint + format check without modifying files"
	@echo "  make clean    - Clean up cache files and artifacts"
	@echo "  make test     - Run benchmark tests"

start:
	@echo "Starting AWS Cost Explorer MCP server..."
	@./start_official_mcp.sh

stop:
	@echo "Stopping AWS Cost Explorer MCP server..."
	@pkill -f "python.*web_app.py" || echo "No server process found"

install:
	@echo "Installing dependencies..."
	@pip3 install -r requirements.txt
	@pip3 install ruff

lint:
	@echo "Running linting checks with ruff..."
	@ruff check *.py
	@echo "Linting complete!"

format:
	@echo "Formatting Python code with ruff..."
	@ruff check --fix --unsafe-fixes *.py
	@ruff format *.py
	@echo "Formatting complete!"

check:
	@echo "Running checks without modifying files..."
	@ruff check *.py
	@ruff format --check *.py
	@echo "Check complete!"

clean:
	@echo "Cleaning up cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

test:
	@echo "Running benchmark tests..."
	@cd test && python benchmark.py

