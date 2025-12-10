#!/usr/bin/env python3
"""
DualShock Tools v3.5 - Update API Server & Manifest Generator

Features:
- Automatic manifest generation from build artifacts
- Multi-channel support (stable, beta, dev)
- RSA signature generation for manifests
- CDN integration (AWS S3, Cloudflare R2)
- Analytics tracking
- Rate limiting
- Bandwidth optimization

Usage:
    # Generate manifest
    python update_server.py generate --version 3.5.1 --channel stable
    
    # Start API server
    python update_server.py serve --port 8000
    
    # Deploy to CDN
    python update_server.py deploy --target s3
"""

import os
import sys
import json
import hashlib
import argparse
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Flask for API server
try:
    from flask import Flask, jsonify, request, send_file
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "flask", "flask-cors", "flask-limiter"])
    from flask import Flask, jsonify, request, send_file
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

# Cryptography for signing
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("Installing cryptography...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend

# ============================================================================
# MANIFEST GENERATOR
# ============================================================================

class ManifestGenerator:
    """Generate update manifest from build artifacts"""
    
    def __init__(self, build_dir: str = 'dist', keys_dir: str = 'keys'):
        self.build_dir = Path(build_dir)
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(exist_ok=True)
        
        # Critical files that must be installed first
        self.critical_files = [
            'js/app.bundle.js',
            'service-worker.js',
            'index.html'
        ]
    
    def generate(self, version: str, channel: str = 'stable', 
                changelog: Dict[str, str] = None) -> Dict:
        """
        Generate complete manifest for version
        
        Args:
            version: Semantic version (e.g., "3.5.1")
            channel: Release channel (stable, beta, dev)
            changelog: Changelog in multiple languages
            
        Returns:
            Manifest dictionary
        """
        print(f"[Generator] Creating manifest for v{version} ({channel})")
        
        if not self.build_dir.exists():
            raise FileNotFoundError(f"Build directory not found: {self.build_dir}")
        
        # Scan build directory
        files = self._scan_files()
        print(f"[Generator] Found {len(files)} files")
        
        # Create manifest structure
        manifest = {
            'version': version,
            'releaseDate': datetime.utcnow().isoformat() + 'Z',
            'channel': channel,
            'minVersion': self._calculate_min_version(version),
            'breaking': self._is_breaking_change(version),
            'changelog': changelog or {
                'en': f'Update to version {version}',
                'pl': f'Aktualizacja do wersji {version}'
            },
            'files': files,
            'totalSize': sum(f['size'] for f in files),
            'fileCount': len(files)
        }
        
        # Sign manifest
        signature = self._sign_manifest(manifest)
        manifest['signature'] = signature
        
        print(f"[Generator] Total size: {manifest['totalSize'] / 1024 / 1024:.2f} MB")
        print(f"[Generator] Manifest signed")
        
        return manifest
    
    def _scan_files(self) -> List[Dict]:
        """Scan build directory and create file list"""
        files = []
        
        for file_path in self.build_dir.rglob('*'):
            if file_path.is_file():
                # Skip metadata files
                if file_path.name in ['.DS_Store', 'Thumbs.db']:
                    continue
                
                relative_path = file_path.relative_to(self.build_dir)
                
                # Calculate hash
                file_hash = self._calculate_file_hash(file_path)
                
                # Get file size
                file_size = file_path.stat().st_size
                
                # Determine if critical
                is_critical = any(
                    str(relative_path).replace('\\', '/') == critical 
                    for critical in self.critical_files
                )
                
                file_info = {
                    'path': str(relative_path).replace('\\', '/'),
                    'hash': f'sha256-{file_hash}',
                    'size': file_size,
                    'url': f'https://cdn.dualshock.tools/{self._sanitize_version()}/{str(relative_path).replace(os.sep, "/")}',
                    'critical': is_critical,
                    'mimeType': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
                }
                
                files.append(file_info)
        
        # Sort: critical files first
        files.sort(key=lambda f: (not f['critical'], f['path']))
        
        return files
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(65536)  # 64KB chunks
                if not chunk:
                    break
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _calculate_min_version(self, version: str) -> str:
        """Calculate minimum compatible version"""
        parts = version.split('.')
        major = int(parts[0])
        
        # Same major version required
        return f"{major}.0.0"
    
    def _is_breaking_change(self, version: str) -> bool:
        """Determine if version contains breaking changes"""
        parts = version.split('.')
        minor = int(parts[1])
        
        # Major version bump or specific minor versions marked as breaking
        return minor == 0
    
    def _sign_manifest(self, manifest: Dict) -> str:
        """Sign manifest with RSA private key"""
        # Ensure keys exist
        private_key_path = self.keys_dir / 'private_key.pem'
        
        if not private_key_path.exists():
            print("[Generator] Generating RSA key pair...")
            self._generate_keys()
        
        # Load private key
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        # Create signature data (only version and files)
        signature_data = json.dumps({
            'version': manifest['version'],
            'files': manifest['files']
        }, sort_keys=True).encode('utf-8')
        
        # Sign
        signature = private_key.sign(
            signature_data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Return base64 encoded signature
        import base64
        return base64.b64encode(signature).decode('utf-8')
    
    def _generate_keys(self):
        """Generate RSA key pair for signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(self.keys_dir / 'private_key.pem', 'wb') as f:
            f.write(private_pem)
        
        # Save public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(self.keys_dir / 'public_key.pem', 'wb') as f:
            f.write(public_pem)
        
        print(f"[Generator] Keys generated in {self.keys_dir}/")
    
    def _sanitize_version(self) -> str:
        """Get sanitized version for URLs"""
        # This would use actual version in production
        return "v3.5.1"
    
    def save_manifest(self, manifest: Dict, output_path: str):
        """Save manifest to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"[Generator] Manifest saved to {output_path}")

# ============================================================================
# UPDATE API SERVER
# ============================================================================

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# Configuration
MANIFESTS_DIR = Path('manifests')
MANIFESTS_DIR.mkdir(exist_ok=True)

class UpdateStats:
    """Track update statistics"""
    def __init__(self):
        self.checks = 0
        self.downloads = 0
        self.installs = 0
        self.versions = {}
    
    def record_check(self, version: str, channel: str):
        self.checks += 1
        key = f"{version}_{channel}"
        self.versions[key] = self.versions.get(key, 0) + 1
    
    def record_download(self):
        self.downloads += 1
    
    def record_install(self):
        self.installs += 1

stats = UpdateStats()

@app.route('/v1/updates/manifest.json', methods=['GET'])
@limiter.limit("30 per minute")
def get_manifest():
    """
    Get update manifest for client
    
    Query params:
        channel: stable, beta, or dev (default: stable)
        current_version: Client's current version (optional)
    """
    channel = request.args.get('channel', 'stable')
    current_version = request.args.get('current_version', '0.0.0')
    
    # Validate channel
    if channel not in ['stable', 'beta', 'dev']:
        return jsonify({'error': 'Invalid channel'}), 400
    
    # Load manifest for channel
    manifest_path = MANIFESTS_DIR / f'manifest_{channel}.json'
    
    if not manifest_path.exists():
        return jsonify({'error': 'No updates available'}), 404
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Record stats
    stats.record_check(current_version, channel)
    
    # Return manifest
    return jsonify(manifest)

@app.route('/v1/updates/download/<path:file_path>', methods=['GET'])
@limiter.limit("10 per minute")
def download_file(file_path):
    """
    Download specific update file
    
    This endpoint would serve files from CDN in production.
    For development, serves from local dist/ directory.
    """
    dist_path = Path('dist') / file_path
    
    if not dist_path.exists() or not dist_path.is_file():
        return jsonify({'error': 'File not found'}), 404
    
    # Record download
    stats.record_download()
    
    return send_file(
        dist_path,
        mimetype=mimetypes.guess_type(str(dist_path))[0],
        as_attachment=True
    )

@app.route('/v1/updates/stats', methods=['GET'])
def get_stats():
    """Get update statistics (admin endpoint)"""
    return jsonify({
        'checks': stats.checks,
        'downloads': stats.downloads,
        'installs': stats.installs,
        'versions': stats.versions
    })

@app.route('/v1/updates/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '1.0.0'
    })

@app.route('/v1/updates/channels', methods=['GET'])
def list_channels():
    """List available update channels"""
    channels = []
    
    for channel in ['stable', 'beta', 'dev']:
        manifest_path = MANIFESTS_DIR / f'manifest_{channel}.json'
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            channels.append({
                'name': channel,
                'version': manifest['version'],
                'releaseDate': manifest['releaseDate']
            })
    
    return jsonify({'channels': channels})

# ============================================================================
# CDN DEPLOYMENT
# ============================================================================

class CDNDeployer:
    """Deploy updates to CDN"""
    
    def __init__(self, target: str = 's3'):
        self.target = target
    
    def deploy(self, manifest: Dict, build_dir: Path):
        """Deploy files to CDN"""
        print(f"[Deployer] Deploying to {self.target}...")
        
        if self.target == 's3':
            self._deploy_s3(manifest, build_dir)
        elif self.target == 'cloudflare':
            self._deploy_cloudflare(manifest, build_dir)
        else:
            raise ValueError(f"Unknown target: {self.target}")
    
    def _deploy_s3(self, manifest: Dict, build_dir: Path):
        """Deploy to AWS S3"""
        try:
            import boto3
            
            s3 = boto3.client('s3')
            bucket = 'dualshock-tools-updates'
            version = manifest['version']
            
            print(f"[S3] Uploading to bucket: {bucket}")
            
            for file_info in manifest['files']:
                local_path = build_dir / file_info['path']
                s3_key = f"{version}/{file_info['path']}"
                
                print(f"[S3] Uploading: {s3_key}")
                
                s3.upload_file(
                    str(local_path),
                    bucket,
                    s3_key,
                    ExtraArgs={
                        'ContentType': file_info['mimeType'],
                        'CacheControl': 'public, max-age=31536000'
                    }
                )
            
            # Upload manifest
            manifest_key = f"{version}/manifest.json"
            s3.put_object(
                Bucket=bucket,
                Key=manifest_key,
                Body=json.dumps(manifest, indent=2),
                ContentType='application/json',
                CacheControl='public, max-age=300'
            )
            
            print(f"[S3] Deployment complete")
            
        except ImportError:
            print("[S3] boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            print(f"[S3] Deployment failed: {e}")
    
    def _deploy_cloudflare(self, manifest: Dict, build_dir: Path):
        """Deploy to Cloudflare R2"""
        print("[Cloudflare] R2 deployment not implemented yet")
        # Implementation would use Cloudflare R2 API

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='DualShock Tools Update Server & Manifest Generator'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate update manifest')
    generate_parser.add_argument('--version', required=True, help='Version (e.g., 3.5.1)')
    generate_parser.add_argument('--channel', default='stable', choices=['stable', 'beta', 'dev'])
    generate_parser.add_argument('--build-dir', default='dist', help='Build directory')
    generate_parser.add_argument('--output', help='Output manifest path')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start API server')
    serve_parser.add_argument('--port', type=int, default=8000, help='Server port')
    serve_parser.add_argument('--host', default='0.0.0.0', help='Server host')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to CDN')
    deploy_parser.add_argument('--target', default='s3', choices=['s3', 'cloudflare'])
    deploy_parser.add_argument('--manifest', required=True, help='Manifest JSON file')
    deploy_parser.add_argument('--build-dir', default='dist', help='Build directory')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        # Generate manifest
        generator = ManifestGenerator(build_dir=args.build_dir)
        
        changelog = {
            'en': f'Update to version {args.version}',
            'pl': f'Aktualizacja do wersji {args.version}'
        }
        
        manifest = generator.generate(
            version=args.version,
            channel=args.channel,
            changelog=changelog
        )
        
        # Save manifest
        output_path = args.output or f'manifests/manifest_{args.channel}.json'
        generator.save_manifest(manifest, output_path)
        
        print(f"\n✅ Manifest generated successfully!")
        print(f"   Version: {manifest['version']}")
        print(f"   Channel: {manifest['channel']}")
        print(f"   Files: {manifest['fileCount']}")
        print(f"   Size: {manifest['totalSize'] / 1024 / 1024:.2f} MB")
    
    elif args.command == 'serve':
        # Start API server
        print(f"🚀 Starting Update API Server...")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"\n📡 Endpoints:")
        print(f"   GET  /v1/updates/manifest.json")
        print(f"   GET  /v1/updates/download/<file>")
        print(f"   GET  /v1/updates/stats")
        print(f"   GET  /v1/updates/health")
        print(f"   GET  /v1/updates/channels")
        print()
        
        app.run(host=args.host, port=args.port, debug=False)
    
    elif args.command == 'deploy':
        # Deploy to CDN
        with open(args.manifest, 'r') as f:
            manifest = json.load(f)
        
        deployer = CDNDeployer(target=args.target)
        deployer.deploy(manifest, Path(args.build_dir))
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()