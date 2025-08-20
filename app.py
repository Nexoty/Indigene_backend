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

# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)
























