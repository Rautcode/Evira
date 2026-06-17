#!/usr/bin/env bash
# Generate a self-signed TLS certificate for local/on-prem use.
# Run once from the project root:  bash nginx/gen-certs.sh
# For production replace these with a CA-signed cert or Let's Encrypt.
set -euo pipefail

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:4096 -days 3650 \
  -keyout "$CERT_DIR/server.key" \
  -out    "$CERT_DIR/server.crt" \
  -subj "/C=IN/ST=Maharashtra/L=Pune/O=Evira/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Self-signed cert written to $CERT_DIR"
echo "  server.crt  — certificate (add to browser/OS trust store to remove warnings)"
echo "  server.key  — private key  (keep secret, never commit)"
