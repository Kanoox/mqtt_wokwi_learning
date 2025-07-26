import sqlite3

conn = sqlite3.connect("capteur_multi.db")
cur = conn.cursor()

# Supprimer capteurs sans aucune mesure
cur.execute("""
DELETE FROM sensors
WHERE id NOT IN (
    SELECT DISTINCT sensor_id FROM measurements
)
""")

# Supprimer capteurs inactifs depuis 30 minutes
cur.execute("""
DELETE FROM sensors
WHERE id IN (
    SELECT s.id FROM sensors s
    LEFT JOIN (
        SELECT sensor_id, MAX(timestamp) AS last_seen
        FROM measurements
        GROUP BY sensor_id
    ) AS latest ON s.id = latest.sensor_id
    WHERE datetime(latest.last_seen) < datetime('now', '-30 minutes')
)
""")

conn.commit()
conn.close()
print("✅ Nettoyage terminé")
