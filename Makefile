# Makefile for managing Python server and ngrok in background
# Author: Assistant
# Description: Manages server lifecycle with background processes

# Configuration
PYTHON_CMD = uv run src/app.py
# Load environment variables from .env file
include .env
export
# Set your own ngrok URL here, or override with: make start NGROK_URL=your-url.ngrok-free.app
NGROK_URL ?= $(shell grep '^NGROK_URL=' .env 2>/dev/null | cut -d'=' -f2 || echo 'your-ngrok-url.ngrok-free.app')
NGROK_PORT = 5000
PID_DIR = .pids
SERVER_PID_FILE = $(PID_DIR)/server.pid
NGROK_PID_FILE = $(PID_DIR)/ngrok.pid

# Colors for output
GREEN = \033[0;32m
RED = \033[0;31m
YELLOW = \033[1;33m
NC = \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  $(YELLOW)start$(NC)     - Start server and ngrok in background"
	@echo "  $(YELLOW)stop$(NC)      - Stop server and ngrok"
	@echo "  $(YELLOW)restart$(NC)   - Stop and start server with latest code"
	@echo "  $(YELLOW)status$(NC)    - Check if server and ngrok are running"
	@echo "  $(YELLOW)logs$(NC)      - Show server logs"
	@echo "  $(YELLOW)clean$(NC)     - Clean up PID files and logs"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  Set your ngrok URL: $(YELLOW)make start NGROK_URL=your-url.ngrok-free.app$(NC)"
	@echo "  Or edit NGROK_URL in this Makefile"

# Create PID directory if it doesn't exist
$(PID_DIR):
	@mkdir -p $(PID_DIR)

# Start server and ngrok in background
.PHONY: start
start: $(PID_DIR)
	@echo "$(GREEN)Starting server and ngrok in background...$(NC)"
	@if [ -f $(SERVER_PID_FILE) ] && kill -0 `cat $(SERVER_PID_FILE)` 2>/dev/null; then \
		echo "$(YELLOW)Server is already running (PID: `cat $(SERVER_PID_FILE)`)$(NC)"; \
	else \
		echo "$(GREEN)Starting Python server...$(NC)"; \
		nohup $(PYTHON_CMD) > server.log 2>&1 & echo $$! > $(SERVER_PID_FILE); \
		echo "$(GREEN)Server started with PID: `cat $(SERVER_PID_FILE)`$(NC)"; \
	fi
	@if [ -f $(NGROK_PID_FILE) ] && kill -0 `cat $(NGROK_PID_FILE)` 2>/dev/null; then \
		echo "$(YELLOW)Ngrok is already running (PID: `cat $(NGROK_PID_FILE)`)$(NC)"; \
	else \
		echo "$(GREEN)Starting ngrok...$(NC)"; \
		nohup ngrok http --url=$(NGROK_URL) $(NGROK_PORT) > ngrok.log 2>&1 & echo $$! > $(NGROK_PID_FILE); \
		echo "$(GREEN)Ngrok started with PID: `cat $(NGROK_PID_FILE)`$(NC)"; \
	fi
	@sleep 2
	@echo "$(GREEN)Services started successfully!$(NC)"
	@echo "$(GREEN)Server URL: https://$(NGROK_URL)$(NC)"

# Stop server and ngrok
.PHONY: stop
stop:
	@echo "$(RED)Stopping server and ngrok...$(NC)"
	@if [ -f $(SERVER_PID_FILE) ]; then \
		if kill -0 `cat $(SERVER_PID_FILE)` 2>/dev/null; then \
			kill `cat $(SERVER_PID_FILE)` && echo "$(RED)Server stopped$(NC)"; \
		else \
			echo "$(YELLOW)Server was not running$(NC)"; \
		fi; \
		rm -f $(SERVER_PID_FILE); \
	else \
		echo "$(YELLOW)No server PID file found$(NC)"; \
	fi
	@if [ -f $(NGROK_PID_FILE) ]; then \
		if kill -0 `cat $(NGROK_PID_FILE)` 2>/dev/null; then \
			kill `cat $(NGROK_PID_FILE)` && echo "$(RED)Ngrok stopped$(NC)"; \
		else \
			echo "$(YELLOW)Ngrok was not running$(NC)"; \
		fi; \
		rm -f $(NGROK_PID_FILE); \
	else \
		echo "$(YELLOW)No ngrok PID file found$(NC)"; \
	fi
	@echo "$(YELLOW)Cleaning up log files...$(NC)"
	@rm -f server.log ngrok.log nohup.out
	@echo "$(GREEN)Stop and cleanup completed$(NC)"

# Restart server with latest code (keeps ngrok running)
.PHONY: restart
restart:
	@echo "$(YELLOW)Restarting server with latest code...$(NC)"
	@if [ -f $(SERVER_PID_FILE) ]; then \
		if kill -0 `cat $(SERVER_PID_FILE)` 2>/dev/null; then \
			kill `cat $(SERVER_PID_FILE)` && echo "$(RED)Old server stopped$(NC)"; \
		fi; \
		rm -f $(SERVER_PID_FILE); \
	fi
	@echo "$(GREEN)Starting new server...$(NC)"
	@nohup $(PYTHON_CMD) > server.log 2>&1 & echo $$! > $(SERVER_PID_FILE)
	@echo "$(GREEN)Server restarted with PID: `cat $(SERVER_PID_FILE)`$(NC)"
	@sleep 1
	@echo "$(GREEN)Server restart completed!$(NC)"

# Check status of services
.PHONY: status
status:
	@echo "$(GREEN)Service Status:$(NC)"
	@if [ -f $(SERVER_PID_FILE) ] && kill -0 `cat $(SERVER_PID_FILE)` 2>/dev/null; then \
		echo "  $(GREEN)✓ Server is running (PID: `cat $(SERVER_PID_FILE)`)$(NC)"; \
	else \
		echo "  $(RED)✗ Server is not running$(NC)"; \
	fi
	@if [ -f $(NGROK_PID_FILE) ] && kill -0 `cat $(NGROK_PID_FILE)` 2>/dev/null; then \
		echo "  $(GREEN)✓ Ngrok is running (PID: `cat $(NGROK_PID_FILE)`)$(NC)"; \
	else \
		echo "  $(RED)✗ Ngrok is not running$(NC)"; \
	fi
	@if [ -f $(SERVER_PID_FILE) ] && kill -0 `cat $(SERVER_PID_FILE)` 2>/dev/null && \
	   [ -f $(NGROK_PID_FILE) ] && kill -0 `cat $(NGROK_PID_FILE)` 2>/dev/null; then \
		echo "  $(GREEN)Server URL: https://$(NGROK_URL)$(NC)"; \
	fi

# Show server logs
.PHONY: logs
logs:
	@if [ -f server.log ]; then \
		echo "$(GREEN)Server logs (last 50 lines):$(NC)"; \
		tail -50 server.log; \
	else \
		echo "$(YELLOW)No server logs found$(NC)"; \
	fi

# Show ngrok logs
.PHONY: ngrok-logs
ngrok-logs:
	@if [ -f ngrok.log ]; then \
		echo "$(GREEN)Ngrok logs (last 50 lines):$(NC)"; \
		tail -50 ngrok.log; \
	else \
		echo "$(YELLOW)No ngrok logs found$(NC)"; \
	fi

# Clean up PID files and logs
.PHONY: clean
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf $(PID_DIR)
	@rm -f server.log ngrok.log
	@echo "$(GREEN)Cleanup completed$(NC)"

# Force kill all related processes (emergency stop)
.PHONY: force-stop
force-stop:
	@echo "$(RED)Force stopping all related processes...$(NC)"
	@pkill -f "$(PYTHON_CMD)" || true
	@pkill -f "ngrok.*$(NGROK_PORT)" || true
	@rm -f $(SERVER_PID_FILE) $(NGROK_PID_FILE)
	@echo "$(RED)Force stop completed$(NC)"

# Development mode - restart server on file changes (requires inotify-tools)
.PHONY: dev
dev:
	@echo "$(GREEN)Starting development mode with auto-restart...$(NC)"
	@echo "$(YELLOW)Note: This requires inotify-tools (apt install inotify-tools)$(NC)"
	@$(MAKE) start
	@while inotifywait -r -e modify,create,delete src/; do \
		echo "$(YELLOW)File changes detected, restarting server...$(NC)"; \
		$(MAKE) restart; \
	done 