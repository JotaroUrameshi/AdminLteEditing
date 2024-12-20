import sqlite3

# Connexion à la base de données (ou création si elle n'existe pas)
conn = sqlite3.connect('clients.db')

# Création du curseur pour exécuter des commandes SQL
cursor = conn.cursor()

# Création de la table "clients"
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL
)
''')

# Ajout de données de test
cursor.executemany('''
INSERT INTO clients (name, email, phone)
VALUES (?, ?, ?)
''', [
    ('John Doe', 'john.doe@example.com', '+123456789'),
    ('Jane Smith', 'jane.smith@example.com', '+987654321')
])

# Sauvegarder et fermer
conn.commit()
conn.close()

print("Base de données et table configurées avec succès.")
