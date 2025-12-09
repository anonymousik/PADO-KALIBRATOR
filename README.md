
 DualShock Tools v3.0 (Community Edition by anonymousik).


1. CHANGELOG v3.0 – Release Notes
Autor wersji: anonymousik
Status: Stable / Major Release

🚀 Nowości (New Features)
 * Software Trigger Remapping (L2/R2): Dodano programową kalibrację triggerów. Pozwala to na mapowanie niepełnego zakresu (np. 0.00-0.88) na pełną skalę (0.00-1.00) w warstwie aplikacji, rozwiązując problem zużytych potencjometrów.
 * Persistent Settings (Issue #125): Zaimplementowano localStorage dla ustawień "Joystick Info". Wybrane tryby wizualizacji są zapamiętywane po odświeżeniu strony.
 * DualSense "Ghost" Filter: Nowy algorytm filtrowania urządzeń HID. Eliminuje widoczność podwójnych kontrolerów ("PS5 Controller" vs "DualSense Wireless Controller"), ukrywając wirtualne urządzenia systemowe, które powodowały błędy połączenia.
 * Universal Clone Support: Wprowadzono "Permissive Mode". Narzędzie nie blokuje już kalibracji po wykryciu potencjalnego klona (błąd 0x81 feature report), lecz wyświetla ostrzeżenie i pozwala kontynuować.
🐛 Poprawki (Bug Fixes)
 * FIX #174 (JDM-020/055 Detection): Naprawiono logikę detekcji oryginalności. Płyty JDM-055 i JDM-040 nie są już błędnie oznaczane jako klony.
 * FIX Timing Issues: Wprowadzono asynchroniczną kolejkę komend (AsyncCommandQueue) z opóźnieniami (50ms) dla operacji zapisu/odczytu, naprawiając błędy timeoutów na starszych rewizjach płyt (JDM-040).
 * FIX WebHID HTTPS Requirement: Skrypty deweloperskie teraz automatycznie generują i obsługują certyfikaty SSL, co jest wymagane przez przeglądarki do działania WebHID.
⚡ Optymalizacje
 * Gulp + Rollup: Zaktualizowano system budowania. app.js jest teraz dzielony na mniejsze chunki (code splitting), co przyspiesza ładowanie aplikacji.
 * SVG Assets: Zoptymalizowano wektory w folderze assets/ zmniejszając rozmiar paczki o 40%.

2. Automatyczny Instalator Lokalny (Auto-Installer)
Z uwagi na wymóg HTTPS przez WebHID API, zwykłe otwarcie pliku .html nie zadziała. 

SKRYPT (setup_and_run.py) WYKONUJĘ AUTOMATYCZNIE UZUPEŁNIENIE NIEZBĘDNYCH ZALEŻNOŚCI W SYSTEMIE

Wymagania: Python 3.x, Node.js, OpenSSL
 (zazwyczaj obecne w systemie lub Git Bash).


Instrukcja użycia instalatora:
 * Upewnij się, że masz zainstalowany Node.js.
 * Umieść plik setup_and_run.py w folderze z projektem.
 * Uruchom terminal i wpisz: python setup_and_run.py.
 * Skrypt wykona wszystko automatycznie i otworzy przeglądarkę.
3. Dokumentacja Techniczna Elementów
A. Struktura Projektu (Project Structure)
/
├── assets/           # Pliki wektorowe SVG (ikony kontrolerów, diagramy)
├── css/              # Źródłowe pliki stylów (SCSS/CSS)
│   └── main.css      # Główny arkusz stylów
├── js/               # Logika aplikacji
│   ├── controllers/  # Logika specyficzna dla urządzeń
│   │   ├── ds4.js    # Klasa obsługi DualShock 4
│   │   └── ds5.js    # Klasa obsługi DualSense (zaktualizowana o filtry)
│   ├── ui/           # Obsługa interfejsu (wykresy, modale)
│   ├── app.js        # Główny punkt wejścia (Entry Point)
│   └── utils.js      # Narzędzia (HexDump, CRC32)
├── lang/             # Pliki tłumaczeń (i18n) - JSON
├── templates/        # Fragmenty HTML ładowane dynamicznie
├── dist/             # WYNIK KOMPILACJI (to serwuje serwer)
├── gulpfile.js       # Konfiguracja task runnera
└── package.json      # Zależności NPM

B. System Budowania (Build System)
Narzędzie wykorzystuje Gulp 4.0 do orkiestracji zadań:
 * HTML Minification: Pliki z templates/ są wstrzykiwane do index.html i minifikowane.
 * JS Bundling (Rollup): Moduły ES6 w folderze js/ są łączone w jeden plik (lub chunki), transpilowane przez Babel (dla kompatybilności) i minifikowane przez Terser.
 * CSS Processing: Łączenie plików CSS i usuwanie zbędnych spacji.
 * Watch Mode: Komenda npx gulp watch śledzi zmiany w plikach i automatycznie przebudowuje projekt w czasie rzeczywistym.
C. Nowe Moduły w Kodzie (v3.0 Specifics)
1. Moduł Filtrowania (js/utils/deviceFilter.js)
Odpowiada za selekcję właściwego urządzenia HID.
 * Funkcja: filterValidInterface(devices)
 * Logika: Sprawdza usagePage. Jeśli wynosi 0xFF00 (Vendor Specific), urządzenie jest akceptowane. Jeśli 0x01 (Generic Desktop), urządzenie jest odrzucane jako "Ghost".
2. Kolejka Komend (js/utils/asyncQueue.js)
Odpowiada za stabilność komunikacji z kontrolerem.
 * Cel: Zapobieganie "zalewaniu" kontrolera komendami, co powodowało błędy w JDM-040.
 * Działanie: Każda komenda sendFeatureReport jest dodawana do Promise Chain i czeka na zakończenie poprzedniej + 50ms marginesu bezpieczeństwa.
4. Instrukcja Obsługi (User Manual)
Wymagania wstępne
 * Przeglądarka oparta na Chromium (Chrome, Edge, Opera, Brave). Firefox nie obsługuje WebHID.
 * Połączenie kontrolera kablem USB (Bluetooth nie obsługuje pełnej kalibracji w trybie WebHID na Windows).
Krok 1: Łączenie kontrolera
 * Podłącz kontroler kablem USB.
 * Kliknij przycisk "Connect" na stronie.
 * WAŻNE (Zmiana w v3.0): W oknie wyboru urządzenia powinieneś teraz widzieć tylko jedną pozycję (np. "DualSense Wireless Controller") zamiast dwóch. Wybierz ją i kliknij "Połącz".
Krok 2: Diagnostyka i Klonowanie
 * Narzędzie automatycznie spróbuje zweryfikować oryginalność.
 * Zielony komunikat: Oryginał.
 * Żółty komunikat (Nowość): "Verification Inconclusive" – narzędzie nie mogło potwierdzić oryginalności, ale odblokowało dostęp do kalibracji (tryb Permissive dla klonów/rzadkich rewizji).
 * Czerwony komunikat: Krytyczny błąd komunikacji.
Krok 3: Kalibracja Analogów
 * Przejdź do zakładki "Calibration".
 * Kliknij "Start Calibration".
 * Obracaj obydwoma gałkami w pełnym zakresie (twórz okręgi) przez 10 sekund.
 * Kliknij "Save to Controller". Dane zostaną trwale zapisane w pamięci Flash kontrolera (działa na PC i konsolach).
Krok 4: Kalibracja Triggerów (Nowość v3.0)
Funkcja dostępna w sekcji "Advanced Tools".
 * Jeśli Twoje triggery (L2/R2) nie osiągają wartości 1.0 (np. dochodzą tylko do 0.88):
 * Wciśnij L2 do oporu i kliknij "Set Max L2".
 * Wciśnij R2 do oporu i kliknij "Set Max R2".
 * Włącz przełącznik "Enable Software Remapping".
   Uwaga: Ta kalibracja działa tylko w przeglądarce/nakładce wykorzystującej ten skrypt, nie zapisuje się w pamięci kontrolera dla konsoli PS5.
Rozwiązywanie problemów
 * Błąd "Security Error" / HTTPS: Uruchom skrypt setup_and_run.py ponownie. WebHID wymaga bezpiecznego połączenia.
 * Brak urządzenia na liście: Sprawdź kabel USB (musi przesyłać dane, nie tylko ładować).
 * "Calibration Failed" na JDM-040: Odłącz kontroler, odczekaj 5 sekund, podłącz ponownie i spróbuj od razu, nie czekając.
