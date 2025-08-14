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

# ----------------------
# SELECT
# ----------------------
@app.route('/tout', methods=['GET'])
def recuperer_alertes():
    uid = request.args.get('uid')  # Passé en paramètre GET

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM alerte")
    alertes = cursor.fetchall()

    import json
    alertes_filtrees = [
        a for a in alertes
        if uid not in (json.loads(a['uids_confirms']) if a['uids_confirms'] else [])
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
        resultats = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


#-----------------------
# RECUPERER MESSAGE SYSTEME
#-----------------------
@app.route('/systeme',methods=['GET'])
def app_systeme():
    try:
        conn =get_db_connection()
        cursor=conn.cursor(dictionary=True)
        
        sql="SELECT * FROM updates"
        cursor.execute(sql)
        resultats =cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success":True,"data":resultats})
        
    except Exception as e:
        return jsonify({"success":False,"error":str(e)}),500


# ----------------------
# UPDATE
# ----------------------
@app.route('/update', methods=['POST'])
def mise_a_jour_alerte():
    try:
        data = request.json
        alerte_id = data.get('id')
        uid = data.get('uid')  # Nouvel identifiant utilisateur

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer la liste existante
        cursor.execute("SELECT uids_confirms FROM alerte WHERE id = %s", (alerte_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'success': False, 'message': "Alerte introuvable"}), 404

        uids_list = result['uids_confirms'] or []
        if isinstance(uids_list, str):
            import json
            uids_list = json.loads(uids_list)

        # Ajouter l'UID s'il n'est pas déjà présent
        if uid not in uids_list:
            uids_list.append(uid)

            cursor.execute("""
                UPDATE alerte 
                SET confirmation = confirmation + 1, uids_confirms = %s 
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
# Récupérer toutes les villes
# ----------------------
@app.route('/villes', methods=['GET'])
def recuperer_villes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ville")
        resultats = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": resultats})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)












