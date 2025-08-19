from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

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
# INSERT
# ----------------------
@app.route('/inserer', methods=['POST'])
def creer_alerte():
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

        cursor.close()
        conn.close()
        
        return jsonify({"success": True, 'message': 'Alerte créée', 'id': last_id})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/adresse', methods=['POST'])
def creer_adresse():
    conn = None
    cursor = None
    try:
        data = request.json

        # Vérification des champs obligatoires
        required_fields = ['nom', 'numero', 'latitude', 'longitude', 'rue', 'email', 'categorie']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"success": False, "error": f"Champs manquants: {', '.join(missing_fields)}"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        INSERT INTO adresse (nom, numero, latitude, longitude, rue, email, categorie)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get('nom'),
            data.get('numero'),
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

# ----------------------
# SELECT APP UPDATE
# ----------------------
@app.route('/sysapp', methods=['GET'])
def app_systeme():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM updates"
        cursor.execute(sql)
        resultats_app = cursor.fetchall() or []  # Toujours un tableau
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "data": resultats_app})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ----------------------
# SELECT
# ----------------------
@app.route('/tout', methods=['GET'])
def recuperer_alertes():
    uid = request.args.get('uid')  # Passé en paramètre GET
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM alerte")
    alertes = cursor.fetchall() or []

    import json
    alertes_filtrees = [
        a for a in alertes
        if uid not in (json.loads(a['uids_confirms']) if a.get('uids_confirms') else [])
    ]

    cursor.close()
    conn.close()

    return jsonify({"success": True, "data": alertes_filtrees})


# ----------------------
# SELECT
# ----------------------
@app.route('/recuperer', methods=['GET'])
def recuperer_alerte():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM alerte")
        resultats = cursor.fetchall() or []
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ----------------------
# Récupérer toutes les villes
# ----------------------
@app.route('/villes', methods=['GET'])
def recuperer_villes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ville")
        resultats = cursor.fetchall() or []
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ----------------------
# SELECT Services
# ----------------------
@app.route('/services', methods=['GET'])
def recuperer_services():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, name, type, latitude, longitude FROM services")
        resultats = cursor.fetchall() or []
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/update', methods=['POST'])
def mise_a_jour_alerte():
    try:
        data = request.json
        alerte_id = data.get('id')
        confirm = data.get('confirmation')
        uid = data.get('uid')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT uids_confirms FROM alerte WHERE id = %s", (alerte_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'message': "Alerte introuvable"}), 404

        import json
        uids_list = result['uids_confirms'] or []
        if isinstance(uids_list, str):
            uids_list = json.loads(uids_list)

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
                    SET confirmation = confirmation - 1, uids_confirms = %s 
                    WHERE id = %s
                """, (json.dumps(uids_list), alerte_id))
            conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': "Alerte confirmée"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ----------------------
# DELETE
# ----------------------
@app.route('/effacer', methods=['POST'])
def effacer_alerte():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "DELETE FROM alerte WHERE id=%s"
        cursor.execute(sql, (data.get('id'),))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': "Le danger est éloigné"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)





















