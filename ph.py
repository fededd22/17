# ✅ Installer automatiquement pyngrok
!pip install pyngrok --quiet

# ✅ Lancer un serveur HTTP (remplaçant proxy) sur le port 8080
import os
from pyngrok import ngrok
import threading

def run_proxy():
    os.system("python3 -m http.server 8080 --bind 0.0.0.0")

threading.Thread(target=run_proxy).start()

# ✅ Créer un tunnel public avec ngrok (port 8080)
public_url = ngrok.connect(8080)
print("🌐 Proxy HTTP public accessible ici :", public_url)
