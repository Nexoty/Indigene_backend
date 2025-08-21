from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json

app = Flask(__name__)
CORS(app)

# Fonction pour créer une connexion à chaque requête
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
            data.get('confirmation'),
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

        # Vérification des champs obligatoires
        required_fields = ['nom', 'latitude', 'longitude', 'rue', 'email', 'categorie']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"success": False, "error": f"Champs manquants: {', '.join(missing_fields)}"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM adresse WHERE email = %s", (data.get('email'),))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Email contient déjà une adresse"}), 409

        # Insertion
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
# SELECT VILLES
# ----------------------
@app.route('/villes', methods=['GET'])
def recuperer_villes():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ville")
        resultats = cursor.fetchall()
        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# SELECT SERVICES
# ----------------------
@app.route('/services', methods=['GET'])
def recuperer_services():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, type, latitude, longitude FROM services")
        resultats = cursor.fetchall()
        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# SELECT DESTINATION PAR RUE
# ----------------------
@app.route('/destination', methods=['GET'])
def recuperer_destination():
    data = request.args.get('adresse')
    conn = None
    cursor = None
    try:
        if not data:
            return jsonify({"success": False, "error": "Aucune adresse fournie"}), 400
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM adresse WHERE rue = %s", (data,))
        resultats_destinations = cursor.fetchall()
        if not resultats_destinations:
            return jsonify({"success": False, "message": "Adresse introuvable"}), 404
        return jsonify({"success": True, "data": resultats_destinations})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# UPDATE ALERTE
# ----------------------
@app.route('/update', methods=['POST'])
def mise_a_jour_alerte():
    conn = None
    cursor = None
    try:
        data = request.json
        alerte_id = data.get('id')
        confirm = data.get('confirmation')
        uid = data.get('uid')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT uids_confirms, confirmation FROM alerte WHERE id = %s", (alerte_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'message': "Alerte introuvable"}), 404

        uids_list = result['uids_confirms'] or []
        if isinstance(uids_list, str):
            uids_list = json.loads(uids_list)

        confirmation_value = result['confirmation'] or 0

        if uid not in uids_list:
            uids_list.append(uid)
            if confirm is True:
                cursor.execute("""
                    UPDATE alerte 
                    SET confirmation = confirmation + 1, uids_confirms = %s
                    WHERE id = %s
                """, (json.dumps(uids_list), alerte_id))
            else:
                cursor.execute("""
                    UPDATE alerte 
                    SET confirmation = GREATEST(confirmation - 1, 0), uids_confirms = %s
                    WHERE id = %s
                """, (json.dumps(uids_list), alerte_id))
            conn.commit()

        return jsonify({'success': True, 'message': "Alerte confirmée"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ----------------------
# DELETE ALERTE
# ----------------------
@app.route('/effacer', methods=['POST'])
def effacer_alerte():
    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM alerte WHERE id=%s", (data.get('id'),))
        conn.commit()
        return jsonify({'success': True, 'message': "Le danger est éloigné"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Utilitaire : distance haversine (mètres)
def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000  # rayon Terre en m
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# -------- Routes --------

# GET /voyages => liste de voyages (optionnel: status filter)
@app.route('/voyages', methods=['GET'])
def list_voyages():
    status = request.args.get('status')  # ex: ?status=in_progress
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        sql = "SELECT id, user_id, title, start_lat, start_lng, end_lat, end_lng, path, color, avatar_url, status, started_at, arrived_at FROM voyage"
        if status:
            sql += " WHERE status = %s"
            cur.execute(sql, (status,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        # parse json field path
        for r in rows:
            if r.get('path') is None:
                r['path'] = []
            else:
                try:
                    # MySQL may return dict for JSON column or string
                    if isinstance(r['path'], (bytes, bytearray)):
                        r['path'] = json.loads(r['path'].decode('utf-8'))
                    elif isinstance(r['path'], str):
                        r['path'] = json.loads(r['path'])
                except Exception:
                    # fallback leave as-is
                    pass
        return jsonify(rows)
    except Error as e:
        print("DB error:", e)
        abort(500, str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

# PUT /voyages/<id> => update fields (start/end/path/status)
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
    except Error as e:
        print("DB error:", e)
        abort(500, str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

# POST /voyages/<id>/arrived
# On peut appeler avec body { "lat": .., "lng": .. } (optionnel) ou le backend vérifiera si start==end selon la demande
@app.route('/voyages/<int:vid>/arrived', methods=['POST'])
def mark_arrived(vid):
    payload = request.get_json(silent=True) or {}
    lat = payload.get('lat')   # position du client (optionnel)
    lng = payload.get('lng')
    # Seuil d'arrivée (mètres)
    ARRIVAL_THRESHOLD_M = float(os.getenv('ARRIVAL_THRESHOLD_M', 20.0))  # 20 m par défaut

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, start_lat, start_lng, end_lat, end_lng, status FROM voyage WHERE id = %s", (vid,))
        r = cur.fetchone()
        if not r:
            return jsonify({"error":"not found"}), 404

        # Si start et end EXACTEMENT égaux: considérer arrivé
        if (r['start_lat'] == r['end_lat']) and (r['start_lng'] == r['end_lng']):
            arrived = True
            reason = "start_equals_end"
        elif lat is not None and lng is not None:
            dist = haversine_meters(lat, lng, r['end_lat'], r['end_lng'])
            arrived = dist <= ARRIVAL_THRESHOLD_M
            reason = f"distance={dist:.1f}m threshold={ARRIVAL_THRESHOLD_M}m"
        else:
            # pas de coords fournies -> on marque arrived si start==end, sinon erreur
            arrived = False
            reason = "no_coords_provided_and_start_not_equal_end"

        if not arrived:
            return jsonify({"arrived": False, "reason": reason}), 200

        # Mettre à jour le voyage
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        cur2 = conn.cursor()
        cur2.execute("UPDATE voyage SET status = %s, arrived_at = %s WHERE id = %s", ('arrived', now, vid))
        conn.commit()
        return jsonify({"arrived": True, "reason": reason, "updated_rows": cur2.rowcount}), 200

    except Error as e:
        print("DB error:", e)
        abort(500, str(e))
    finally:
        if 'cur' in locals(): cur.close()
        if 'cur2' in locals(): cur2.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

# Simple route pour health check
@app.route('/', methods=['GET'])
def hello():
    return jsonify({"msg":"voyage API running"}), 200

# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)

























