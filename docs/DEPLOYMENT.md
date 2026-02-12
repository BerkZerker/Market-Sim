# Deployment Guide

How to deploy Market-Sim to a production VPS.

---

## Prerequisites

- A VPS with at least 2 vCPU / 4GB RAM (Hetzner CPX21 recommended — ~$8/mo)
- A domain name pointing to the VPS IP (A record)
- SSH access to the VPS
- Docker and Docker Compose installed on the VPS

---

## 1. VPS Initial Setup

### Install Docker

```bash
# Ubuntu 22.04+
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
```

### Configure Firewall

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Caddy redirect)
sudo ufw allow 443/tcp   # HTTPS (Caddy)
sudo ufw enable
```

### Install fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
```

---

## 2. Clone and Configure

```bash
git clone https://github.com/BerkZerker/Market-Sim.git
cd Market-Sim
```

### Create Production Environment File

```bash
cp .env.production.example .env
```

Edit `.env` with your production values:

```bash
# REQUIRED — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=your-64-char-hex-string-here

# Database (use the PostgreSQL container)
DATABASE_URL=postgresql+asyncpg://marketsim:your-db-password@postgres:5432/marketsim

# Domain (for CORS and Caddy)
DOMAIN=marketsim.yourdomain.com
ALLOWED_ORIGINS=["https://marketsim.yourdomain.com"]

# Environment
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000

# Market config (adjust as needed)
TICKERS={"FUN": 100.0, "MEME": 50.0, "YOLO": 200.0, "HODL": 75.0, "PUMP": 25.0}
STARTING_CASH=10000.0

# Rate limiting
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60

# PostgreSQL
POSTGRES_USER=marketsim
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=marketsim
```

---

## 3. Docker Compose (Production)

The production `docker-compose.yml` includes Caddy, PostgreSQL, and the app:

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./frontend/dist:/srv/frontend
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - market-sim
    restart: unless-stopped

  market-sim:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - HOST=0.0.0.0
      - PORT=8000
      - ENVIRONMENT=production
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
  pgdata:
```

### Caddyfile

```
{$DOMAIN} {
    # API and WebSocket
    handle /api/* {
        reverse_proxy market-sim:8000
    }
    handle /ws/* {
        reverse_proxy market-sim:8000
    }

    # Frontend (SPA)
    handle {
        root * /srv/frontend
        file_server
        try_files {path} /index.html
    }

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}
```

---

## 4. Deploy

### First Deployment

```bash
# Build and start everything
docker compose up --build -d

# Check logs
docker compose logs -f market-sim

# Verify health
curl https://marketsim.yourdomain.com/api/health
```

### Subsequent Deployments

```bash
git pull origin main
docker compose up --build -d
```

### Database Migrations (after Alembic is set up)

```bash
# Run migrations inside the container
docker compose exec market-sim alembic upgrade head
```

---

## 5. Backups

### Manual Backup

```bash
docker compose exec postgres pg_dump -U marketsim marketsim | gzip > backup-$(date +%Y%m%d).sql.gz
```

### Automated Daily Backups

Create `deploy/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/home/deploy/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Dump database
docker compose exec -T postgres pg_dump -U marketsim marketsim | gzip > "$BACKUP_DIR/marketsim_$DATE.sql.gz"

# Clean old backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: marketsim_$DATE.sql.gz"
```

Add to crontab:

```bash
crontab -e
# Add: 0 3 * * * cd /home/deploy/Market-Sim && ./deploy/backup.sh >> /var/log/backup.log 2>&1
```

---

## 6. Monitoring

### Health Check

The `/api/health` endpoint returns system status:

```json
{
  "status": "ok",
  "database": "connected",
  "exchange": {"tickers": 5, "users": 42},
  "websockets": {"connections": 17},
  "uptime_seconds": 86400,
  "version": "0.1.0"
}
```

### UptimeRobot (Free)

1. Create account at uptimerobot.com
2. Add HTTP monitor for `https://marketsim.yourdomain.com/api/health`
3. Check interval: 5 minutes
4. Alert contacts: your email

### Logs

```bash
# All services
docker compose logs -f

# Just the app
docker compose logs -f market-sim

# Just the database
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail 100 market-sim
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

---

## 7. Maintenance

### Restart Services

```bash
# Restart everything
docker compose restart

# Restart just the app (preserves DB)
docker compose restart market-sim

# Full rebuild
docker compose down && docker compose up --build -d
```

### Database Shell

```bash
docker compose exec postgres psql -U marketsim marketsim
```

### Clear All Data (Nuclear Option)

```bash
docker compose down -v  # Removes volumes (ALL DATA LOST)
docker compose up --build -d
```

---

## 8. Troubleshooting

### App Won't Start

```bash
# Check logs for errors
docker compose logs market-sim

# Common issues:
# - JWT_SECRET not set → "JWT_SECRET must be set in production"
# - DATABASE_URL wrong → connection refused
# - Port conflict → "address already in use"
```

### Database Connection Refused

```bash
# Check if postgres is healthy
docker compose ps
docker compose logs postgres

# Verify connection string matches postgres service name
# DATABASE_URL should use "postgres" as host (Docker service name)
```

### SSL Certificate Not Working

```bash
# Check Caddy logs
docker compose logs caddy

# Common issues:
# - Domain A record not pointing to VPS IP
# - Port 80/443 blocked by firewall
# - Rate limited by Let's Encrypt (wait 1 hour)
```

### WebSocket Connection Failed

```bash
# Verify WebSocket proxy in Caddyfile
# The /ws/* path must be proxied to the app
# Check browser console for WebSocket errors
# Common: mixed content (HTTP page trying WSS)
```

### Performance Issues

```bash
# Check resource usage
docker stats

# If PostgreSQL is slow:
docker compose exec postgres psql -U marketsim -c "SELECT count(*) FROM trades;"
# If millions of rows, add database cleanup job

# If memory is high:
# Check WebSocket connections — each holds memory
# Check order book depth — deep books use more memory
```

---

## 9. Security Checklist

Before going live:

- [ ] `JWT_SECRET` is set to a random 64-character hex string
- [ ] `ENVIRONMENT=production` is set
- [ ] `ALLOWED_ORIGINS` contains only your domain
- [ ] UFW firewall is active (only 22, 80, 443 open)
- [ ] fail2ban is running
- [ ] SSH key authentication is enabled (password auth disabled)
- [ ] `.env` file is NOT committed to git
- [ ] PostgreSQL password is strong and unique
- [ ] Automated backups are running
- [ ] Health monitoring is configured
- [ ] Docker images are up to date (`docker compose pull`)

---

## Cost Summary

| Item | Monthly Cost |
|------|-------------|
| Hetzner CPX21 (2 vCPU, 4GB) | ~$8 |
| Domain name | ~$1 (annual ÷ 12) |
| Backblaze B2 backups | ~$1 |
| UptimeRobot | Free |
| Let's Encrypt SSL | Free |
| **Total** | **~$10/mo** |

Scale up to CPX31 (4 vCPU, 8GB, ~$15/mo) when you hit 500+ concurrent users.
