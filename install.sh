#!/bin/bash

################################################################################
# DualShock Tools v3.5 - Master Installation & Deployment Script
# Author: anonymousik (Community Edition Enhanced)
# License: MIT
#
# This script automates the complete installation, migration, and deployment
# process for DualShock Tools v3.5.
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
VERSION="3.5.0"
PROJECT_NAME="dualshock-tools"
REPO_URL="https://github.com/dualshock-tools/dualshock-tools.github.io.git"
PORT=8443
CERT_FILE="server.pem"
KEY_FILE="server.key"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${BOLD}  DualShock Tools v${VERSION} - Master Installer                      ${NC}${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}${BOLD}▶ $1${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

################################################################################
# Requirement Checks
################################################################################

check_requirements() {
    print_section "Checking System Requirements"
    
    local all_ok=true
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js installed: $NODE_VERSION"
    else
        print_error "Node.js not found!"
        print_info "Install from: https://nodejs.org/"
        all_ok=false
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm installed: v$NPM_VERSION"
    else
        print_error "npm not found!"
        all_ok=false
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python installed: $PYTHON_VERSION"
    else
        print_error "Python 3 not found!"
        print_info "Install from: https://www.python.org/"
        all_ok=false
    fi
    
    # Check OpenSSL
    if command -v openssl &> /dev/null; then
        OPENSSL_VERSION=$(openssl version | cut -d' ' -f2)
        print_success "OpenSSL installed: $OPENSSL_VERSION"
    else
        print_error "OpenSSL not found!"
        print_info "Install via: sudo apt install openssl (Linux) or brew install openssl (macOS)"
        all_ok=false
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_success "Git installed: v$GIT_VERSION"
    else
        print_warning "Git not found (optional for updates)"
    fi
    
    if [ "$all_ok" = false ]; then
        echo ""
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
}

################################################################################
# Project Setup
################################################################################

setup_project() {
    print_section "Setting Up Project Structure"
    
    # Create main directories
    mkdir -p js/{controllers,services,diagnostics,utils,i18n}
    mkdir -p css
    mkdir -p assets/icons
    mkdir -p public
    mkdir -p tests
    mkdir -p lang
    
    print_success "Created directory structure"
    
    # Generate package.json if not exists
    if [ ! -f package.json ]; then
        print_info "Generating package.json..."
        cat > package.json << 'EOF'
{
  "name": "dualshock-tools",
  "version": "3.5.0",
  "description": "Professional calibration tool for PlayStation controllers",
  "main": "js/app.js",
  "scripts": {
    "dev": "gulp watch",
    "build": "gulp build",
    "build:dev": "NODE_ENV=development gulp build",
    "build:prod": "NODE_ENV=production gulp build",
    "serve": "python3 server.py",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint js/**/*.js"
  },
  "dependencies": {
    "crypto-js": "^4.2.0",
    "lz-string": "^1.5.0"
  },
  "devDependencies": {
    "@babel/core": "^7.23.0",
    "@babel/preset-env": "^7.23.0",
    "@rollup/plugin-babel": "^6.0.4",
    "@rollup/plugin-commonjs": "^25.0.7",
    "@rollup/plugin-node-resolve": "^15.2.3",
    "gulp": "^4.0.2",
    "gulp-clean-css": "^4.3.0",
    "gulp-htmlmin": "^5.0.1",
    "gulp-terser": "^2.1.0",
    "rollup": "^4.9.0",
    "eslint": "^8.56.0",
    "jest": "^29.7.0"
  },
  "keywords": [
    "dualshock",
    "dualsense",
    "ps4",
    "ps5",
    "controller",
    "calibration",
    "webhid"
  ],
  "author": "anonymousik",
  "license": "MIT"
}
EOF
        print_success "Generated package.json"
    fi
}

################################################################################
# Dependency Installation
################################################################################

install_dependencies() {
    print_section "Installing NPM Dependencies"
    
    if [ -f package.json ]; then
        print_info "Running npm install..."
        npm install --silent
        print_success "Dependencies installed"
    else
        print_error "package.json not found!"
        exit 1
    fi
}

################################################################################
# SSL Certificate Generation
################################################################################

generate_ssl() {
    print_section "Generating SSL Certificates"
    
    if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        print_warning "Certificates already exist. Skipping generation."
        return
    fi
    
    print_info "Generating self-signed certificate..."
    
    openssl req -newkey rsa:2048 -new -nodes -x509 -days 365 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=US/ST=Local/L=Local/O=DualShockTools/CN=localhost" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "SSL certificates generated"
        print_info "Certificate: $CERT_FILE"
        print_info "Private key: $KEY_FILE"
    else
        print_error "Failed to generate certificates"
        exit 1
    fi
}

################################################################################
# PWA Setup
################################################################################

setup_pwa() {
    print_section "Setting Up Progressive Web App"
    
    # Create manifest.json
    cat > public/manifest.json << 'EOF'
{
  "name": "DualShock Tools",
  "short_name": "DS Tools",
  "description": "Professional calibration tool for PlayStation controllers",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#0f3460",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/assets/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
EOF
    print_success "Created manifest.json"
    
    # Create service worker
    cat > public/service-worker.js << 'EOF'
const CACHE_VERSION = 'v3.5.0';
const CACHE_ASSETS = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/app.bundle.js',
  '/assets/icons/icon-192.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_VERSION).then(cache => cache.addAll(CACHE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys => 
      Promise.all(keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then(response => 
      response || fetch(e.request)
    )
  );
});
EOF
    print_success "Created service-worker.js"
}

################################################################################
# Build System
################################################################################

setup_build_system() {
    print_section "Configuring Build System"
    
    # Create gulpfile.js
    cat > gulpfile.js << 'EOF'
const gulp = require('gulp');
const babel = require('@rollup/plugin-babel').default;
const resolve = require('@rollup/plugin-node-resolve').default;
const commonjs = require('@rollup/plugin-commonjs');
const terser = require('gulp-terser');
const cleanCSS = require('gulp-clean-css');
const htmlmin = require('gulp-htmlmin');
const rollup = require('rollup');

const paths = {
  js: { src: 'js/**/*.js', dest: 'dist/js' },
  css: { src: 'css/**/*.css', dest: 'dist/css' },
  html: { src: 'index.html', dest: 'dist' },
  assets: { src: 'assets/**/*', dest: 'dist/assets' },
  public: { src: 'public/**/*', dest: 'dist' }
};

async function scripts() {
  const bundle = await rollup.rollup({
    input: 'js/app.js',
    plugins: [resolve(), commonjs(), babel({ babelHelpers: 'bundled', presets: ['@babel/preset-env'] })]
  });
  await bundle.write({ file: 'dist/js/app.bundle.js', format: 'iife', sourcemap: true });
}

function styles() {
  return gulp.src(paths.css.src).pipe(cleanCSS()).pipe(gulp.dest(paths.css.dest));
}

function html() {
  return gulp.src(paths.html.src)
    .pipe(htmlmin({ collapseWhitespace: true, removeComments: true }))
    .pipe(gulp.dest(paths.html.dest));
}

function assets() {
  return gulp.src(paths.assets.src).pipe(gulp.dest(paths.assets.dest));
}

function publicFiles() {
  return gulp.src(paths.public.src).pipe(gulp.dest(paths.public.dest));
}

function watch() {
  gulp.watch(paths.js.src, scripts);
  gulp.watch(paths.css.src, styles);
  gulp.watch(paths.html.src, html);
}

const build = gulp.series(gulp.parallel(scripts, styles, html, assets, publicFiles));

exports.scripts = scripts;
exports.styles = styles;
exports.html = html;
exports.watch = watch;
exports.build = build;
exports.default = build;
EOF
    print_success "Created gulpfile.js"
}

################################################################################
# Development Server
################################################################################

create_server() {
    print_section "Creating Development Server"
    
    cat > server.py << 'EOF'
#!/usr/bin/env python3
"""
DualShock Tools v3.5 - Development Server
"""

import http.server
import ssl
import webbrowser
import sys
from pathlib import Path

PORT = 8443
CERT_FILE = "server.pem"
KEY_FILE = "server.key"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="dist", **kwargs)
    
    def end_headers(self):
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()

def main():
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║  🎮 DualShock Tools v3.5 - Development Server                      ║
╚════════════════════════════════════════════════════════════════════╝

Server: https://localhost:{PORT}
Status: Starting...
    """)
    
    if not Path(CERT_FILE).exists() or not Path(KEY_FILE).exists():
        print("❌ SSL certificates not found!")
        print("   Run: ./install.sh")
        sys.exit(1)
    
    server_address = ('localhost', PORT)
    httpd = http.server.HTTPServer(server_address, CustomHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"✓ Server running at https://localhost:{PORT}")
    print(f"⚠️  Accept the security warning in your browser\n")
    
    webbrowser.open(f"https://localhost:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x server.py
    print_success "Created server.py"
}

################################################################################
# Project Build
################################################################################

build_project() {
    print_section "Building Project"
    
    if [ -f gulpfile.js ]; then
        print_info "Running build process..."
        npx gulp build
        print_success "Project built successfully"
    else
        print_warning "No build system found, skipping build"
    fi
}

################################################################################
# Migration from v2.2
################################################################################

migrate_from_v22() {
    print_section "Detecting Previous Installation"
    
    if [ -f "js/app.js" ]; then
        print_warning "Existing installation detected"
        echo -e "${YELLOW}Do you want to backup existing files? (yes/no)${NC}"
        read -r response
        
        if [[ "$response" =~ ^[Yy] ]]; then
            BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$BACKUP_DIR"
            
            print_info "Creating backup..."
            cp -r js css assets lang "$BACKUP_DIR/" 2>/dev/null || true
            
            print_success "Backup created: $BACKUP_DIR"
        fi
    fi
}

################################################################################
# Final Setup
################################################################################

finalize_installation() {
    print_section "Finalizing Installation"
    
    # Create .gitignore if not exists
    if [ ! -f .gitignore ]; then
        cat > .gitignore << 'EOF'
node_modules/
dist/
*.log
.env
.DS_Store
server.pem
server.key
coverage/
EOF
        print_success "Created .gitignore"
    fi
    
    # Create README if not exists
    if [ ! -f README.md ]; then
        print_info "Creating README.md..."
        echo "# DualShock Tools v${VERSION}" > README.md
        echo "See full documentation at: https://github.com/dualshock-tools" >> README.md
        print_success "Created README.md"
    fi
    
    print_success "Installation complete!"
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    print_header
    
    echo -e "${BOLD}This script will:${NC}"
    echo "  1. Check system requirements"
    echo "  2. Set up project structure"
    echo "  3. Install dependencies"
    echo "  4. Generate SSL certificates"
    echo "  5. Configure PWA"
    echo "  6. Build the project"
    echo "  7. Create development server"
    echo ""
    echo -e "${YELLOW}Continue? (yes/no)${NC}"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy] ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    check_requirements
    migrate_from_v22
    setup_project
    install_dependencies
    generate_ssl
    setup_pwa
    setup_build_system
    create_server
    build_project
    finalize_installation
    
    # Final message
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${BOLD}  ✅ Installation Complete!                                         ${NC}${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo ""
    echo -e "  ${CYAN}1.${NC} Start the development server:"
    echo -e "     ${BOLD}python3 server.py${NC}"
    echo ""
    echo -e "  ${CYAN}2.${NC} Open in browser:"
    echo -e "     ${BOLD}https://localhost:${PORT}${NC}"
    echo ""
    echo -e "  ${CYAN}3.${NC} Accept the security warning"
    echo -e "     (Click 'Advanced' → 'Proceed to localhost')"
    echo ""
    echo -e "${YELLOW}⚠️  Important:${NC} This app requires a Chromium-based browser"
    echo -e "   (Chrome, Edge, Opera, or Brave)"
    echo ""
    echo -e "${MAGENTA}Made with ❤️  by anonymousik${NC}"
    echo ""
}

# Run main function
main "$@"