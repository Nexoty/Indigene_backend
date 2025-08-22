from flask import Flask, request, jsonify, abort,session
from flask_cors import CORS
import mysql.connector
import json
import random  # pour make_fun_message
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("ewewbdshdssdghsdywewewywew")
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

FUN_TEMPLATES = {
    "Route inondée": [
        "🌊 Gade dlo a! Si m’ te ou, m’ t ap pran bato wi!",
        "🐊 Atansyon! Dlo sa ka gen kwo-kodil 😅"
    ],
    "Accident": [
        "🚗💥 Pinga prese! Gen aksidan devan.",
        "⛔ Tann ti moman, bagay yo pa dous la."
    ],
    "Tir violent": [
        "🔫 Eyy, gen move zafè bal la! Evite zòn nan vit.",
        "🏃🏾 Kouri lontan, tounen byento 😬"
    ],
}

def make_fun_message(alert_type: str):
    if alert_type in FUN_TEMPLATES:
        return random.choice(FUN_TEMPLATES[alert_type])
    return f"⚠️ {alert_type} rapòte! Pran prekosyon."

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

        # Insertion alerte
        sql = """
        INSERT INTO alerte (id_utilisateur, type, latitude, longitude, confirmation, uids_confirms, image, adresse)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get('uid'),
            data.get('type'),
            data.get('latitude'),
            data.get('longitude'),
            0,          # confirmation initiale
            '[]',       # uids_confirms vide
            data.get('image'),
            data.get('adresse')
        )
        cursor.execute(sql, values)
        conn.commit()
        last_id = cursor.lastrowid

        # Ajouter 1 point initial à l'utilisateur
        cursor.execute("UPDATE users SET points = points + 1 WHERE id=%s", (data.get('uid'),))
        conn.commit()

        return jsonify({"success": True, 'message': 'Alerte créée', 'id': last_id})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/alerte/vote', methods=['POST'])
def vote_alerte():
    conn = None
    cursor = None
    try:
        data = request.json
        alert_id = data.get('alerte_id')
        user_id = data.get('user_id')
        vote = data.get('vote', 'useful')  # 'useful' ou 'fake'

        if not all([alert_id, user_id]):
            return jsonify({"success": False, "error": "Champs manquants"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer alerte existante
        cursor.execute("SELECT uids_confirms, id_utilisateur FROM alerte WHERE id=%s", (alert_id,))
        alert = cursor.fetchone()
        uids = json.loads(alert['uids_confirms'])

        # Vérifier si l'utilisateur a déjà voté
        if user_id not in uids and vote == "useful":
            uids.append(user_id)
            confirmation = len(uids)
            cursor.execute("UPDATE alerte SET confirmation=%s, uids_confirms=%s WHERE id=%s",
                           (confirmation, json.dumps(uids), alert_id))
            conn.commit()

            # + points si au moins 2 confirmations
            if confirmation >= 2:
                cursor.execute("UPDATE users SET points = points + 2 WHERE id=%s", (alert['id_utilisateur'],))
                conn.commit()

        return jsonify({"success": True, "confirmations": len(uids)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/leaderboard/weekly', methods=['GET'])
def leaderboard_weekly():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Leaderboard par points sur la semaine
    cursor.execute("""
        SELECT u.id, u.username, u.points, COUNT(a.id) as alerts_count
        FROM users u
        LEFT JOIN alerte a ON a.id_utilisateur = u.id
            AND a.created_at >= NOW() - INTERVAL 7 DAY
        GROUP BY u.id
        ORDER BY u.points DESC
        LIMIT 10
    """)
    top = cursor.fetchall()

    # Attribution badges
    for t in top:
        badges = []
        if t['alerts_count'] >= 1: badges.append("Ti Machann Alert")
        if t['alerts_count'] >= 5: badges.append("Gran Signalè")
        if t['alerts_count'] >= 10: badges.append("Chodyè Difé 🔥")
        t['badges'] = badges

    return jsonify({"success": True, "top": top})



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
# SELECT NOTIFICATIONS
# ----------------------
@app.route('/notifications', methods=['GET'])
def get_notifications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM notifications WHERE active = 1 ORDER BY created_at DESC")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "data": data})

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
# UPDATE CONFIRMATION
# ----------------------
@app.route('/update', methods=['POST'])
def mise_a_jour_alerte():
    try:
        data = request.json
        alerte_id = data.get('id')
        uid = data.get('uid')
        confirmation = data.get('confirmation')  # True = +1, False = -1

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier si uid est déjà dans la liste
        cursor.execute("SELECT uids_confirms, confirmation FROM alerte WHERE id = %s", (alerte_id,))
        alerte = cursor.fetchone()
        if not alerte:
            return jsonify({"success": False, "message": "Alerte introuvable"})

        uids_confirms = alerte["uids_confirms"] or "[]"
        import json
        uids_confirms = json.loads(uids_confirms)

        if uid in uids_confirms:
            return jsonify({"success": False, "message": "Vous avez déjà confirmé ou infirmé cette alerte."})

        # Mettre à jour la confirmation
        if confirmation:  
            sql = "UPDATE alerte SET confirmation = confirmation + 1 WHERE id = %s"
            cursor.execute(sql, (alerte_id,))
        else:  
            sql = """
                UPDATE alerte 
                SET confirmation = CASE 
                    WHEN confirmation > 0 THEN confirmation - 1 
                    ELSE 0 
                END
                WHERE id = %s
            """
            cursor.execute(sql, (alerte_id,))

        # Ajouter uid dans la liste
        uids_confirms.append(uid)
        sql_update_uids = "UPDATE alerte SET uids_confirms = %s WHERE id = %s"
        cursor.execute(sql_update_uids, (json.dumps(uids_confirms), alerte_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': "Alerte mise à jour"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



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


























