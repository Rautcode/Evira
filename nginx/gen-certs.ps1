# gen-certs.ps1 — Generate self-signed TLS certificates for the nginx reverse proxy.
# Run from the repo root: .\nginx\gen-certs.ps1
# Requires: openssl on PATH (ships with Git for Windows and WSL; or install via choco install openssl)

param(
    [string]$OutDir = "$PSScriptRoot\certs"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    Write-Error "openssl not found on PATH. Install Git for Windows (which includes openssl) or run: choco install openssl"
    exit 1
}

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$KeyFile  = Join-Path $OutDir "nginx.key"
$CertFile = Join-Path $OutDir "nginx.crt"
$SanConf  = Join-Path $OutDir "san.cnf"

# Write a minimal openssl config with Subject Alternative Names
@"
[req]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn
x509_extensions    = v3_req

[dn]
C  = US
ST = State
L  = City
O  = SCADA
CN = localhost

[v3_req]
subjectAltName = @alt_names
keyUsage       = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
IP.1  = 127.0.0.1
"@ | Set-Content -Encoding utf8 $SanConf

Write-Host "Generating 4096-bit RSA key and self-signed certificate..."
& openssl req -x509 -nodes -newkey rsa:4096 -days 3650 `
    -keyout $KeyFile `
    -out    $CertFile `
    -config $SanConf

if ($LASTEXITCODE -ne 0) {
    Write-Error "openssl failed (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
}

Remove-Item $SanConf -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done. Files written to: $OutDir"
Write-Host "  Key : $KeyFile"
Write-Host "  Cert: $CertFile"
Write-Host ""
Write-Host "These are mounted by docker-compose.yml into the nginx container."
Write-Host "Your browser will show a security warning for self-signed certs — add an exception or import the .crt into your system trust store."
