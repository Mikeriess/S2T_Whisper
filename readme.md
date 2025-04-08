# Audio Batch Transskriberingsværktøj

Dette (work-in-progress) værktøj giver dig mulighed for at transskribere lydfiler i batch ved hjælp af Whisper-modeller som eks. Syv.ai's Hviske. Det understøtter flere outputformater og kan behandle flere filer parallelt.

## Forudsætninger

- Anaconda (anbefales til styring af environments)
- Python 3.8 eller højere
- FFmpeg (til konvertering af lydfiler)

## Installation

### Windows
1. Download og installer [Anaconda](https://www.anaconda.com/download) til Windows
2. Åbn Anaconda Prompt
3. Opret et nyt environments:
   ```bash
   conda create -n transcription python=3.8
   conda activate transcription
   ```
4. Installer afhængigheder:
   ```bash
   pip install -r requirements.txt
   ```

### macOS
1. Download og installer [Anaconda](https://www.anaconda.com/download) til macOS
2. Åbn Terminal
3. Opret et nyt environments:
   ```bash
   conda create -n transcription python=3.8
   conda activate transcription
   ```
4. Installer afhængigheder:
   ```bash
   pip install -r requirements.txt
   ```

## Konfiguration

Værktøjet bruger en `settings.json` fil til konfiguration. Her er de tilgængelige indstillinger:

- `model`: Whisper-modellen der skal bruges (standard: "syvai/hviske-v2")
- `language`: Sprogkoden til transskription (standard: "da")
- `output_format`: Liste over outputformater (["json", "txt"])
- `output_dir`: Mappe til outputfiler (standard: "output")
- `input_dir`: Mappe indeholdende input-lydfiler (standard: "input")
- `batch_size`: Antal filer der skal behandles parallelt (standard: 10)
- `verbose`: Aktiver detaljeret output (standard: true)

## Brug

1. Placer dine lydfiler i `input` mappen
2. Kør transskriptionen:
   ```bash
   python transcribe.py
   ```
3. Find dine transskriberede filer i `output` mappen

## Outputformater

Værktøjet genererer følgende outputformater:
- TXT: Ren tekst transskription
- JSON: Struktureret transskriptionsdata

## Fejlfinding

Hvis du støder på problemer:
1. Sikr dig at alle afhængigheder er installeret korrekt
2. Kontroller at dine lydfiler er i et understøttet format (WAV, MP3, M4A, FLAC)
3. Verificer settings.json konfiguration 
4. Kontroller at FFmpeg er installeret korrekt på dit system

Eller opret et issue i dette repo ^^