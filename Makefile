# Makefile for Custom Network Proxy Server
# Python-based proxy server with HTTP/HTTPS support

.PHONY: all run test test-basic test-concurrent clean help check install

# Default target
all: check

# Check Python syntax
check:
	@echo "Checking Python syntax..."
	@python -m py_compile src/*.py
	@echo "✓ All Python files are syntactically correct"

# Run the proxy server
run:
	@echo "Starting proxy server..."
	@python src/server.py

# Run all tests
test: test-basic test-concurrent
	@echo ""
	@echo "All tests completed"

# Run basic functional tests
test-basic:
	@echo "Running basic functional tests..."
	@bash tests/test_basic.sh

# Run concurrent connection tests
test-concurrent:
	@echo "Running concurrent connection tests..."
	@python tests/test_concurrent.py

# Install required Python packages (if any were needed)
install:
	@echo "This project uses only Python standard library"
	@echo "No additional packages needed"
	@python --version

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf src/__pycache__
	@rm -rf logs/*.log logs/*.log.*
	@rm -f src/*.pyc
	@echo "✓ Cleanup complete"

# Display help
help:
	@echo "Custom Network Proxy Server - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make check           - Check Python syntax"
	@echo "  make run             - Start the proxy server"
	@echo "  make test            - Run all tests"
	@echo "  make test-basic      - Run basic functional tests"
	@echo "  make test-concurrent - Run concurrent connection tests"
	@echo "  make clean           - Remove generated files"
	@echo "  make install         - Check Python installation"
	@echo "  make help            - Display this help message"
	@echo ""
	@echo "Usage examples:"
	@echo "  make run             # Start server on localhost:8888"
	@echo "  make test            # Run test suite (server must be running)"
