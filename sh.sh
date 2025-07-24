#!/bin/bash

# Installer pyngrok
pip install pyngrok --quiet

# Créer un script Python temporaire et l’exécuter
cat <<EOF > ngrok_start.py
import os
import threading
from pyngrok import ngrok

def run_proxy():
    os.system("python3 -m http.server 8080 --bind 0.0.0.0")

threading.Thread(target=run_proxy).start()

public_url = ngrok.connect(8080)
print("🌐 Proxy public accessible ici :", public_url)
EOF

# Lancer le script Python
python3 ngrok_start.py
