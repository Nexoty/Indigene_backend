from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import mysql.connector
import json
import math
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

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
# Utilitaire: distance Haversine (mètres)
# ----------------------
def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000  # rayon Terre en m
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ----------------------
# Correction pour update_voyage
# ----------------------
@app.route('/voyages/<int:vid>', methods=['PUT'])
def update_voyage(vid):
    data = request.get_json(force=True)
    allowed = {'start_lat','start_lng','end_lat','end_lng','path','color','avatar_url','status','title'}
    fields = []
    values = []
    for k,v in data.items():
        if k in allowed:
            if k == 'path':
                values.append(json.dumps(v))
            else:
                values.append(v)
            fields.append(f"{k} = %s")
    if not fields:
        return jsonify({"error":"no valid fields to update"}), 400
    values.append(vid)
    sql = f"UPDATE voyage SET {', '.join(fields)} WHERE id = %s"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql, tuple(values))
        conn.commit()
        return jsonify({"ok": True, "updated": cur.rowcount})
    except mysql.connector.Error as e:
        print("DB error:", e)
        abort(500, str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

# ----------------------
# Correction mark_arrived
# ----------------------
@app.route('/voyages/<int:vid>/arrived', methods=['POST'])
def mark_arrived(vid):
    payload = request.get_json(silent=True) or {}
    lat = payload.get('lat')
    lng = payload.get('lng')
    ARRIVAL_THRESHOLD_M = float(os.getenv('ARRIVAL_THRESHOLD_M', 20.0))

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, start_lat, start_lng, end_lat, end_lng, status FROM voyage WHERE id = %s", (vid,))
        r = cur.fetchone()
        if not r:
            return jsonify({"error":"not found"}), 404

        if (r['start_lat'] == r['end_lat']) and (r['start_lng'] == r['end_lng']):
            arrived = True
            reason = "start_equals_end"
        elif lat is not None and lng is not None:
            dist = haversine_meters(lat, lng, r['end_lat'], r['end_lng'])
            arrived = dist <= ARRIVAL_THRESHOLD_M
            reason = f"distance={dist:.1f}m threshold={ARRIVAL_THRESHOLD_M}m"
        else:
            arrived = False
            reason = "no_coords_provided_and_start_not_equal_end"

        if not arrived:
            return jsonify({"arrived": False, "reason": reason}), 200

        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("UPDATE voyage SET status = %s, arrived_at = %s WHERE id = %s", ('arrived', now, vid))
        conn.commit()
        return jsonify({"arrived": True, "reason": reason, "updated_rows": cur.rowcount}), 200

    except mysql.connector.Error as e:
        print("DB error:", e)
        abort(500, str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

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





