# MQTT Learning

Ce projet permet de recevoir des données de température via MQTT, de les stocker dans une base de données SQLite et de les visualiser via un tableau de bord Python.

## Fonctionnalités
- Connexion à un broker MQTT
- Réception de données capteurs (température & humidité)
- Stockage dans une base SQLite
- Visualisation via un dashboard Streamlit
- Carte interactive avec position GPS des capteurs
- **Gestion de plusieurs arroseurs indépendants**, chacun associé à un capteur d'humidité
- **Arrosage automatique** si l’humidité mesurée est sous un seuil défini
- **Contrôle manuel** des arroseurs via interface graphique

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
   - Accédez à la simulation Wokwi : [Simulation ESP32 double DHT sur Wokwi](https://wokwi.com/projects/437457486740084737)
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
- Pour nettoyer la base de données (suppression des capteurs inactifs ou sans mesures) :
  ```bash
  python cleanup.py
  ```

## Fichiers principaux
- `main.py` : réception et stockage des données MQTT
- `dashboard.py` : visualisation des données
- `cleanup.py` : script de nettoyage de la base de données (suppression des capteurs inactifs ou sans mesures)
- `requirements.txt` : dépendances Python
- `.env`: Fichier d'environnement pour stocker des valeurs secrètes.

## Auteur
Florentin Binet

## Licence
Ce projet est sous licence MIT. 