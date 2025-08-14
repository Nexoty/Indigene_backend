from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# Connexion à la base de données
db = mysql.connector.connect(
    host='srv1457.hstgr.io',   # ou '82.197.82.14'
    port=3306,
    user='u119316410_nexoty',
    password='X2~NrF5iY3$c',
    database='u119316410_indigene'
)
cursor = db.cursor(dictionary=True)

# ----------------------
# INSERT
# ----------------------
@app.route('/inserer', methods=['POST'])
def creer_alerte():
    try:
        data = request.json
        
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
        db.commit()
        
        return jsonify({"success": True, 'message': 'Alerte créée', 'id': cursor.lastrowid})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



# ----------------------
# SELECT
# ----------------------
@app.route('/recuperer', methods=['GET'])
def recuperer_alerte():
    cursor.execute("SELECT * FROM alerte")
    resultats = cursor.fetchall()
    return jsonify(resultats)

# ----------------------
# UPDATE
# ----------------------
@app.route('/update', methods=['POST'])
def mise_a_jour_alerte():
    try:
        data = request.json
        confirmation = 1
        sql = "UPDATE alerte SET confirmation=%s WHERE id=%s"
        cursor.execute(sql, (confirmation, data.get('id')))
        db.commit()
        return jsonify({'success': True, 'message': "Alerte mise à jour"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ----------------------
# DELETE
# ----------------------
@app.route('/effacer', methods=['POST'])
def effacer_alerte():
    try:
        data = request.json
        sql = "DELETE FROM alerte WHERE id=%s"
        cursor.execute(sql, (data.get('id'),))
        db.commit()
        return jsonify({'success': True, 'message': "Le danger est éloigné"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ----------------------
# Lancer le serveur
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)






