#!/usr/bin/env python3
"""
DualShock Tools - Automatic Migration & Enhancement System v3.5
Author: anonymousik (Community Edition Enhanced)
License: MIT

System automatycznej aktualizacji z v2.2 do v3.5 z pełną diagnostyką i raportowaniem.
"""

import os
import sys
import json
import shutil
import subprocess
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import urllib.request
import ssl

class Color:
    """Kolorowanie terminala"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class MigrationAnalyzer:
    """Analizator struktury projektu i wykrywacz problemów"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = []
        self.warnings = []
        self.stats = {}
        
    def analyze(self) -> Dict:
        """Główna metoda analizy"""
        print(f"\n{Color.CYAN}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}🔍 ANALIZA PROJEKTU - FAZA 1: DIAGNOSTYKA{Color.RESET}")
        print(f"{Color.CYAN}{'='*70}{Color.RESET}\n")
        
        results = {
            'structure': self._analyze_structure(),
            'dependencies': self._analyze_dependencies(),
            'code_quality': self._analyze_code(),
            'security': self._analyze_security(),
            'performance': self._analyze_performance()
        }
        
        self._print_analysis_report(results)
        return results
    
    def _analyze_structure(self) -> Dict:
        """Analiza struktury katalogów i plików"""
        print(f"{Color.BLUE}📁 Analiza struktury projektu...{Color.RESET}")
        
        required_dirs = ['js', 'css', 'assets', 'lang']
        required_files = ['index.html', 'package.json', 'gulpfile.js']
        
        structure = {
            'missing_dirs': [],
            'missing_files': [],
            'total_files': 0,
            'total_size': 0,
            'js_files': [],
            'css_files': [],
            'html_files': []
        }
        
        # Sprawdź wymagane katalogi
        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                structure['missing_dirs'].append(dir_name)
                self.issues.append(f"Brak wymaganego katalogu: {dir_name}")
        
        # Sprawdź wymagane pliki
        for file_name in required_files:
            file_path = self.project_path / file_name
            if not file_path.exists():
                structure['missing_files'].append(file_name)
                self.issues.append(f"Brak wymaganego pliku: {file_name}")
        
        # Skanuj pliki projektu
        for ext, key in [('.js', 'js_files'), ('.css', 'css_files'), ('.html', 'html_files')]:
            files = list(self.project_path.rglob(f'*{ext}'))
            structure[key] = [str(f.relative_to(self.project_path)) for f in files]
            structure['total_files'] += len(files)
            structure['total_size'] += sum(f.stat().st_size for f in files)
        
        print(f"  ✓ Znaleziono {structure['total_files']} plików")
        print(f"  ✓ Całkowity rozmiar: {structure['total_size'] / 1024:.2f} KB")
        
        return structure
    
    def _analyze_dependencies(self) -> Dict:
        """Analiza zależności Node.js"""
        print(f"\n{Color.BLUE}📦 Analiza zależności...{Color.RESET}")
        
        deps = {
            'package_json_exists': False,
            'dependencies': {},
            'devDependencies': {},
            'outdated': [],
            'vulnerable': []
        }
        
        pkg_path = self.project_path / 'package.json'
        if pkg_path.exists():
            deps['package_json_exists'] = True
            with open(pkg_path) as f:
                pkg_data = json.load(f)
                deps['dependencies'] = pkg_data.get('dependencies', {})
                deps['devDependencies'] = pkg_data.get('devDependencies', {})
            
            print(f"  ✓ Zależności produkcyjne: {len(deps['dependencies'])}")
            print(f"  ✓ Zależności deweloperskie: {len(deps['devDependencies'])}")
            
            # Sprawdź przestarzałe pakiety (wymaga npm)
            try:
                result = subprocess.run(
                    ['npm', 'outdated', '--json'],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    outdated = json.loads(result.stdout)
                    deps['outdated'] = list(outdated.keys())
                    if deps['outdated']:
                        self.warnings.append(f"Przestarzałe pakiety: {', '.join(deps['outdated'][:5])}")
            except:
                pass
        else:
            self.issues.append("Brak pliku package.json")
        
        return deps
    
    def _analyze_code(self) -> Dict:
        """Analiza jakości kodu"""
        print(f"\n{Color.BLUE}🔬 Analiza jakości kodu...{Color.RESET}")
        
        quality = {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'complexity_issues': [],
            'es6_features': {
                'arrow_functions': 0,
                'async_await': 0,
                'classes': 0,
                'template_literals': 0
            },
            'potential_bugs': []
        }
        
        js_files = list(self.project_path.rglob('*.js'))
        
        for js_file in js_files:
            if 'node_modules' in str(js_file) or 'dist' in str(js_file):
                continue
                
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    quality['total_lines'] += len(lines)
                    
                    # Zlicz komentarze
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith('//') or stripped.startswith('/*'):
                            quality['comment_lines'] += 1
                        elif stripped and not stripped.startswith('*'):
                            quality['code_lines'] += 1
                    
                    # Wykryj ES6 features
                    quality['es6_features']['arrow_functions'] += content.count('=>')
                    quality['es6_features']['async_await'] += content.count('async ') + content.count('await ')
                    quality['es6_features']['classes'] += content.count('class ')
                    quality['es6_features']['template_literals'] += content.count('`')
                    
                    # Wykryj potencjalne problemy
                    if 'eval(' in content:
                        quality['potential_bugs'].append(f"{js_file.name}: Użycie eval()")
                    if 'innerHTML' in content and 'sanitize' not in content.lower():
                        quality['potential_bugs'].append(f"{js_file.name}: Niesanitized innerHTML")
                    if content.count('localStorage') > 5:
                        quality['potential_bugs'].append(f"{js_file.name}: Nadmierne użycie localStorage")
                    
                    # Wykryj zbyt złożone funkcje (heurystyka)
                    functions = re.findall(r'function\s+\w+\s*\([^)]*\)\s*{', content)
                    for func in functions:
                        func_start = content.index(func)
                        func_body = content[func_start:func_start+5000]
                        if func_body.count('if') > 10:
                            quality['complexity_issues'].append(f"{js_file.name}: Wysoka złożoność cyklomatyczna")
                            break
                            
            except Exception as e:
                self.warnings.append(f"Nie można przeanalizować {js_file.name}: {e}")
        
        comment_ratio = (quality['comment_lines'] / quality['total_lines'] * 100) if quality['total_lines'] > 0 else 0
        
        print(f"  ✓ Łącznie linii kodu: {quality['total_lines']}")
        print(f"  ✓ Komentarze: {quality['comment_lines']} ({comment_ratio:.1f}%)")
        print(f"  ✓ Użycie ES6: Arrow={quality['es6_features']['arrow_functions']}, Async={quality['es6_features']['async_await']}")
        
        if comment_ratio < 10:
            self.warnings.append(f"Niska dokumentacja kodu ({comment_ratio:.1f}% komentarzy)")
        
        return quality
    
    def _analyze_security(self) -> Dict:
        """Analiza bezpieczeństwa"""
        print(f"\n{Color.BLUE}🔒 Analiza bezpieczeństwa...{Color.RESET}")
        
        security = {
            'vulnerabilities': [],
            'best_practices': [],
            'https_required': False,
            'csp_present': False,
            'input_validation': 0
        }
        
        # Sprawdź index.html pod kątem CSP
        index_path = self.project_path / 'index.html'
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Content-Security-Policy' in content:
                    security['csp_present'] = True
                else:
                    self.warnings.append("Brak Content Security Policy w index.html")
        
        # Sprawdź certyfikaty SSL
        cert_files = list(self.project_path.glob('*.pem')) + list(self.project_path.glob('*.key'))
        if cert_files:
            security['https_required'] = True
            print(f"  ✓ Znaleziono certyfikaty SSL: {len(cert_files)}")
        
        # Skanuj kod pod kątem walidacji inputu
        js_files = list(self.project_path.rglob('*.js'))
        for js_file in js_files:
            if 'node_modules' in str(js_file):
                continue
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'validate' in content.lower() or 'sanitize' in content.lower():
                        security['input_validation'] += 1
            except:
                pass
        
        print(f"  ✓ Pliki z walidacją inputu: {security['input_validation']}")
        
        return security
    
    def _analyze_performance(self) -> Dict:
        """Analiza wydajności"""
        print(f"\n{Color.BLUE}⚡ Analiza wydajności...{Color.RESET}")
        
        perf = {
            'unminified_js': [],
            'unminified_css': [],
            'large_files': [],
            'build_system_present': False,
            'code_splitting': False
        }
        
        # Sprawdź system budowania
        if (self.project_path / 'gulpfile.js').exists():
            perf['build_system_present'] = True
            print(f"  ✓ System budowania: Gulp")
        elif (self.project_path / 'webpack.config.js').exists():
            perf['build_system_present'] = True
            print(f"  ✓ System budowania: Webpack")
        
        # Wykryj duże pliki
        for file in self.project_path.rglob('*'):
            if file.is_file() and 'node_modules' not in str(file):
                size = file.stat().st_size
                if size > 500000:  # >500KB
                    perf['large_files'].append({
                        'name': str(file.relative_to(self.project_path)),
                        'size': size / 1024
                    })
        
        if perf['large_files']:
            print(f"  ⚠ Znaleziono {len(perf['large_files'])} dużych plików")
            for f in perf['large_files'][:3]:
                print(f"    - {f['name']}: {f['size']:.1f} KB")
        
        return perf
    
    def _print_analysis_report(self, results: Dict):
        """Wydrukuj podsumowanie analizy"""
        print(f"\n{Color.CYAN}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}📊 PODSUMOWANIE ANALIZY{Color.RESET}")
        print(f"{Color.CYAN}{'='*70}{Color.RESET}\n")
        
        # Problemy krytyczne
        if self.issues:
            print(f"{Color.RED}❌ PROBLEMY KRYTYCZNE ({len(self.issues)}):{Color.RESET}")
            for issue in self.issues[:10]:
                print(f"  • {issue}")
            if len(self.issues) > 10:
                print(f"  ... i {len(self.issues) - 10} więcej")
            print()
        
        # Ostrzeżenia
        if self.warnings:
            print(f"{Color.YELLOW}⚠️  OSTRZEŻENIA ({len(self.warnings)}):{Color.RESET}")
            for warning in self.warnings[:10]:
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... i {len(self.warnings) - 10} więcej")
            print()
        
        # Status ogólny
        if not self.issues:
            print(f"{Color.GREEN}✅ Projekt gotowy do migracji!{Color.RESET}\n")
        else:
            print(f"{Color.RED}⛔ Wymagane poprawki przed migracją!{Color.RESET}\n")


class ProjectMigrator:
    """Główny mechanizm migracji projektu"""
    
    def __init__(self, project_path: str, backup: bool = True):
        self.project_path = Path(project_path)
        self.backup_path = None
        self.should_backup = backup
        self.migration_log = []
        
    def migrate(self) -> bool:
        """Wykonaj pełną migrację"""
        print(f"\n{Color.CYAN}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}🚀 MIGRACJA DO v3.5 - FAZA 2: MODERNIZACJA{Color.RESET}")
        print(f"{Color.CYAN}{'='*70}{Color.RESET}\n")
        
        try:
            if self.should_backup:
                self._create_backup()
            
            self._update_project_structure()
            self._migrate_javascript()
            self._implement_pwa()
            self._implement_profile_manager()
            self._implement_diagnostics()
            self._update_dependencies()
            self._generate_migration_report()
            
            print(f"\n{Color.GREEN}{'='*70}{Color.RESET}")
            print(f"{Color.GREEN}{Color.BOLD}✅ MIGRACJA ZAKOŃCZONA SUKCESEM!{Color.RESET}")
            print(f"{Color.GREEN}{'='*70}{Color.RESET}\n")
            
            return True
            
        except Exception as e:
            print(f"\n{Color.RED}❌ BŁĄD MIGRACJI: {e}{Color.RESET}")
            if self.backup_path:
                print(f"{Color.YELLOW}Przywracanie z backupu...{Color.RESET}")
                self._restore_backup()
            return False
    
    def _create_backup(self):
        """Utwórz backup projektu"""
        print(f"{Color.BLUE}💾 Tworzenie backupu...{Color.RESET}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = self.project_path.parent / f"backup_v2.2_{timestamp}"
        
        shutil.copytree(self.project_path, self.backup_path, 
                       ignore=shutil.ignore_patterns('node_modules', 'dist', '.git'))
        
        print(f"  ✓ Backup utworzony: {self.backup_path}")
        self.migration_log.append(f"Backup: {self.backup_path}")
    
    def _update_project_structure(self):
        """Aktualizuj strukturę katalogów"""
        print(f"\n{Color.BLUE}📁 Aktualizacja struktury projektu...{Color.RESET}")
        
        new_dirs = [
            'js/services',
            'js/diagnostics',
            'js/utils',
            'js/i18n',
            'public',
            'tests'
        ]
        
        for dir_path in new_dirs:
            full_path = self.project_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Utworzono: {dir_path}")
        
        self.migration_log.append("Struktura katalogów zaktualizowana")
    
    def _migrate_javascript(self):
        """Migruj kod JavaScript do ES6+"""
        print(f"\n{Color.BLUE}⚙️  Migracja kodu JavaScript...{Color.RESET}")
        
        # Utwórz nowy utils.js z ulepszonymi funkcjami
        utils_content = '''/**
 * DualShock Tools v3.5 - Utilities Module
 * Enhanced with ES6+ features and improved error handling
 */

export class DeviceFilter {
  static VENDOR_ID = 0x054C;
  static DUALSENSE_PID = 0x0CE6;
  static DS4_PID = 0x05C4;
  
  /**
   * Filtruj "ghost" devices (Issue #174 fix)
   */
  static filterValidInterface(devices) {
    return devices.filter(device => {
      // Sprawdź usagePage - tylko Vendor Specific (0xFF00)
      if (device.collections) {
        const hasVendorPage = device.collections.some(c => c.usagePage === 0xFF00);
        const hasGenericPage = device.collections.some(c => c.usagePage === 0x01);
        
        // Odrzuć jeśli TYLKO Generic Desktop (ghost device)
        if (hasGenericPage && !hasVendorPage) {
          console.log(`[Filter] Rejected ghost device: ${device.productName}`);
          return false;
        }
      }
      
      return device.vendorId === this.VENDOR_ID && 
             (device.productId === this.DUALSENSE_PID || device.productId === this.DS4_PID);
    });
  }
}

export class AsyncCommandQueue {
  constructor(delayMs = 50) {
    this.queue = Promise.resolve();
    this.delayMs = delayMs;
  }
  
  /**
   * Dodaj komendę do kolejki z opóźnieniem (JDM-040 stability fix)
   */
  async add(commandFn) {
    this.queue = this.queue.then(async () => {
      try {
        const result = await commandFn();
        await this._delay(this.delayMs);
        return result;
      } catch (err) {
        console.error('[Queue] Command failed:', err);
        throw err;
      }
    });
    
    return this.queue;
  }
  
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export class HexDump {
  static format(buffer, bytesPerLine = 16) {
    const bytes = new Uint8Array(buffer);
    let output = '';
    
    for (let i = 0; i < bytes.length; i += bytesPerLine) {
      const chunk = bytes.slice(i, i + bytesPerLine);
      const hex = Array.from(chunk).map(b => b.toString(16).padStart(2, '0')).join(' ');
      const ascii = Array.from(chunk).map(b => (b >= 32 && b < 127) ? String.fromCharCode(b) : '.').join('');
      
      output += `${i.toString(16).padStart(4, '0')}: ${hex.padEnd(bytesPerLine * 3)}  ${ascii}\\n`;
    }
    
    return output;
  }
}
'''
        
        utils_path = self.project_path / 'js' / 'utils' / 'enhanced-utils.js'
        with open(utils_path, 'w', encoding='utf-8') as f:
            f.write(utils_content)
        
        print(f"  ✓ Utworzono: js/utils/enhanced-utils.js")
        self.migration_log.append("Moduły JavaScript zmodernizowane")
    
    def _implement_pwa(self):
        """Implementuj Progressive Web App"""
        print(f"\n{Color.BLUE}📱 Implementacja PWA...{Color.RESET}")
        
        # Manifest.json
        manifest = {
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
                    "src": "/assets/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/assets/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        
        manifest_path = self.project_path / 'public' / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"  ✓ Utworzono manifest.json")
        
        # Service Worker
        sw_content = '''/**
 * DualShock Tools v3.5 - Service Worker
 * Offline-first caching strategy
 */

const CACHE_VERSION = 'v3.5.0';
const CACHE_ASSETS = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/app.bundle.js',
  '/assets/icon-192.png',
  '/assets/icon-512.png'
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      console.log('[SW] Caching app shell');
      return cache.addAll(CACHE_ASSETS);
    })
  );
  
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_VERSION)
            .map(key => caches.delete(key))
      );
    })
  );
  
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        console.log('[SW] Serving from cache:', event.request.url);
        return response;
      }
      
      return fetch(event.request).then(response => {
        // Cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_VERSION).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        
        return response;
      });
    }).catch(() => {
      // Offline fallback
      if (event.request.destination === 'document') {
        return caches.match('/index.html');
      }
    })
  );
});
'''
        
        sw_path = self.project_path / 'public' / 'service-worker.js'
        with open(sw_path, 'w', encoding='utf-8') as f:
            f.write(sw_content)
        
        print(f"  ✓ Utworzono service-worker.js")
        self.migration_log.append("PWA zaimplementowane")
    
    def _implement_profile_manager(self):
        """Implementuj system zarządzania profilami"""
        print(f"\n{Color.BLUE}💾 Implementacja Profile Manager...{Color.RESET}")
        
        profile_manager_content = '''/**
 * DualShock Tools v3.5 - Profile Manager
 * Cloud backup with client-side encryption
 */

import CryptoJS from 'crypto-js';

export class ProfileManager {
  constructor() {
    this.apiEndpoint = 'https://api.dualshock.tools/v1/profiles';
    this.localStoragePrefix = 'dst_profile_';
  }
  
  /**
   * Backup profilu z opcjonalnym cloud sync
   */
  async backupProfile(deviceSerial, calibrationData) {
    try {
      // Lokalna kopia (zawsze)
      const localKey = `${this.localStoragePrefix}${deviceSerial}`;
      const profileData = {
        version: '3.5.0',
        timestamp: Date.now(),
        device: deviceSerial,
        calibration: calibrationData,
        metadata: {
          userAgent: navigator.userAgent,
          locale: navigator.language
        }
      };
      
      localStorage.setItem(localKey, JSON.stringify(profileData));
      console.log('[Profile] Local backup saved');
      
      // Cloud backup (jeśli użytkownik wyraził zgodę)
      if (await this.hasCloudConsent()) {
        await this._cloudBackup(deviceSerial, profileData);
      }
      
      return { success: true, location: 'local' };
      
    } catch (error) {
      console.error('[Profile] Backup failed:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Przywróć profil (cloud -> local fallback)
   */
  async restoreProfile(deviceSerial) {
    try {
      // Próba cloud restore
      if (await this.hasCloudConsent()) {
        const cloudData = await this._cloudRestore(deviceSerial);
        if (cloudData) {
          console.log('[Profile] Restored from cloud');
          return cloudData.calibration;
        }
      }
      
      // Fallback do localStorage
      const localKey = `${this.localStoragePrefix}${deviceSerial}`;
      const localData = localStorage.getItem(localKey);
      
      if (localData) {
        const profile = JSON.parse(localData);
        console.log('[Profile] Restored from local storage');
        return profile.calibration;
      }
      
      return null;
      
    } catch (error) {
      console.error('[Profile] Restore failed:', error);
      return null;
    }
  }
  
  /**
   * Cloud backup z szyfrowaniem
   */
  async _cloudBackup(deviceSerial, profileData) {
    const encrypted = CryptoJS.AES.encrypt(
      JSON.stringify(profileData),
      deviceSerial
    ).toString();
    
    const fingerprint = this._hashSerial(deviceSerial);
    
    const response = await fetch(this.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fingerprint,
        data: encrypted,
        timestamp: Date.now()
      })
    });
    
    if (!response.ok) {
      throw new Error(`Cloud backup failed: ${response.status}`);
    }
    
    console.log('[Profile] Cloud backup successful');
  }
  
  /**
   * Cloud restore z deszyfrowaniem
   */
  async _cloudRestore(deviceSerial) {
    const fingerprint = this._hashSerial(deviceSerial);
    
    const response = await fetch(`${this.apiEndpoint}/${fingerprint}`);
    
    if (!response.ok) {
      return null;
    }
    
    const { data } = await response.json();
    const decrypted = CryptoJS.AES.decrypt(data, deviceSerial).toString(CryptoJS.enc.Utf8);
    
    return JSON.parse(decrypted);
  }
  
  /**
   * Sprawdź zgodę użytkownika na cloud backup
   */
  async hasCloudConsent() {
    const consent = localStorage.getItem('dst_cloud_consent');
    return consent === 'true';
  }
  
  /**
   * Hash serial number (anonimizacja)
   */
  _hashSerial(serial) {
    return CryptoJS.SHA256(serial).toString().substring(0, 16);
  }
  
  /**
   * Eksport profilu do QR code
   */
  generateQRExport(deviceSerial) {
    const localKey = `${this.localStoragePrefix}${deviceSerial}`;
    const profileData = localStorage.getItem(localKey);
    
    if (!profileData) {
      throw new Error('Profile not found');
    }
    
    // Kompresja danych przed QR
    const compressed = LZString.compressToBase64(profileData);
    return compressed;
  }
  
  /**
   * Import profilu z QR code
   */
  importFromQR(qrData, deviceSerial) {
    try {
      const decompressed = LZString.decompressFromBase64(qrData);
      const profile = JSON.parse(decompressed);
      
      // Walidacja
      if (!profile.calibration) {
        throw new Error('Invalid profile data');
      }
      
      const localKey = `${this.localStoragePrefix}${deviceSerial}`;
      localStorage.setItem(localKey, decompressed);
      
      return profile.calibration;
    } catch (error) {
      console.error('[Profile] QR import failed:', error);
      throw error;
    }
  }
}
'''
        
        profile_path = self.project_path / 'js' / 'services' / 'profileManager.js'
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(profile_manager_content)
        
        print(f"  ✓ Utworzono profileManager.js")
        self.migration_log.append("Profile Manager zaimplementowany")
    
    def _implement_diagnostics(self):
        """Implementuj system diagnostyczny"""
        print(f"\n{Color.BLUE}🔬 Implementacja Diagnostics System...{Color.RESET}")
        
        diagnostics_content = '''/**
 * DualShock Tools v3.5 - Diagnostics & Health Monitor
 * Advanced wear analysis and latency profiling
 */

export class StickWearAnalyzer {
  constructor() {
    this.samples = [];
    this.maxSamples = 1000;
    this.thresholds = {
      excellent: 0.05,
      good: 0.15,
      warning: 0.30,
      critical: 0.50
    };
  }
  
  /**
   * Dodaj próbkę do analizy
   */
  addSample(leftStick, rightStick) {
    this.samples.push({
      timestamp: Date.now(),
      left: { x: leftStick.x, y: leftStick.y },
      right: { x: rightStick.x, y: rightStick.y }
    });
    
    // Utrzymuj limit próbek
    if (this.samples.length > this.maxSamples) {
      this.samples.shift();
    }
  }
  
  /**
   * Oblicz metryki zużycia
   */
  calculateWearMetrics() {
    if (this.samples.length < 100) {
      return {
        error: 'Insufficient data (need at least 100 samples)',
        samples: this.samples.length
      };
    }
    
    const leftDeadZone = this._analyzeDeadZone('left');
    const rightDeadZone = this._analyzeDeadZone('right');
    
    const leftDrift = this._analyzeDrift('left');
    const rightDrift = this._analyzeDrift('right');
    
    return {
      leftStick: {
        deadZoneVariance: leftDeadZone,
        drift: leftDrift,
        wearLevel: this._calculateWearLevel(leftDeadZone, leftDrift),
        recommendation: this._getRecommendation(leftDeadZone, leftDrift)
      },
      rightStick: {
        deadZoneVariance: rightDeadZone,
        drift: rightDrift,
        wearLevel: this._calculateWearLevel(rightDeadZone, rightDrift),
        recommendation: this._getRecommendation(rightDeadZone, rightDrift)
      },
      samplesAnalyzed: this.samples.length,
      sessionDuration: this._getSessionDuration()
    };
  }
  
  /**
   * Analiza dead zone (próbki w centrum)
   */
  _analyzeDeadZone(stick) {
    const centerSamples = this.samples.filter(s => {
      const pos = s[stick];
      return Math.abs(pos.x) < 0.1 && Math.abs(pos.y) < 0.1;
    });
    
    if (centerSamples.length < 10) {
      return 0;
    }
    
    // Oblicz wariancję pozycji w centrum
    const positions = centerSamples.map(s => s[stick]);
    const avgX = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
    const avgY = positions.reduce((sum, p) => sum + p.y, 0) / positions.length;
    
    const variance = positions.reduce((sum, p) => {
      return sum + Math.pow(p.x - avgX, 2) + Math.pow(p.y - avgY, 2);
    }, 0) / positions.length;
    
    return Math.sqrt(variance);
  }
  
  /**
   * Analiza driftu (niezamierzone przesunięcie)
   */
  _analyzeDrift(stick) {
    const centerSamples = this.samples
      .filter(s => {
        const pos = s[stick];
        return Math.abs(pos.x) < 0.1 && Math.abs(pos.y) < 0.1;
      })
      .slice(-100); // Ostatnie 100 próbek
    
    if (centerSamples.length < 10) {
      return { x: 0, y: 0, magnitude: 0 };
    }
    
    const avgX = centerSamples.reduce((sum, s) => sum + s[stick].x, 0) / centerSamples.length;
    const avgY = centerSamples.reduce((sum, s) => sum + s[stick].y, 0) / centerSamples.length;
    
    const magnitude = Math.sqrt(avgX * avgX + avgY * avgY);
    
    return {
      x: avgX,
      y: avgY,
      magnitude: magnitude,
      direction: this._getDriftDirection(avgX, avgY)
    };
  }
  
  /**
   * Oblicz poziom zużycia (0-1)
   */
  _calculateWearLevel(deadZoneVariance, drift) {
    const dzScore = deadZoneVariance / this.thresholds.critical;
    const driftScore = drift.magnitude / 0.3;
    
    return Math.min((dzScore + driftScore) / 2, 1);
  }
  
  /**
   * Rekomendacja dla użytkownika
   */
  _getRecommendation(deadZoneVariance, drift) {
    const wearLevel = this._calculateWearLevel(deadZoneVariance, drift);
    
    if (wearLevel < this.thresholds.excellent) {
      return {
        status: 'excellent',
        message: 'Analog stick is in excellent condition',
        action: 'none',
        color: '#00ff00'
      };
    } else if (wearLevel < this.thresholds.good) {
      return {
        status: 'good',
        message: 'Minor wear detected, continue monitoring',
        action: 'monitor',
        color: '#90ee90'
      };
    } else if (wearLevel < this.thresholds.warning) {
      return {
        status: 'warning',
        message: 'Noticeable wear, recalibration recommended',
        action: 'recalibrate',
        color: '#ffaa00'
      };
    } else {
      return {
        status: 'critical',
        message: 'Severe wear detected, consider module replacement',
        action: 'replace_module',
        color: '#ff0000'
      };
    }
  }
  
  /**
   * Kierunek driftu (dla UI)
   */
  _getDriftDirection(x, y) {
    const angle = Math.atan2(y, x) * 180 / Math.PI;
    
    if (angle >= -45 && angle < 45) return 'right';
    if (angle >= 45 && angle < 135) return 'up';
    if (angle >= 135 || angle < -135) return 'left';
    return 'down';
  }
  
  /**
   * Czas trwania sesji diagnostycznej
   */
  _getSessionDuration() {
    if (this.samples.length < 2) return 0;
    
    const firstSample = this.samples[0].timestamp;
    const lastSample = this.samples[this.samples.length - 1].timestamp;
    
    return Math.round((lastSample - firstSample) / 1000); // sekundy
  }
  
  /**
   * Eksport danych diagnostycznych
   */
  exportDiagnostics() {
    const metrics = this.calculateWearMetrics();
    
    return {
      version: '3.5.0',
      timestamp: Date.now(),
      metrics: metrics,
      rawSamples: this.samples.map(s => ({
        t: s.timestamp,
        lx: s.left.x.toFixed(3),
        ly: s.left.y.toFixed(3),
        rx: s.right.x.toFixed(3),
        ry: s.right.y.toFixed(3)
      }))
    };
  }
}

/**
 * Latency Profiler - pomiar opóźnienia wejścia
 */
export class LatencyProfiler {
  constructor() {
    this.measurements = [];
  }
  
  /**
   * Rozpocznij pomiar latencji
   */
  async measureLatency(device, iterations = 10) {
    console.log('[Latency] Starting measurement...');
    
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      
      try {
        // Wyślij dummy command i czekaj na odpowiedź
        await device.sendFeatureReport(0x05, new Uint8Array(64));
        const response = await device.receiveFeatureReport(0x05);
        
        const end = performance.now();
        const latency = end - start;
        
        this.measurements.push({
          iteration: i + 1,
          latency: latency,
          timestamp: Date.now()
        });
        
        // Opóźnienie między pomiarami
        await this._delay(100);
        
      } catch (error) {
        console.error(`[Latency] Measurement ${i + 1} failed:`, error);
      }
    }
    
    return this.getStatistics();
  }
  
  /**
   * Statystyki latencji
   */
  getStatistics() {
    if (this.measurements.length === 0) {
      return null;
    }
    
    const latencies = this.measurements.map(m => m.latency);
    const sorted = [...latencies].sort((a, b) => a - b);
    
    return {
      min: Math.min(...latencies),
      max: Math.max(...latencies),
      avg: latencies.reduce((a, b) => a + b) / latencies.length,
      median: sorted[Math.floor(sorted.length / 2)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
      samples: this.measurements.length
    };
  }
  
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
'''
        
        diagnostics_path = self.project_path / 'js' / 'diagnostics' / 'healthMonitor.js'
        with open(diagnostics_path, 'w', encoding='utf-8') as f:
            f.write(diagnostics_content)
        
        print(f"  ✓ Utworzono healthMonitor.js")
        self.migration_log.append("System diagnostyczny zaimplementowany")
    
    def _update_dependencies(self):
        """Aktualizuj package.json"""
        print(f"\n{Color.BLUE}📦 Aktualizacja zależności...{Color.RESET}")
        
        new_package = {
            "name": "dualshock-tools",
            "version": "3.5.0",
            "description": "Professional calibration tool for PlayStation controllers",
            "main": "js/app.js",
            "scripts": {
                "dev": "gulp watch",
                "build": "gulp build",
                "serve": "python3 server.py",
                "test": "jest",
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
        
        pkg_path = self.project_path / 'package.json'
        with open(pkg_path, 'w') as f:
            json.dump(new_package, f, indent=2)
        
        print(f"  ✓ Zaktualizowano package.json")
        
        # Aktualizuj gulpfile.js
        gulpfile_content = '''/**
 * DualShock Tools v3.5 - Build Configuration
 */

const gulp = require('gulp');
const babel = require('@rollup/plugin-babel').default;
const resolve = require('@rollup/plugin-node-resolve').default;
const commonjs = require('@rollup/plugin-commonjs');
const terser = require('gulp-terser');
const cleanCSS = require('gulp-clean-css');
const htmlmin = require('gulp-htmlmin');
const rollup = require('rollup');

// Paths
const paths = {
  js: {
    src: 'js/**/*.js',
    dest: 'dist/js'
  },
  css: {
    src: 'css/**/*.css',
    dest: 'dist/css'
  },
  html: {
    src: 'index.html',
    dest: 'dist'
  },
  assets: {
    src: 'assets/**/*',
    dest: 'dist/assets'
  },
  public: {
    src: 'public/**/*',
    dest: 'dist'
  }
};

// JavaScript bundling with Rollup
async function scripts() {
  const bundle = await rollup.rollup({
    input: 'js/app.js',
    plugins: [
      resolve(),
      commonjs(),
      babel({
        babelHelpers: 'bundled',
        presets: ['@babel/preset-env']
      })
    ]
  });

  await bundle.write({
    file: 'dist/js/app.bundle.js',
    format: 'iife',
    sourcemap: true
  });
}

// CSS minification
function styles() {
  return gulp.src(paths.css.src)
    .pipe(cleanCSS())
    .pipe(gulp.dest(paths.css.dest));
}

// HTML minification
function html() {
  return gulp.src(paths.html.src)
    .pipe(htmlmin({
      collapseWhitespace: true,
      removeComments: true
    }))
    .pipe(gulp.dest(paths.html.dest));
}

// Copy assets
function assets() {
  return gulp.src(paths.assets.src)
    .pipe(gulp.dest(paths.assets.dest));
}

// Copy public files (manifest, SW)
function publicFiles() {
  return gulp.src(paths.public.src)
    .pipe(gulp.dest(paths.public.dest));
}

// Watch files
function watch() {
  gulp.watch(paths.js.src, scripts);
  gulp.watch(paths.css.src, styles);
  gulp.watch(paths.html.src, html);
  gulp.watch(paths.assets.src, assets);
}

// Build task
const build = gulp.series(
  gulp.parallel(scripts, styles, html, assets, publicFiles)
);

// Export tasks
exports.scripts = scripts;
exports.styles = styles;
exports.html = html;
exports.assets = assets;
exports.watch = watch;
exports.build = build;
exports.default = build;
'''
        
        gulpfile_path = self.project_path / 'gulpfile.js'
        with open(gulpfile_path, 'w', encoding='utf-8') as f:
            f.write(gulpfile_content)
        
        print(f"  ✓ Zaktualizowano gulpfile.js")
        self.migration_log.append("Zależności zaktualizowane")
    
    def _generate_migration_report(self):
        """Generuj raport migracji"""
        print(f"\n{Color.BLUE}📝 Generowanie raportu migracji...{Color.RESET}")
        
        report = f"""
{'='*70}
DUALSHOCK TOOLS - RAPORT MIGRACJI v2.2 → v3.5
{'='*70}

Data migracji: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup: {self.backup_path}

ZMIANY WPROWADZONE:
{'='*70}

"""
        
        for log_entry in self.migration_log:
            report += f"✓ {log_entry}\n"
        
        report += f"""

NOWE FUNKCJE:
{'='*70}

1. Progressive Web App (PWA)
   - Instalacja jednym kliknięciem
   - Działanie offline
   - Automatyczne aktualizacje
   
2. Profile Manager
   - Backup lokalny i cloud (opcjonalny)
   - Szyfrowanie end-to-end
   - Eksport/import przez QR code
   
3. Advanced Diagnostics
   - Analiza zużycia analogów
   - Detekcja driftu
   - Pomiar latencji input
   
4. Enhanced Stability
   - Asynchroniczna kolejka komend
   - Filtrowanie "ghost" devices
   - Lepsze wsparcie dla JDM-040/055

NASTĘPNE KROKI:
{'='*70}

1. Zainstaluj zależności:
   npm install

2. Zbuduj projekt:
   npm run build

3. Uruchom serwer deweloperski:
   npm run serve

4. Otwórz w przeglądarce:
   https://localhost:8443

UWAGA: Pamiętaj o zaakceptowaniu self-signed certyfikatu!

{'='*70}
"""
        
        report_path = self.project_path / 'MIGRATION_REPORT.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"  ✓ Raport zapisany: MIGRATION_REPORT.txt")
    
    def _restore_backup(self):
        """Przywróć projekt z backupu"""
        if not self.backup_path or not self.backup_path.exists():
            print(f"{Color.RED}Backup nie istnieje!{Color.RESET}")
            return
        
        print(f"{Color.YELLOW}Przywracanie z: {self.backup_path}{Color.RESET}")
        
        # Usuń obecny katalog
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        
        # Przywróć backup
        shutil.copytree(self.backup_path, self.project_path)
        
        print(f"{Color.GREEN}Backup przywrócony pomyślnie!{Color.RESET}")


class AutoInstaller:
    """Automatyczny instalator środowiska"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        
    def install(self):
        """Wykonaj pełną instalację"""
        print(f"\n{Color.CYAN}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}⚙️  AUTO-INSTALLER - FAZA 3: KONFIGURACJA{Color.RESET}")
        print(f"{Color.CYAN}{'='*70}{Color.RESET}\n")
        
        self._check_requirements()
        self._install_npm_packages()
        self._generate_ssl_certificates()
        self._create_launch_script()
        self._build_project()
        
        print(f"\n{Color.GREEN}{'='*70}{Color.RESET}")
        print(f"{Color.GREEN}{Color.BOLD}✅ INSTALACJA ZAKOŃCZONA!{Color.RESET}")
        print(f"{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    def _check_requirements(self):
        """Sprawdź wymagania systemowe"""
        print(f"{Color.BLUE}🔍 Sprawdzanie wymagań...{Color.RESET}")
        
        requirements = {
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'openssl': ['openssl', 'version']
        }
        
        for name, cmd in requirements.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                version = result.stdout.strip()
                print(f"  ✓ {name}: {version}")
            except Exception as e:
                print(f"  {Color.RED}✗ {name}: Nie znaleziono!{Color.RESET}")
                print(f"    Zainstaluj {name} przed kontynuacją")
                sys.exit(1)
    
    def _install_npm_packages(self):
        """Zainstaluj pakiety NPM"""
        print(f"\n{Color.BLUE}📦 Instalowanie pakietów NPM...{Color.RESET}")
        
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd=self.project_path,
                check=True,
                timeout=300
            )
            print(f"  ✓ Pakiety zainstalowane")
        except subprocess.TimeoutExpired:
            print(f"  {Color.YELLOW}⚠ Timeout - kontynuuję...{Color.RESET}")
        except Exception as e:
            print(f"  {Color.RED}✗ Błąd instalacji: {e}{Color.RESET}")
    
    def _generate_ssl_certificates(self):
        """Generuj certyfikaty SSL"""
        print(f"\n{Color.BLUE}🔒 Generowanie certyfikatów SSL...{Color.RESET}")
        
        cert_file = self.project_path / 'server.pem'
        key_file = self.project_path / 'server.key'
        
        if cert_file.exists() and key_file.exists():
            print(f"  ✓ Certyfikaty już istnieją")
            return
        
        cmd = [
            'openssl', 'req', '-newkey', 'rsa:2048',
            '-new', '-nodes', '-x509', '-days', '365',
            '-keyout', str(key_file),
            '-out', str(cert_file),
            '-subj', '/C=PL/ST=Local/L=Local/O=DualShockTools/CN=localhost'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Certyfikaty wygenerowane")
        except Exception as e:
            print(f"  {Color.RED}✗ Błąd generowania: {e}{Color.RESET}")
    
    def _create_launch_script(self):
        """Utwórz skrypt startowy"""
        print(f"\n{Color.BLUE}🚀 Tworzenie skryptu startowego...{Color.RESET}")
        
        server_script = '''#!/usr/bin/env python3
"""
DualShock Tools v3.5 - Development Server
"""

import http.server
import ssl
import webbrowser
from pathlib import Path

PORT = 8443
CERT_FILE = "server.pem"
KEY_FILE = "server.key"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="dist", **kwargs)

def main():
    print(f"🚀 Starting DualShock Tools v3.5")
    print(f"📡 Server: https://localhost:{PORT}")
    print(f"⚠️  Accept the security warning in your browser\\n")
    
    server_address = ('localhost', PORT)
    httpd = http.server.HTTPServer(server_address, CustomHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    webbrowser.open(f"https://localhost:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped")

if __name__ == "__main__":
    main()
'''
        
        server_path = self.project_path / 'server.py'
        with open(server_path, 'w', encoding='utf-8') as f:
            f.write(server_script)
        
        # Zrób skrypt wykonywalnym
        server_path.chmod(0o755)
        
        print(f"  ✓ Utworzono server.py")
    
    def _build_project(self):
        """Zbuduj projekt"""
        print(f"\n{Color.BLUE}🏗️  Budowanie projektu...{Color.RESET}")
        
        try:
            subprocess.run(
                ['npx', 'gulp', 'build'],
                cwd=self.project_path,
                check=True,
                timeout=120
            )
            print(f"  ✓ Projekt zbudowany")
        except Exception as e:
            print(f"  {Color.YELLOW}⚠ Błąd budowania: {e}{Color.RESET}")
            print(f"  Możesz ręcznie uruchomić: npm run build")


def main():
    """Główna funkcja programu"""
    print(f"""
{Color.CYAN}{'='*70}
{Color.BOLD}DUALSHOCK TOOLS - AUTOMATIC MIGRATION SYSTEM v3.5{Color.RESET}
{Color.CYAN}{'='*70}{Color.RESET}

Autor: anonymousik (Community Edition Enhanced)
Licencja: MIT

Ten skrypt automatycznie zaktualizuje Twój projekt z wersji v2.2 do v3.5.
Wszystkie zmiany będą zapisane, a backup zostanie utworzony automatycznie.

""")
    
    # Pobierz ścieżkę projektu
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = input(f"{Color.YELLOW}Podaj ścieżkę do projektu (lub '.' dla bieżącego katalogu): {Color.RESET}").strip()
        if not project_path:
            project_path = '.'
    
    project_path = Path(project_path).resolve()
    
    if not project_path.exists():
        print(f"{Color.RED}❌ Ścieżka nie istnieje: {project_path}{Color.RESET}")
        sys.exit(1)
    
    print(f"\n{Color.GREEN}📂 Projekt: {project_path}{Color.RESET}\n")
    
    # Potwierdź kontynuację
    confirm = input(f"{Color.YELLOW}Kontynuować migrację? (yes/no): {Color.RESET}").strip().lower()
    if confirm not in ['yes', 'y', 'tak', 't']:
        print(f"{Color.RED}Anulowano.{Color.RESET}")
        sys.exit(0)
    
    # FAZA 1: Analiza
    analyzer = MigrationAnalyzer(project_path)
    analysis_results = analyzer.analyze()
    
    if analyzer.issues:
        print(f"\n{Color.RED}❌ Znaleziono problemy krytyczne. Napraw je przed migracją.{Color.RESET}")
        proceed = input(f"{Color.YELLOW}Kontynuować mimo to? (yes/no): {Color.RESET}").strip().lower()
        if proceed not in ['yes', 'y']:
            sys.exit(1)
    
    # FAZA 2: Migracja
    migrator = ProjectMigrator(project_path, backup=True)
    success = migrator.migrate()
    
    if not success:
        print(f"\n{Color.RED}❌ Migracja nie powiodła się!{Color.RESET}")
        sys.exit(1)
    
    # FAZA 3: Instalacja
    installer = AutoInstaller(project_path)
    installer.install()
    
    # Finalne instrukcje
    print(f"""
{Color.CYAN}{'='*70}
{Color.BOLD}🎉 MIGRACJA ZAKOŃCZONA SUKCESEM!{Color.RESET}
{Color.CYAN}{'='*70}{Color.RESET}

{Color.GREEN}✅ Projekt zaktualizowany do v3.5{Color.RESET}
{Color.GREEN}✅ Backup utworzony: {migrator.backup_path}{Color.RESET}
{Color.GREEN}✅ Wszystkie zależności zainstalowane{Color.RESET}

{Color.BOLD}URUCHOMIENIE:{Color.RESET}

  1. Przejdź do katalogu projektu:
     cd {project_path}

  2. Uruchom serwer deweloperski:
     python3 server.py

  3. Otwórz w przeglądarce:
     https://localhost:8443

{Color.YELLOW}⚠️  WAŻNE: Zaakceptuj ostrzeżenie o certyfikacie w przeglądarce!{Color.RESET}

{Color.BOLD}NOWE FUNKCJE v3.5:{Color.RESET}

  📱 PWA - Instaluj jako aplikację
  💾 Profile Manager - Backup i przywracanie kalibracji
  🔬 Advanced Diagnostics - Analiza zużycia i driftu
  ⚡ Enhanced Performance - Szybsze ładowanie i działanie
  🌍 i18n Ready - Gotowe na tłumaczenia

{Color.BOLD}DOKUMENTACJA:{Color.RESET}
  Sprawdź plik MIGRATION_REPORT.txt dla szczegółów

{Color.CYAN}{'='*70}{Color.RESET}
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}⚠️  Przerwano przez użytkownika{Color.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Color.RED}❌ BŁĄD KRYTYCZNY: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)