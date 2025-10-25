"""
═══════════════════════════════════════════════════════════════
PDF CONVERTER - Excel zu PDF
═══════════════════════════════════════════════════════════════
"""

import subprocess
import platform
from pathlib import Path


def convert_excel_to_pdf(excel_path: str, pdf_path: str) -> bool:
    """
    Konvertiert Excel zu PDF
    
    Versucht verschiedene Methoden:
    1. LibreOffice (macOS/Linux)
    2. Microsoft Excel (macOS mit Excel installiert)
    3. Fallback: Kopiert Excel (besser als nichts)
    """
    
    excel_file = Path(excel_path)
    pdf_file = Path(pdf_path)
    
    # Method 1: LibreOffice (empfohlen)
    try:
        if platform.system() == 'Darwin':  # macOS
            libreoffice_paths = [
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                '/usr/local/bin/soffice',
            ]
            
            for lo_path in libreoffice_paths:
                if Path(lo_path).exists():
                    subprocess.run([
                        lo_path,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', str(pdf_file.parent),
                        str(excel_file)
                    ], check=True, capture_output=True)
                    
                    # Rename output file if needed
                    default_output = pdf_file.parent / f"{excel_file.stem}.pdf"
                    if default_output != pdf_file and default_output.exists():
                        default_output.rename(pdf_file)
                    
                    return True
        
        elif platform.system() == 'Linux':
            subprocess.run([
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(pdf_file.parent),
                str(excel_file)
            ], check=True, capture_output=True)
            
            default_output = pdf_file.parent / f"{excel_file.stem}.pdf"
            if default_output != pdf_file and default_output.exists():
                default_output.rename(pdf_file)
            
            return True
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Method 2: AppleScript + Excel (macOS)
    if platform.system() == 'Darwin':
        try:
            applescript = f'''
            tell application "Microsoft Excel"
                open "{excel_file}"
                set activeWorkbook to active workbook
                save activeWorkbook in "{pdf_file}" as PDF file format
                close activeWorkbook
            end tell
            '''
            
            subprocess.run(['osascript', '-e', applescript], check=True, capture_output=True)
            return True
        except:
            pass
    
    # Method 3: Fallback - Create placeholder PDF
    print(f"⚠️  PDF-Konvertierung fehlgeschlagen. Bitte Excel manuell als PDF speichern:")
    print(f"   {excel_path}")
    print(f"\nInstalliere LibreOffice für automatische Konvertierung:")
    print(f"   brew install --cask libreoffice")
    
    # Create a simple text file as placeholder
    with open(pdf_path, 'w') as f:
        f.write(f"PDF konnte nicht automatisch erstellt werden.\n")
        f.write(f"Bitte Excel-Datei manuell öffnen und als PDF speichern:\n")
        f.write(f"{excel_path}\n")
    
    return False


def install_libreoffice_instructions():
    """
    Zeigt Installations-Anweisungen für LibreOffice
    """
    if platform.system() == 'Darwin':
        return """
        LibreOffice für automatische PDF-Konvertierung installieren:
        
        Option 1 - Homebrew (empfohlen):
            brew install --cask libreoffice
        
        Option 2 - Manuell:
            https://www.libreoffice.org/download/
        """
    elif platform.system() == 'Linux':
        return """
        LibreOffice installieren:
        
        Ubuntu/Debian:
            sudo apt-get install libreoffice
        
        Fedora:
            sudo dnf install libreoffice
        """
    else:
        return "LibreOffice von https://www.libreoffice.org/ herunterladen"
