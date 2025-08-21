from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import mysql.connector
import json
import math
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader
import uuid

app = Flask(__name__)
CORS(app)

cloudinary.config(
    cloud_name='dg5fzqmtg',
    api_key='511658453183448',
    api_secret='-wRVxd1qbX0-4HvNOmQmXcdbxqg'
)
# Fonction pour créer une connexion MySQL
def get_db_connection():
    return mysql.connector.connect(
        host='srv1457.hstgr.io',
        port=3306,
        user='u119316410_nexoty',
        password='X2~NrF5iY3$c',
        database='u119316410_indigene'
    )

# ----------------------
# INSERT ALERTE
# ----------------------
@app.route('/inserer', methods=['POST'])
def creer_alerte():
    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        INSERT INTO alerte (id_utilisateur, type, latitude, longitude, confirmation, image, adresse)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get('uid'),
            data.get('type'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('confirmation', 0),
            data.get('image'),
            data.get('adresse')
        )

        cursor.execute(sql, values)
        conn.commit()
        last_id = cursor.lastrowid

        return jsonify({"success": True, 'message': 'Alerte créée', 'id': last_id})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# INSERT ADRESSE
# ----------------------
@app.route('/adresse', methods=['POST'])
def creer_adresse():
    conn = None
    cursor = None
    try:
        data = request.json

        required_fields = ['nom', 'latitude', 'longitude', 'rue', 'email', 'categorie']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"success": False, "error": f"Champs manquants: {', '.join(missing_fields)}"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM adresse WHERE email = %s", (data.get('email'),))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Email contient déjà une adresse"}), 409

        sql = """
        INSERT INTO adresse (nom, latitude, longitude, rue, email, categorie)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get('nom'),
            data.get('latitude'),
            data.get('longitude'),
            data.get('rue'),
            data.get('email'),
            data.get('categorie')
        )
        cursor.execute(sql, values)
        conn.commit()
        last_id = cursor.lastrowid

        return jsonify({"success": True, "message": "Adresse créée", "id": last_id})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# SELECT APP UPDATE
# ----------------------
@app.route('/sysapp', methods=['GET'])
def app_systeme():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM updates WHERE active = %s", (1,))
        resultats_app = cursor.fetchall()
        return jsonify({"success": True, "data": resultats_app})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# SELECT ALERTES FILTREES PAR UID
# ----------------------
@app.route('/tout', methods=['GET'])
def recuperer_alertes():
    uid = request.args.get('uid')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alerte WHERE confirmation >= %s", (1,))
        alertes = cursor.fetchall() or []

        alertes_filtrees = [
            a for a in alertes
            if uid not in (json.loads(a['uids_confirms']) if a.get('uids_confirms') else [])
        ]
        return jsonify({"success": True, "data": alertes_filtrees})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# SELECT ALERTES ACTIVES
# ----------------------
@app.route('/recuperer', methods=['GET'])
def recuperer_alerte():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alerte WHERE confirmation >= %s", (1,))
        resultats = cursor.fetchall()
        if not resultats:
            return jsonify({"success": False, "message": "Aucune alerte active trouvée"}), 404
        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# Récupérer les services
# ----------------------
@app.route('/services', methods=['GET'])
def recuperer_villes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM services")
        resultats = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ----------------------
# Créer un voyage
# ----------------------
@app.route('/voyages', methods=['POST'])
def create_voyage():
    conn = None
    cursor = None
    try:
        data = request.get_json()

        end_address = data.get('end')
        title = data.get('title')
        participants = data.get('participants', [])  # tableau
        if not end_address or not title:
            return jsonify({"success": False, "error": "Tous les champs sont requis"}), 400

        # Générer un lien unique pour le voyage
        voyage_uuid = str(uuid.uuid4())
        link = f"https://nexoty.com/voyage/{voyage_uuid}"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insérer le voyage avec les participants stockés en JSON
        sql = """
        INSERT INTO voyage (title, participant, end_address, link, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        # Convertir le tableau en chaîne JSON
        import json
        participant_json = json.dumps(participants)
        values = (title, participant_json, end_address, link, datetime.utcnow())
        cursor.execute(sql, values)
        conn.commit()

        voyage_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "id": voyage_id,
            "link": link,
            "message": "Voyage créé avec succès"
        })

    except Exception as e:
        print("Erreur backend:", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# Récupérer les utilisateurs inscrits pour un voyage
# ----------------------
@app.route('/voyages/users', methods=['GET'])
def get_voyage_users():
    conn = None
    cursor = None
    try:
        voyage_id = request.args.get('id')
        if not voyage_id:
            return jsonify({"success": False, "error": "ID du voyage requis"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        SELECT u.id, u.username, u.avatar_url
        FROM profile u
        INNER JOIN voyage_users vu ON vu.user_id = u.id
        WHERE vu.voyage_id = %s
        """
        cursor.execute(sql, (voyage_id,))
        users = cursor.fetchall() or []

        return jsonify({"success": True, "users": users})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/friend/add', methods=['POST'])
def add_friend():
    data = request.get_json()
    user_id = data.get('user_id')  # ID de l'utilisateur connecté
    friend_phone = data.get('friend_phone')  # Numéro de téléphone de l'ami

    if not user_id or not friend_phone:
        return jsonify({"success": False, "error": "Champs requis"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier que le profil de l'ami existe
        cursor.execute("SELECT id FROM profile WHERE phone = %s", (friend_phone,))
        friend = cursor.fetchone()
        if not friend:
            return jsonify({"success": False, "error": "Profil ami non trouvé"}), 404

        friend_id = friend['id']

        # Ajouter l'ami
        cursor.execute(
            "INSERT IGNORE INTO profile_friends (user_id, friend_id) VALUES (%s, %s)",
            (user_id, friend_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Ami ajouté"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/friends/<int:user_id>', methods=['GET'])
def get_friends(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        SELECT p.id, p.username, p.phone, p.photo
        FROM profile p
        INNER JOIN profile_friends pf ON pf.friend_id = p.id
        WHERE pf.user_id = %s
        """
        cursor.execute(sql, (user_id,))
        friends = cursor.fetchall() or []

        return jsonify({"success": True, "friends": friends})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/profile', methods=['POST'])
def create_profile():
    conn = None
    cursor = None
    try:
        username = request.form.get('username')
        phone = request.form.get('phone')
        photo_file = request.files.get('photo')

        if not username or not phone:
            return jsonify({"success": False, "error": "Nom et numéro requis"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier si le profil existe déjà
        cursor.execute("SELECT * FROM profile WHERE phone = %s", (phone,))
        existing_profile = cursor.fetchone()
        if existing_profile:
            return jsonify({"success": False, "error": "Ce numéro existe déjà", "profile": existing_profile}), 400

        photo_url = None
        if photo_file:
            # Upload sur Cloudinary seulement si une image est envoyée
            result = cloudinary.uploader.upload(photo_file)
            photo_url = result['secure_url']

        # Insertion en DB
        cursor.execute(
            "INSERT INTO profile (username, phone, photo) VALUES (%s, %s, %s)",
            (username, phone, photo_url)
        )
        conn.commit()
        profile_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "id": profile_id,
            "photo": photo_url,
            "username": username,
            "phone": phone
        })

    except Exception as e:
        print("Erreur backend:", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/profile/friend', methods=['GET'])
def check_profile_friend():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"success": False, "error": "Numéro requis"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, phone, photo FROM profile WHERE phone = %s", (phone,))
        profile = cursor.fetchone()

        if profile:
            return jsonify({"success": True, "data": profile})
        else:
            return jsonify({"success": True, "data": None})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    phone = request.json.get("phone")
    if not phone:
        return jsonify({"success": False, "error": "Numéro requis"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM profile WHERE phone = %s", (phone,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 404

        # Enregistrer l'utilisateur dans la session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['phone'] = user['phone']
        session['photo'] = user['photo']

        return jsonify({"success": True, "user": user})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    
@app.route('/api/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Non connecté"}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session['user_id'],
            "username": session['username'],
            "phone": session['phone'],
            "photo": session['photo']
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Déconnecté"})




# ----------------------
# Health check
# ----------------------
@app.route('/', methods=['GET'])
def hello():
    return jsonify({"msg":"voyage API running"}), 200

# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)
















