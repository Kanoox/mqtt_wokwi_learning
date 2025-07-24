# MQTT Learning

Ce projet permet de recevoir des données de température via MQTT, de les stocker dans une base de données SQLite et de les visualiser via un tableau de bord Python.

## Niveau 3 - Système d’arrosage automatique

Ce niveau consiste à réaliser un système d’arrosage automatique avec Wokwi.

- **Matériel simulé** : ESP32 + servo moteur (pour la vanne d’arrosage)
- **Fonctionnement** :
  - Le servo moteur a deux positions : ouverte (arrosage activé) et fermée (arrosage désactivé).
  - L’arrosage peut être déclenché :
    - Manuellement, en envoyant un message MQTT depuis votre système.
    - Automatiquement, si la moyenne des valeurs des capteurs d’humidité passe sous un seuil défini.
- **Communication** :
  - Le système reçoit les ordres d’arrosage via MQTT.
  - Les capteurs d’humidité envoient leurs valeurs via MQTT (voir simulation Wokwi).

**Simulation Wokwi** :  
Utilisez Wokwi pour simuler l’ESP32, le servo moteur et les capteurs d’humidité.  
Le code Python permet d’envoyer les commandes MQTT pour piloter l’arrosage.

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