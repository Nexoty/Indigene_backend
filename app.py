from flask import Flask, request, jsonify, abort,session
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
# VERSION LEADS
# ----------------------

@app.post("/alerts")
def create_alert():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    a_type = data.get("type")
    lat = data.get("lat")
    lng = data.get("lng")

    if not all([user_id, a_type, lat, lng]):
        return jsonify({"success": False, "error": "Champs manquants"}), 400

    msg = make_fun_message(a_type)

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""INSERT INTO alerts (user_id, type, message, lat, lng)
                   VALUES (%s,%s,%s,%s,%s)""", (user_id, a_type, msg, lat, lng))
    alert_id = cur.lastrowid

    # scoring simple : +1 point par alerte (exemple)
    # (tu peux avoir une table user_scores si tu veux pousser)
    return jsonify({"success": True, "alert_id": alert_id, "fun": msg})

@app.get("/alerts/nearby")
def alerts_nearby():
    """Récupère alertes proches pour la carte / TTS."""
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
        radius_km = float(request.args.get("radius_km", 1.5))
    except:
        return jsonify({"success": False, "error": "Paramètres coords invalides"}), 400

    # Filtre temporel : dernières 6h
    db = get_db()
    cur = db.cursor(dictionary=True)
    # approx naïve: 1 deg ~ 111km
    deg = radius_km / 111.0
    cur.execute("""
      SELECT id, type, message, lat, lng, created_at
      FROM alerts
      WHERE lat BETWEEN %s AND %s
        AND lng BETWEEN %s AND %s
        AND created_at >= NOW() - INTERVAL 6 HOUR
      ORDER BY created_at DESC
      LIMIT 100
    """, (lat-deg, lat+deg, lng-deg, lng+deg))
    rows = cur.fetchall() or []
    return jsonify({"success": True, "alerts": rows})

@app.get("/leaderboard/weekly")
def leaderboard_weekly():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
      SELECT u.id, u.username, COUNT(a.id) as alerts_count
      FROM users u
      JOIN alerts a ON a.user_id = u.id
      WHERE a.created_at >= (CURDATE() - INTERVAL WEEKDAY(CURDATE()) DAY)
      GROUP BY u.id
      ORDER BY alerts_count DESC
      LIMIT 10
    """)
    return jsonify({"success": True, "top": cur.fetchall()})

@app.post("/alerts/vote")
def vote_alert():
    data = request.get_json() or {}
    alert_id = data.get("alert_id")
    user_id = data.get("user_id")
    vote = data.get("vote", "useful")  # 'useful' or 'fake'
    if not all([alert_id, user_id]):
        return jsonify({"success": False, "error": "Champs manquants"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""INSERT INTO alert_votes (alert_id, user_id, vote)
                       VALUES (%s,%s,%s)
                       ON DUPLICATE KEY UPDATE vote=VALUES(vote)""",
                    (alert_id, user_id, vote))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def assign_badges():
    db = get_db()
    cur = db.cursor(dictionary=True)
    # 1) Héros de la route: 10 alertes en 7 jours
    cur.execute("""
      SELECT user_id, COUNT(*) cnt FROM alerts
      WHERE created_at >= NOW() - INTERVAL 7 DAY
      GROUP BY user_id HAVING cnt >= 10
    """)
    winners = cur.fetchall()
    cur.execute("SELECT id FROM badges WHERE code='HERO_7D'")
    badge = cur.fetchone()
    if badge:
      for w in winners:
        cur.execute("""INSERT IGNORE INTO user_badges (user_id, badge_id) VALUES (%s,%s)""",
                    (w["user_id"], badge["id"]))



# ----------------------
# Rester pour SESSION UTILISATEURS
# ----------------------

@app.route('/api/profile', methods=['POST'])
def create_profile():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        username = data.get('username')
        phone = data.get('phone')

        if not username or not phone:
            return jsonify({"success": False, "error": "Nom et numéro requis"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier si le profil existe déjà
        cursor.execute("SELECT * FROM profile WHERE phone = %s", (phone,))
        existing_profile = cursor.fetchone()
        if existing_profile:
            return jsonify({
                "success": False,
                "error": "Ce numéro existe déjà",
                "profile": existing_profile
            }), 400

        # Insertion simple en DB (sans photo)
        cursor.execute(
            "INSERT INTO profile (username, phone) VALUES (%s, %s)",
            (username, phone)
        )
        conn.commit()
        profile_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "id": profile_id,
            "username": username,
            "phone": phone
        })

    except Exception as e:
        print("Erreur backend:", e)
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

        # Pas besoin de session, on renvoie directement l'utilisateur
        return jsonify({"success": True, "user": user})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    
@app.route('/api/me', methods=['POST'])
def me():
    user_id = request.json.get("id")
    if not user_id:
        return jsonify({"success": False, "error": "ID requis"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM profile WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "error": "Utilisateur introuvable"}), 404

        return jsonify({"success": True, "user": user})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


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






















