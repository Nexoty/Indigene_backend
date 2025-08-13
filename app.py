from flask import Flask,request,jsonify
from flask_cors import CORS
import mysql.connector

app =Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host='srv1457.hstgr.io',    # ou '82.197.82.14'
    port=3306,
    user='u119316410_nexoty',
    password='X2~NrF5iY3$c',
    database='u119316410_indigene'
)

cursor = db.cursor(dictionary=True)
#Inserer
@app.route('/inserer',methods=['POST'])
def creer_alerte():
    data =request.json
    confirmation=1
    sql="INSERT INTO alerte (id_utilisateur,type,latitude,longitude,confirmation,image)VALUES(%s,%s,%s,%s,%s,%s)"
    values=(data['uid'],data['type'],data['latitude'],data['longitude'],confirmation,data['image'])
    cursor.execute(sql,values)
    db.commit()
    return jsonify ({"success":True,'message':'creation alerte','id':cursor.lastrowid})

#Recuperer
@app.route('/recuperer',methods=['GET'])
def recuperer_alerte():
    cursor.execute("SELECT * FROM alerte")
    resultats=cursor.fetchall()
    return jsonify(resultats)

#Mise a jour
@app.route('/update',methods=['POST'])
def mise_a_jour_alerte():
    data =request.json
    confirmation=1
    sql="UPDATE alerte SET confirmation=%s WHERE id=%s"
    cursor.execute(sql,(confirmation,data['id']))
    return  jsonify({'success':True,'message':"Alerte mise a jour"})

@app.route('/effacer',methods=['POST'])
def effacer_alerte():
    data=request.json
    sql="DELETE FROM alerte WHERE id=%s"
    cursor.execute(sql,data['id'])
    return jsonify({'success':True,'message':"Le danger est eloigne"})



if __name__ =='__main__':

    app.run(debug=True)



