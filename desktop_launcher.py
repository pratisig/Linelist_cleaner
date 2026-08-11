"""
Desktop Entrypoint for Windows Executable (.exe).
Launches the FastAPI server and automatically opens the user's default web browser.
PratiSIG Consulting Services - Dakar, Sénégal.
"""

import sys
import os
import time
import socket
import threading
import webbrowser
import uvicorn

# Ensure package directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from linelist_cleaner.web.app import app


def find_available_port(starting_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds an open TCP port starting from starting_port."""
    for port in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return starting_port


def open_browser_delayed(url: str, delay: float = 1.2):
    """Opens default browser after a short delay allowing server to start."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[*] Note: Veuillez ouvrir manuellement votre navigateur a l'adresse : {url}")


def main():
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    banner = f"""
===================================================================
   PRATISIG CONSULTING SERVICES - DAKAR, SENEGAL
   La pratique des SIG, notre metier
-------------------------------------------------------------------
   LINELIST CLEANER & GEOCODAGE EN CASCADE (P-CODES OCHA)
   Auteur  : Youssoupha MBODJI
   Contact : pratisig.consulting@gmail.com
===================================================================
   [+] Application prete pour une utilisation hors-ligne (Desktop).
   [+] L'interface web s'ouvre automatiquement a l'adresse :
       -> {url}

   [!] Laissez cette fenetre ouverte pendant l'utilisation.
   [!] Pour quitter, fermez simplement cette fenetre ou faites Ctrl+C.
===================================================================
"""
    print(banner)

    # Launch browser opener in background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    # Start Uvicorn web server
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False
        )
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Arret de Linelist Cleaner. A bientot !")


if __name__ == "__main__":
    main()
