# MQTT Learning

Ce projet permet de recevoir des données de température via MQTT, de les stocker dans une base de données SQLite et de les visualiser via un tableau de bord Python.

## Fonctionnalités
- Connexion à un broker MQTT
- Réception de messages de température
- Stockage des données dans une base SQLite
- Visualisation des données via un dashboard Python

## Installation
1. Clonez le dépôt :
   ```bash
   git clone https://github.com/Kanoox/mqtt_wokwi_learning
   cd mqtt_learning
   ```
2. Créez un environnement virtuel (optionnel mais recommandé) :
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Créez un fichier `.env` à la racine du projet pour stocker les informations sensibles (non versionnées) :
   ```env
   MQTT_BROKER=adresseip
   MQTT_PORT=port
   ```

5. (Optionnel) Pour simuler des capteurs et tester l'envoi de données MQTT, utilisez le projet Wokwi suivant :
   - Accédez à la simulation Wokwi : [Simulation ESP32 double DHT sur Wokwi](https://wokwi.com/projects/437364276739113985)
   - Cliquez sur "Start Simulation" pour lancer l'envoi de données vers le broker MQTT.
   - Les données publiées sur le topic `wokwi/sensor/temperature` et `wokwi/sensor/humidity` seront automatiquement reçues par ce projet Python.

## Utilisation
- Pour lancer la collecte des données MQTT :
  ```bash
  python main.py
  ```
- Pour lancer le dashboard (visualisation) :
  ```bash
  python dashboard.py
  ```

## Fichiers principaux
- `main.py` : réception et stockage des données MQTT
- `dashboard.py` : visualisation des données
- `requirements.txt` : dépendances Python
- `.env`: Fichier d'environnement pour stocker des valeurs secrètes.

## Auteur
Florentin Binet

## Licence
Ce projet est sous licence MIT. 