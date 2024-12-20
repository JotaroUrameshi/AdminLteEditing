from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import pandas as pd

app = Flask(__name__)

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Configuration du dossier pour les uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modèle pour la table "clients"
class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    aerial_view = db.Column(db.String(200), nullable=True)  # Chemin vers la photo

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "aerial_view": self.aerial_view
        }

# Création automatique des tables
with app.app_context():
    db.create_all()

# Route pour l'URL racine
@app.route('/', methods=['GET'])
def home():
    return render_template('index2.html')

# Route pour afficher la page de gestion des clients
@app.route('/clients', methods=['GET'])
def clients_view():
    clients = Client.query.all()
    return render_template('clients.html', clients=[client.to_dict() for client in clients])

# Route pour ajouter un nouveau client
@app.route('/clients/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'GET':
        return render_template('new_client_form.html')

    if request.method == 'POST':
        data = request.form
        try:
            if Client.query.filter_by(email=data.get('email')).first():
                return jsonify({"success": False, "message": "Email déjà utilisé"}), 400

            new_client = Client(
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone')
            )
            db.session.add(new_client)
            db.session.commit()
            return redirect('/clients')
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400

# Route pour éditer un client
@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = db.session.get(Client, client_id)
    if not client:
        return "Client non trouvé", 404

    if request.method == 'GET':
        return render_template('edit_client.html', client=client.to_dict())

    if request.method == 'POST':
        try:
            # Mise à jour des informations du client
            client.name = request.form['name']
            client.email = request.form['email']
            client.phone = request.form['phone']

            # Gestion de l'upload de la photo
            if 'aerial_view' in request.files:
                file = request.files['aerial_view']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{client.id}_{filename}")
                    file.save(filepath)
                    client.aerial_view = filepath  # Stocker le chemin dans la base de données

            db.session.commit()
            return redirect('/clients')
        except Exception as e:
            return f"Erreur : {e}", 500

# Route pour importer des clients via un fichier Excel
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier envoyé"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        required_columns = {'name', 'email', 'phone'}
        if not required_columns.issubset(df.columns):
            return jsonify({"success": False, "message": f"Colonnes manquantes : {required_columns - set(df.columns)}"}), 400

        for _, row in df.iterrows():
            if not Client.query.filter_by(email=row['email']).first():
                new_client = Client(
                    name=row['name'],
                    email=row['email'],
                    phone=row['phone']
                )
                db.session.add(new_client)
        db.session.commit()

        return jsonify({"success": True, "message": "Contacts importés avec succès"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
