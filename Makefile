.PHONY: all setup clean sandbox

all: setup

setup:
	@echo "[+] Initializing secure workspace environment..."
	@mkdir -p bin configs/profile.d
	@chmod +x bin/sanitize-env bin/secure-exec

clean:
	@echo "[+] Purging local volatile workspace data..."
	@rm -rf /tmp/secure-workspace
	@history -c || true

sandbox:
	@echo "[+] Building secure execution sandbox..."
	@docker build -f Dockerfile.sandbox -t sysadmin-footprint-mask:sandbox .
