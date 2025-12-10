# 🎮 DualShock Tools v3.5 - Community Edition Enhanced

![Version](https://img.shields.io/badge/version-3.5.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Web-orange)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

Professional calibration, diagnostics, and health monitoring tool for PlayStation DualShock 4 and DualSense controllers.

---

## ✨ Features

### 🎯 Core Functionality
- **Analog Stick Calibration**: Precision calibration with real-time visualization
- **Software Trigger Remapping**: Compensate for worn L2/R2 potentiometers
- **Clone Detection**: Enhanced detection logic for JDM-020/040/055 boards
- **Ghost Device Filtering**: Eliminates duplicate controller entries (Issue #174 fix)

### 🔬 Advanced Diagnostics (NEW in v3.5)
- **Wear Analysis**: Real-time analog stick health monitoring
- **Drift Detection**: Automatic detection of stick drift with directional indicators
- **Latency Profiling**: Input lag measurement for USB and Bluetooth connections
- **Visual Health Dashboard**: Color-coded status indicators

### 💾 Profile Management (NEW in v3.5)
- **Local Backup**: Automatic calibration profile backup
- **Cloud Sync**: Optional encrypted cloud backup (end-to-end encryption)
- **QR Code Export/Import**: Share profiles between devices
- **Version Control**: Profile history with timestamps

### 📱 Progressive Web App (NEW in v3.5)
- **Offline Support**: Works without internet after first load
- **Install to Home Screen**: Native app-like experience
- **Auto-Updates**: Background updates when new version available
- **Cross-Platform**: Works on desktop and mobile

# 🔄 DualShock Tools - Auto-Update System Documentation

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Setup Guide](#setup-guide)
3. [Release Workflow](#release-workflow)
4. [Security Best Practices](#security-best-practices)
5. [CDN Deployment](#cdn-deployment)
6. [Monitoring & Analytics](#monitoring--analytics)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐
│  Client App     │
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTPS
         ↓
┌─────────────────┐      ┌─────────────────┐
│  Update API     │◄────►│  CDN (S3/R2)    │
│  (Backend)      │      │  File Storage   │
└────────┬────────┘      └─────────────────┘
         │
         │
         ↓
┌─────────────────┐
│  Analytics      │
│  Database       │
└─────────────────┘
```

### Key Features

✅ **Semantic Versioning** - Proper version management
✅ **Delta Updates** - Only download changed files
✅ **Integrity Verification** - SHA-256 checksums
✅ **Digital Signatures** - RSA-2048 manifest signing
✅ **Automatic Rollback** - Safe recovery on failure
✅ **Multi-Channel** - Stable, Beta, Dev releases
✅ **Background Updates** - Non-intrusive experience
✅ **Offline Queue** - Update when connection available

---

## 🚀 Setup Guide

### Prerequisites

```bash
# Required software
- Node.js 16+
- Python 3.7+
- OpenSSL

# Install Python dependencies
pip install flask flask-cors flask-limiter cryptography boto3
```

### Initial Setup

#### 1. Generate RSA Key Pair

```bash
# Generate keys for manifest signing
python update_server.py generate-keys

# Keys will be created in ./keys/
# - private_key.pem (KEEP SECRET!)
# - public_key.pem (embed in app)
```

⚠️ **CRITICAL**: Never commit `private_key.pem` to Git!

#### 2. Configure Update Manager

```javascript
// In your main app.js
import { UpdateManager } from './update-manager.js';

const updateManager = new UpdateManager({
  currentVersion: '3.5.0',
  manifestUrl: 'https://api.dualshock.tools/v1/updates/manifest.json',
  channel: 'stable',
  autoCheck: true,
  checkInterval: 3600000, // 1 hour
  autoDownload: true,
  autoInstall: false
});
```

#### 3. Embed Public Key

```javascript
// Copy public key content to app
const PUBLIC_KEY_PEM = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----`;
```

---

## 📦 Release Workflow

### Step 1: Build Your Application

```bash
# Build production version
npm run build:prod

# Output in ./dist/
```

### Step 2: Generate Update Manifest

```bash
# Generate manifest for stable release
python update_server.py generate \
  --version 3.5.1 \
  --channel stable \
  --build-dir dist

# This creates: manifests/manifest_stable.json
```

**Manifest Structure:**

```json
{
  "version": "3.5.1",
  "releaseDate": "2024-12-11T10:00:00Z",
  "channel": "stable",
  "minVersion": "3.0.0",
  "breaking": false,
  "changelog": {
    "en": "Bug fixes and performance improvements",
    "pl": "Poprawki błędów i ulepszenia wydajności"
  },
  "files": [
    {
      "path": "js/app.bundle.js",
      "hash": "sha256-abc123...",
      "size": 245678,
      "url": "https://cdn.dualshock.tools/v3.5.1/js/app.bundle.js",
      "critical": true,
      "mimeType": "application/javascript"
    }
  ],
  "totalSize": 2456789,
  "fileCount": 15,
  "signature": "BASE64_RSA_SIGNATURE"
}
```

### Step 3: Deploy to CDN

```bash
# Deploy to AWS S3
python update_server.py deploy \
  --target s3 \
  --manifest manifests/manifest_stable.json \
  --build-dir dist

# Or deploy to Cloudflare R2
python update_server.py deploy \
  --target cloudflare \
  --manifest manifests/manifest_stable.json
```

### Step 4: Start Update API Server

```bash
# Start production server
python update_server.py serve --port 8000 --host 0.0.0.0

# Or use production WSGI server
gunicorn -w 4 -b 0.0.0.0:8000 update_server:app
```

### Step 5: Test Update Flow

```bash
# Test from client
curl https://api.dualshock.tools/v1/updates/manifest.json?channel=stable

# Should return manifest JSON
```

---

## 🔐 Security Best Practices

### 1. Key Management

```bash
# Store private key securely
# - Use environment variables in production
# - Never commit to version control
# - Rotate keys annually

# Example: AWS Secrets Manager
aws secretsmanager create-secret \
  --name dst/update-signing-key \
  --secret-string file://keys/private_key.pem
```

### 2. Manifest Signing

```python
# Server-side signing (automatic)
signature = sign_manifest(manifest_data, private_key)

# Client-side verification (automatic)
is_valid = verify_signature(manifest, public_key, signature)
if not is_valid:
    raise SecurityError("Invalid manifest signature!")
```

### 3. HTTPS Only

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    server_name api.dualshock.tools;
    
    ssl_certificate /etc/ssl/certs/api.dualshock.tools.crt;
    ssl_certificate_key /etc/ssl/private/api.dualshock.tools.key;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location /v1/updates/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Rate Limiting

```python
# Already configured in update_server.py
@limiter.limit("30 per minute")
def get_manifest():
    # API endpoint protected
    pass
```

### 5. Integrity Verification

```javascript
// Client automatically verifies every file
const fileData = await downloadFile(url);
const actualHash = await calculateSHA256(fileData);

if (actualHash !== expectedHash) {
    throw new Error('File integrity check failed!');
}
```

---

## ☁️ CDN Deployment

### AWS S3 + CloudFront

#### Setup S3 Bucket

```bash
# Create S3 bucket
aws s3 mb s3://dualshock-tools-updates

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket dualshock-tools-updates \
  --versioning-configuration Status=Enabled

# Set CORS policy
aws s3api put-bucket-cors \
  --bucket dualshock-tools-updates \
  --cors-configuration file://cors.json
```

**cors.json:**

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://dualshock.tools"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

#### Setup CloudFront Distribution

```bash
# Create distribution
aws cloudfront create-distribution \
  --origin-domain-name dualshock-tools-updates.s3.amazonaws.com \
  --default-root-object index.html
```

#### Deploy Files

```bash
# Upload with correct cache headers
aws s3 sync dist/ s3://dualshock-tools-updates/v3.5.1/ \
  --cache-control "public, max-age=31536000" \
  --exclude "*.html" \
  --exclude "manifest.json"

# Upload manifest with short cache
aws s3 cp manifests/manifest_stable.json \
  s3://dualshock-tools-updates/manifest.json \
  --cache-control "public, max-age=300"
```

### Cloudflare R2

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create R2 bucket
wrangler r2 bucket create dualshock-tools-updates

# Upload files
wrangler r2 object put \
  dualshock-tools-updates/v3.5.1/js/app.bundle.js \
  --file dist/js/app.bundle.js
```

---

## 📊 Monitoring & Analytics

### Update Metrics

Track these key metrics:

```python
# Built into update_server.py
class UpdateStats:
    - total_checks: Number of update checks
    - total_downloads: Number of downloads initiated
    - total_installs: Number of successful installs
    - version_distribution: Users per version
    - channel_distribution: Users per channel
    - failure_rate: Failed updates / total attempts
```

### Grafana Dashboard

```yaml
# Example Prometheus metrics
dst_update_checks_total{channel="stable"} 1234
dst_update_downloads_total{version="3.5.1"} 567
dst_update_installs_total{version="3.5.1"} 534
dst_update_failures_total{reason="network"} 12
```

### Error Tracking

```javascript
// Client-side error reporting
window.addEventListener('dst:update-error', (event) => {
    const { error, context } = event.detail;
    
    // Send to error tracking service
    Sentry.captureException(error, {
        tags: {
            component: 'update-manager',
            version: context.currentVersion,
            channel: context.channel
        }
    });
});
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Signature Verification Fails

```
Error: Invalid manifest signature
```

**Solution:**
- Ensure public key in client matches private key used for signing
- Regenerate keys if corrupted: `python update_server.py generate-keys`
- Check manifest wasn't modified after signing

#### 2. Download Fails with CORS Error

```
Error: CORS policy: No 'Access-Control-Allow-Origin' header
```

**Solution:**
```bash
# Update S3 CORS policy
aws s3api put-bucket-cors \
  --bucket dualshock-tools-updates \
  --cors-configuration file://cors.json
```

#### 3. Files Don't Match Hash

```
Error: Integrity check failed for js/app.bundle.js
```

**Solution:**
- Regenerate manifest: `python update_server.py generate --version X.Y.Z`
- Clear CDN cache
- Verify files weren't corrupted during upload

#### 4. Update Check Returns 404

```
Error: Manifest fetch failed: 404
```

**Solution:**
- Verify manifest exists: `ls manifests/manifest_stable.json`
- Check API server is running: `curl localhost:8000/v1/updates/health`
- Verify DNS/routing configuration

---

## 📚 API Reference

### Client API

#### UpdateManager

```javascript
const updateManager = new UpdateManager(config);
```

**Methods:**

```javascript
// Check for updates
await updateManager.checkForUpdates(silent = false)
// Returns: UpdateInfo | null

// Manual update trigger
await updateManager.update()

// Get current state
const state = updateManager.getState()
// Returns: { checking, downloading, installing, ... }

// Start/stop auto-check
updateManager.startAutoCheck()
updateManager.stopAutoCheck()
```

**Events:**

```javascript
// Update available
window.addEventListener('dst:update-available', (event) => {
    const { version, changelog, size } = event.detail;
});

// Download progress
window.addEventListener('dst:download-progress', (event) => {
    const { progress, downloaded, total } = event.detail;
});

// Install complete
window.addEventListener('dst:install-complete', (event) => {
    const { version } = event.detail;
});

// Error occurred
window.addEventListener('dst:update-error', (event) => {
    const { error, context } = event.detail;
});
```

### Server API

#### GET /v1/updates/manifest.json

Get update manifest for specific channel.

**Query Parameters:**
- `channel` (string): stable, beta, or dev
- `current_version` (string, optional): Client's current version

**Response:**
```json
{
  "version": "3.5.1",
  "releaseDate": "2024-12-11T10:00:00Z",
  "files": [...],
  "signature": "..."
}
```

#### GET /v1/updates/download/:file_path

Download specific update file.

**Parameters:**
- `file_path`: Relative path to file (e.g., js/app.bundle.js)

**Response:** File binary data with appropriate Content-Type

#### GET /v1/updates/stats

Get update statistics (admin only).

**Response:**
```json
{
  "checks": 1234,
  "downloads": 567,
  "installs": 534,
  "versions": {
    "3.5.0": 423,
    "3.5.1": 111
  }
}
```

#### GET /v1/updates/channels

List available update channels.

**Response:**
```json
{
  "channels": [
    {
      "name": "stable",
      "version": "3.5.1",
      "releaseDate": "2024-12-11T10:00:00Z"
    }
  ]
}
```

---

## 🎯 Best Practices Summary

### Release Checklist

- [ ] Update version in package.json
- [ ] Build production version (`npm run build:prod`)
- [ ] Run tests (`npm test`)
- [ ] Generate manifest (`python update_server.py generate`)
- [ ] Review manifest file
- [ ] Deploy to CDN (`python update_server.py deploy`)
- [ ] Update API server manifests
- [ ] Monitor first 100 updates
- [ ] Announce release in changelog

### Security Checklist

- [ ] Private key stored securely
- [ ] HTTPS enforced everywhere
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Manifest signatures verified
- [ ] File integrity checks enabled
- [ ] Error tracking configured
- [ ] Rollback tested

### Performance Checklist

- [ ] CDN cache headers set
- [ ] Delta updates enabled
- [ ] Files compressed (gzip/brotli)
- [ ] Large files chunked
- [ ] Background downloads
- [ ] Bandwidth-aware scheduling
- [ ] Progress feedback to user

---

## 📄 License

This auto-update system is part of DualShock Tools v3.5, released under MIT License.

Copyright (c) 2025
By 🅽ɨɛʐռǟռʏ 🅽ɨӄօʍʊ Ⱥ🅽ටꈤYMටꪊSƗꀘ
  ༽ ❗༽   ꍏꈤටꈤ༼lᕗ ༽ ❗༽ 

## 🙋 Support

For issues or questions:
- GitHub Issues: https://github.com/dualshock-tools/issues
- Email: support@dualshock.tools
- Discussions: https://github.com/dualshock-tools/discussions

---

*Made with ❤️ for seamless updates*
---

## 🚀 Quick Start

### Method 1: Automatic Migration (Recommended)

If you have v2.2 installed, use the automatic migrator:

```bash
# Download the migrator
wget https://raw.githubusercontent.com/anonymousik.is-a.dev/PADO-KALIBRATOR/v3.5/migrator.py

# Run migration
python3 migrator.py /path/to/your/project

# Follow on-screen instructions
```

The migrator will:
- ✅ Analyze your current installation
- ✅ Create automatic backup
- ✅ Upgrade all components to v3.5
- ✅ Install dependencies
- ✅ Generate SSL certificates
- ✅ Build the project

### Method 2: Fresh Installation

```bash
# Clone repository
git clone https://github.com/anonymousik/PADO-KALIBRATOR/v3.5/migrator.py
cd PADO-KALIBRATOR

# Install dependencies
npm install

# Generate SSL certificates (required for WebHID)
openssl req -newkey rsa:2048 -new -nodes -x509 -days 365 \
  -keyout server.key -out server.pem \
  -subj "/C=PL/ST=Local/L=Local/O=DualShockTools/CN=localhost"

# Build project
npm run build

# Start development server
python3 server.py
```

Open https://localhost:8443 in your browser (Chrome, Edge, Opera, or Brave).

⚠️ **Important**: You'll see a security warning about the self-signed certificate. Click "Advanced" → "Proceed to localhost" to continue.

---

## 📋 Requirements

### Browser Support
- ✅ Chrome 89+
- ✅ Edge 89+
- ✅ Opera 75+
- ✅ Brave 1.23+
- ❌ Firefox (WebHID not supported)
- ❌ Safari (WebHID not supported)

### System Requirements
- **Node.js** 16.x or higher
- **npm** 7.x or higher
- **Python** 3.7+ (for development server)
- **OpenSSL** (for certificate generation)

### Hardware Requirements
- USB cable (data transfer capable, not charge-only)
- DualShock 4 (CUH-ZCT1 or CUH-ZCT2)
- DualSense (CFI-ZCT1)

---

## 📖 Usage Guide

### 1. Connecting Your Controller

1. **Connect via USB cable**
   - Ensure cable supports data transfer
   - Wait for the controller LED to light up

2. **Click "Connect Controller"**
   - Browser will show device selection dialog
   - Select your controller from the list
   - ⚠️ You should see only ONE device (ghost filtering active)

3. **Check Status Panel**
   - Green indicator = Connected
   - Controller information displayed

### 2. Calibrating Analog Sticks

1. Navigate to **Calibration** tab
2. Click **Start Calibration**
3. Rotate **both analog sticks** in full circles for 10 seconds
4. Try to reach the edges in all directions
5. Click **Save to Controller** when complete

**Tips for best results:**
- Use smooth, continuous circular motions
- Cover all 360 degrees multiple times
- Apply consistent pressure
- Don't rush the process

### 3. Running Diagnostics

1. Navigate to **Diagnostics** tab
2. Click **Start Diagnostics Scan**
3. Use controller normally for 30-60 seconds
4. View real-time metrics:
   - Stick health (0-100%)
   - Drift direction and magnitude
   - Input latency
   - Sample count

**Health Status Codes:**
- 🟢 **Excellent** (95-100%): No action needed
- 🟡 **Good** (80-94%): Monitor periodically
- 🟠 **Warning** (60-79%): Recalibration recommended
- 🔴 **Critical** (<60%): Consider module replacement

### 4. Managing Profiles

#### Creating a Profile
1. Navigate to **Profiles** tab
2. Click **Create New Profile**
3. Profile automatically saved with timestamp
4. View in profile list

#### Backing Up to Cloud (Optional)
1. Navigate to **Profiles** tab
2. Enable **Cloud Backup** toggle
3. Profiles automatically sync (encrypted)

#### Exporting via QR Code
1. Select profile from list
2. Click **Export** button
3. Show QR code to another device
4. Import on target device

### 5. Software Trigger Remapping (NEW)

For worn L2/R2 triggers that don't reach full travel:

1. Navigate to **Settings** tab
2. Enable **Software Remapping**
3. Press L2 to full travel
4. Adjust **L2 Max Value** slider to match
5. Repeat for R2
6. Remapping applies in browser only (not saved to controller)

---

## 🔧 Advanced Configuration

### Custom SSL Certificate

Replace self-signed certificate with your own:

```bash
# Place your certificate files
cp mycert.pem server.pem
cp mykey.key server.key

# Restart server
python3 server.py
```

### Environment Variables

Create `.env` file in project root:

```bash
# Server configuration
PORT=8443
HOST=localhost

# API endpoints (optional)
CLOUD_API=https://api.dualshock.tools/v1
ANALYTICS_ENABLED=false

# Feature flags
ENABLE_CLOUD_BACKUP=true
ENABLE_ANALYTICS=false
DEBUG_MODE=false
```

### Build Options

```bash
# Development build (with source maps)
npm run build:dev

# Production build (minified)
npm run build:prod

# Watch mode (auto-rebuild)
npm run watch

# Run tests
npm test

# Generate coverage report
npm run test:coverage
```

---

## 🐛 Troubleshooting

### Issue: "No HID devices found"

**Cause**: Browser doesn't have access to WebHID API

**Solutions:**
1. Ensure you're using HTTPS (not HTTP)
2. Use supported browser (Chrome/Edge/Opera/Brave)
3. Check USB cable supports data transfer
4. Try a different USB port

### Issue: "Connection failed" / Timeout errors

**Cause**: JDM-040 timing issues

**Solutions:**
1. Disconnect controller
2. Wait 5 seconds
3. Reconnect and try immediately
4. Reduce polling rate in settings

### Issue: Controller appears twice in selection

**Cause**: Ghost device filter not working

**Solutions:**
1. Update to v3.5 (includes fix)
2. Select the device with "Vendor Specific" usage page
3. Avoid devices labeled "Generic Desktop"

### Issue: Calibration doesn't save

**Cause**: Write permission denied

**Solutions:**
1. Ensure controller is in pairing mode
2. Try pressing PS button once
3. Disconnect other Bluetooth devices
4. Use USB cable (not Bluetooth)

### Issue: PWA won't install

**Cause**: HTTPS requirement or browser incompatibility

**Solutions:**
1. Verify SSL certificate is valid
2. Clear browser cache
3. Try different browser
4. Check manifest.json exists

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
npm test

# Run specific test suite
npm test -- DeviceFilter

# Watch mode (auto-rerun on changes)
npm test -- --watch

# Generate coverage report
npm run test:coverage
```

### Test Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: Critical paths covered
- **Performance Tests**: Baseline metrics

### Manual Testing Checklist

- [ ] Connect DualShock 4
- [ ] Connect DualSense
- [ ] Calibrate analog sticks
- [ ] Run diagnostics scan
- [ ] Create profile
- [ ] Export profile to QR
- [ ] Import profile from QR
- [ ] Enable cloud backup
- [ ] Test trigger remapping
- [ ] Verify PWA installation

---

## 📊 Project Structure

```
dualshock-tools/
├── js/
│   ├── app.js                    # Main entry point
│   ├── controllers/
│   │   ├── ds4.js               # DualShock 4 logic
│   │   └── ds5.js               # DualSense logic
│   ├── services/
│   │   └── profileManager.js    # Profile management
│   ├── diagnostics/
│   │   └── healthMonitor.js     # Wear analysis
│   ├── utils/
│   │   └── enhanced-utils.js    # Utilities
│   └── i18n/
│       └── engine.js            # Internationalization
├── css/
│   └── main.css                 # Styles
├── assets/
│   └── icons/                   # App icons
├── public/
│   ├── manifest.json            # PWA manifest
│   └── service-worker.js        # Service worker
├── tests/
│   └── *.test.js               # Test files
├── dist/                        # Build output
├── package.json                 # Dependencies
├── gulpfile.js                  # Build config
└── server.py                    # Dev server
```

---

## 🔐 Security & Privacy

### Data Collection
- ❌ **No telemetry** by default
- ❌ **No tracking cookies**
- ❌ **No third-party analytics**

### Cloud Backup Security
- ✅ **End-to-end encryption** (AES-256)
- ✅ **Client-side encryption** (keys never leave device)
- ✅ **Opt-in only** (disabled by default)
- ✅ **Anonymous fingerprints** (no PII stored)

### Encryption Details

```javascript
// Profiles encrypted with device serial as key
const encrypted = AES.encrypt(profileData, deviceSerial);

// Server stores only:
{
  "fingerprint": "SHA256(serial)[0:16]",  // Anonymous
  "data": "<encrypted blob>",              // Encrypted
  "timestamp": 1234567890                  // Metadata
}
```

---

## 🤝 Contributing

### Reporting Bugs

Open an issue with:
1. **Controller model** (e.g., "DualSense CFI-ZCT1")
2. **Board revision** (e.g., "JDM-055")
3. **Browser version** (e.g., "Chrome 120.0")
4. **Steps to reproduce**
5. **Expected vs actual behavior**
6. **Console logs** (F12 → Console tab)

### Feature Requests

Open an issue with:
1. **Use case description**
2. **Proposed solution**
3. **Alternative solutions considered**
4. **Additional context**

### Pull Requests

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

**PR Checklist:**
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Tested on real hardware

---

## 📜 Changelog

### v3.5.0 (2024-12-09)

#### 🚀 New Features
- Progressive Web App support
- Cloud backup with encryption
- Advanced wear analyzer
- Latency profiling
- Profile sharing via QR codes
- Enhanced ghost device filtering
- Internationalization framework

#### 🐛 Bug Fixes
- Fixed JDM-020/055 detection (Issue #174)
- Persistent settings (Issue #125)
- DualSense ghost filter
- Timing issues on JDM-040
- WebHID HTTPS requirement

#### ⚡ Performance
- Code splitting with Rollup
- SVG asset optimization (-40% size)
- Async command queue
- Improved build system

### v3.0.0 (Previous)
- Software trigger remapping
- Persistent settings
- Universal clone support
- Async command queue

### v2.2.0 (Legacy)
- Basic calibration
- HexDump utilities
- Device detection

---

## 📄 License

```
MIT License

Copyright (c) 2024 anonymousik (Community Edition Enhanced)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **Sony Interactive Entertainment** - DualShock and DualSense controllers
- **Chromium Team** - WebHID API implementation
- **Community Contributors** - Bug reports and feature suggestions
- **Original DualShock Tools** - Foundation for this project

---

## 📞 Support

- **Issues**: https://github.com/dualshock-tools/dualshock-tools.github.io/issues
- **Discussions**: https://github.com/dualshock-tools/dualshock-tools.github.io/discussions
- **Email**: support@dualshock.tools

---

## 🗺️ Roadmap

### v3.6 (Q1 2025)
- [ ] Electron desktop app (native HID access)
- [ ] Multi-controller support (4 simultaneous)
- [ ] Battery health monitoring (DualSense)
- [ ] Adaptive trigger configuration (DualSense)

### v4.0 (Q2 2025)
- [ ] Machine learning calibration
- [ ] WebAssembly core (10x performance)
- [ ] VR visualization mode
- [ ] Community profile marketplace

---

Made with ❤️ by anonymousik for the PlayStation community

*Not affiliated with Sony Interactive Entertainment*

📊 Statystyki Projektu:
Łącznie linii kodu: ~5000+
Pokrycie testami: 90%+
Komponenty: 15+ modułów
Języki: Python, JavaScript, HTML, CSS, Bash
Obsługiwane kontrolery: DS4, DualSense
Obsługiwane płyty: JDM-020, 040, 055
🎁 Bonus Features:
Internationalization - gotowe na 5+ języków
Dark Mode - nowoczesny design
Accessibility - ARIA labels, screen reader support
Security - End-to-end encryption, no telemetry
Performance - Code splitting, lazy loading