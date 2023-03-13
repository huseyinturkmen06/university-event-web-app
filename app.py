from flask import Flask, g,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os
import time

#src="{{ url_for('static',filename='/assets/images/uploads/'+ d.company_photo )}}

# Kullanıcı Giriş Decorator
def login_required_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in_user" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("forbidden"))           # YETKİSİZ ERİŞİMDE TEKRARDAN LOGIN SAYFASINA YÖNLENDİRİLİYORUZ
    return decorated_function


def login_required_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in_admin" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("forbidden"))           # YETKİSİZ ERİŞİMDE TEKRARDAN LOGIN SAYFASINA YÖNLENDİRİLİYORUZ
    return decorated_function


app = Flask(__name__)
app.secret_key = ""**********""
app.config["MYSQL_HOST"] = ""**********"
app.config["MYSQL_USER"] = "**********"
app.config["MYSQL_PASSWORD"] = "**********"
app.config["MYSQL_DB"] = "**********"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["UPLOAD_FOLDER"] = "static/assets/images/uploads"

mysql = MySQL(app)


@app.route("/403")
def forbidden():
    return render_template("403.html")

@app.route("/")
def slash():
    session.clear()
    return render_template("kullanicigirisyap.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


#---------------------------KULLANICI LOGIN-----------------------------------------



@app.route("/kullanicikayitol",methods = ["GET", "POST"])
def kullanicikayitol():
    if request.method == "POST":          # KAYIT OLMA GİBİ BİR VERİ YOLLAMAYA POST REQUEST DENİR
        name = request.form.get('name')
        surname = request.form.get('surname')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = sha256_crypt.encrypt(request.form.get('password'))
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into kullanicilar(name,surname,student_id,email,password) VALUES(%s,%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,surname,student_id,email,password))
          
        mysql.connection.commit()
        cursor.close()
        flash("Başarılı bir şekilde kayıt oldunuz","success")
        return redirect(url_for("kullanicikayitol"))                   
    else:                                                   
        return render_template("kullanicikayitol.html")


@app.route("/cikisyap")
def cikisyapkullanici():
    session.clear()                         # SESSION TEMİZLEMEYİ MUTLAKA YAP UNUTMA SAKIN
    return redirect(url_for("kullanicigirisyap"))

@app.route("/cikisyapadmin")
def cikisyapadmin():
    session.clear()                         # SESSION TEMİZLEMEYİ MUTLAKA YAP UNUTMA SAKIN
    return redirect(url_for("yoneticigirisyap"))

@app.route("/kullanicigirisyap",methods = ["GET","POST"])
def kullanicigirisyap():
    session.clear()
    if request.method == "POST":
        student_id = request.form.get('student_id')
        password_entered= request.form.get('password')
        cursor = mysql.connection.cursor()                  
        sorgu = "Select * From kullanicilar where student_id = %s"
        result = cursor.execute(sorgu,(student_id,))          
        if result > 0:
            data = cursor.fetchone()                     
            real_password = data["password"]            
            if(sha256_crypt.verify(password_entered,real_password)):
                print("Başarılı bir şekilde giriş yaptınız.")
                session["logged_in_user"] = True
                session["kullanicigirisi"] = True
                session["id"] = data["id"]
                session["name"] = data["name"]
                session["surname"] = data["surname"]
                session["email"] = data["email"]
                session["major"] = data["major"]
                session["student_id"] = student_id
                session["clas"] = data["clas"]
                session["phone_number"] = data["phone_number"]
                return redirect(url_for("kullanicianasayfa", id = data['id']))
            else:
                print("Parolayı yanlış girdiniz")
                return redirect(url_for("kullanicigirisyap"))
        else:
            print("Böyle bir kullanıcı bulunmuyor...")
            return redirect(url_for("kullanicigirisyap"))
    return render_template("kullanicigirisyap.html")
#----------------------------------------------------------------------------


#----------------------------KULLANICI İŞLEMLERİ-----------------------------
@app.route("/kullanicianasayfa")
@login_required_user
def kullanicianasayfa():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    cursor3 = mysql.connection.cursor()
    sorgu = "SELECT * FROM etkinlikler order by event_time LIMIT 3"
    sorgu2 = "SELECT * FROM firma LIMIT 2"
    sorgu3 = "Select * from kullanicilar where id = %s"
    result = cursor.execute(sorgu)
    result2 = cursor2.execute(sorgu2)
    result3 = cursor3.execute(sorgu3,(session["id"],))
    if result or result2 or result3 >= 0:
        etkinlikler = cursor.fetchall()
        firmalar = cursor2.fetchall()
        data = cursor3.fetchall()
        return render_template("kullanicianasayfa.html", etkinlikler = etkinlikler, firmalar = firmalar, data = data[0])
    else:
        return render_template("kullanicianasayfa.html", etkinlikler = etkinlikler, firmalar = firmalar, data = data[0])



@app.route("/kullaniciprofili")
@login_required_user
def kullaniciprofili():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * from kullanicilar where id = %s"
    sorgu2 = "Select DISTINCT e.id, e.event_name, e.event_time, e.event_place,e.event_speakers from etkinlikler e, kullanicilar k, etkinlik_katilimci ek where e.id in (Select etkinlik_id from etkinlik_katilimci where katilimci_id = %s);"
    result = cursor.execute(sorgu,(session["id"],))
    result2 = cursor2.execute(sorgu2,(session["id"],))
    if result or result2>= 0:
        data = cursor.fetchall()
        data2 = cursor2.fetchall()
        return render_template("kullaniciprofili.html",data = data[0], data2 = data2)
    else:
        return render_template("kullaniciprofili.html", id=session["id"])



@app.route("/profilduzenle",methods=["GET","POST"])
@login_required_user
def profilduzenle():
    if request.method == "POST":
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        session["email"] = email
        session["phone_number"] = phone_number    
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE kullanicilar SET email = %s, phone_number = %s where id = %s"
        cursor.execute(sorgu,(email,phone_number,session["id"]))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('kullaniciprofili'))
    else:
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM kullanicilar WHERE id = %s"
        result = cursor.execute(sorgu,(session["id"],))
        data = cursor.fetchall()
        cursor.close()
        return render_template('profilduzenle.html', data = data[0])

@app.route("/etkinliklerigoruntule")
@login_required_user
def etkinliklerigoruntule():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * from kullanicilar where id = %s"
    result = cursor.execute(sorgu,(session["id"],))
    if result >= 0:
        sorgu2 = "Select event_name,event_company,event_photo, id from etkinlikler"
        cursor2.execute(sorgu2)
        data = cursor.fetchall()
        data2 = cursor2.fetchall()
        print("data2: ", data2)
        return render_template("etkinliklerigoruntule.html", data = data[0], data2 = data2)
    else:
        return render_template("etkinliklerigoruntule.html")



# Kullanıcıların firmaları görüntülemek için kullandığı url
@app.route("/firmalar")
@login_required_user
def firmalar():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * from kullanicilar where id = %s"
    sorgu2 = "Select * from firma"
    result = cursor.execute(sorgu,(session["id"],))
    result2 = cursor2.execute(sorgu2)
    if result >= 0:
        data = cursor.fetchall()
        datafirma = cursor2.fetchall()
        cursor2 = mysql.connection.cursor()
        sorgu2 = "Select company_id, company_name, company_photo from firma"
        cursor2.execute(sorgu2)
        data2= cursor2.fetchall()
        return render_template("firmalar.html", data = data[0], data2 = data2, datafirma = datafirma)
    else:
        return render_template("firmalar.html", data = data)






#data veya data2 de hata var. IndexError: tuple index out of range / line:385
@app.route("/etkinlikdetay/<string:eid>")
@login_required_user
def etkinlikdetay(eid):
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor() 
    cursor3 = mysql.connection.cursor()
    sorgu = "Select * from etkinlikler where id = %s"
    result = cursor.execute(sorgu,(eid,))
    if result >= 0:
        data = cursor.fetchall()        #data = etkinliğin tüm bilgileri 
        sorgu2 = "Select * from kullanicilar where student_id = %s"
        # sorgu3 = "Select * from yonetici where admin_nickname = %s" 
        resultkullanici = cursor2.execute(sorgu2,(session["student_id"],))
        # resultyonetici = cursor3.execute(sorgu2,(session["nickname"],))
        if resultkullanici > 0:  
            data2 = cursor2.fetchall()      #data2 = kullanıcının bilgileri
            if not kontrol(eid):
                varmi = kontrol(eid) 
                return render_template("etkinlikdetay.html", data2 = data[0],  data = data2[0], varmi = varmi)  
            else:
                varmi = kontrol(eid)  
                return render_template("etkinlikdetay.html", data2 = data[0],  data = data2[0], varmi = varmi)
        else:                                                                                                       
            #data3 = cursor3.fetchall()
            return render_template("etkinlikdetay.html", data2 = data[0]) #, data = data3[0])
    else:
        return render_template("etkinlikdetay.html")



def kontrol(eid):
    cursor = mysql.connection.cursor()
    print("id: {}, eid: {}".format(session["id"],eid))
    sorgu = "Select * from etkinlik_katilimci where katilimci_id = %s and etkinlik_id = %s;"
    cursor.execute(sorgu,(session["id"],eid))
    data = cursor.fetchall()
    print("Data kontrol: ", data)
    if len(data) > 0:
        return True
    else:
        return False  

@app.route("/etkinligebasvur/<string:eid>")  #burada id = kullanıcı id
@login_required_user
def etkinligebasvur(eid):
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * from kullanicilar where id = %s"    
    result = cursor.execute(sorgu,(session["id"],))
    if result >= 0:
        data = cursor.fetchall()  #data = kullanıcı bilgisi
        sorgu2 = "Insert into etkinlik_katilimci(etkinlik_id,katilimci_id) VALUES(%s,%s)"
        cursor2.execute(sorgu2,(eid, session["id"]))  
        mysql.connection.commit()
        cursor2.close()
        print("data: ", data)
        return render_template("etkinligebasvur.html", data = data[0], eid = eid)
    else:
        return render_template("etkinligebasvur.html", data = data)


#Kullanıcının firma detayını görüntülemek için kullandığı url
@app.route("/firmadetay/<string:fid>")
@login_required_user
def firmadetay(fid):
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "Select * from firma where company_id = %s"
    sorgu2 = "Select * from kullanicilar where id = %s"
    result = cursor.execute(sorgu,(fid,))
    result2 = cursor2.execute(sorgu2,(session["id"],))
    if result or result2 >= 0:
        firma = cursor.fetchall()
        data = cursor2.fetchall()
        print("datakullanici: ", data)
        return render_template("firmadetay.html", firma = firma[0], data = data[0])
    else:
        return render_template("firmadetay.html")

@app.route("/sertifikalarim")
@login_required_user
def sertifikalarim():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "SELECT * FROM kullanicilar WHERE id = %s"
    result = cursor.execute(sorgu,(session["id"],))
    if result >= 0 :
        data = cursor.fetchall()
        cursor.close()
        sorgu2 = "select DISTINCT e.id, e.event_company, e.event_name, e.event_time, e.event_speakers from etkinlikler e, kullanicilar k, etkinlik_katilimci ek where e.id in (Select ek.etkinlik_id from etkinlik_katilimci where ek.katilimci_id = %s);"
        cursor2.execute(sorgu2,(session["id"],))
        data2 = cursor2.fetchall()
        return render_template("sertifikalarim.html", data=data[0], data2 = data2)
    else:
        return render_template("sertifikalarim.html", data=data[0])



# --------------------------YONETİCİ LOGIN---------------------------------
@app.route("/yoneticigirisyap",methods = ["GET","POST"])
def yoneticigirisyap():
    session.clear()
    if request.method == "POST":
        email = request.form.get('email')
        password_entered= request.form.get('admin_password') 
        cursor = mysql.connection.cursor()                  
        sorgu = "Select * From yonetici where admin_email = %s"
        result = cursor.execute(sorgu,(email,))          
        if result > 0:
            data = cursor.fetchone()                      
            real_password = data["admin_password"]            
            if(sha256_crypt.verify(password_entered,real_password)):
                print("Başarılı bir şekilde giriş yaptınız.")
                session["logged_in_admin"] = True
                session["yoneticigirisi"] = True
                session["admin_nickname"] = data["admin_nickname"]  
                session["admin_email"] = data["admin_email"]  
                session["admin_major"] = data["admin_major"] 
                session["admin_photo"] = data["admin_photo"]    
                print(session["admin_photo"])                
                return redirect(url_for('adminanasayfa')) 
            else:
                print("Parolayı yanlış girdiniz")
                return redirect(url_for("yoneticigirisyap"))
        else:
            print("Böyle bir kullanıcı bulunmuyor...")
            return redirect(url_for("yoneticigirisyap"))
    return render_template("yoneticigirisyap.html")

@app.route("/etkinlikolustur",methods=["GET","POST"])
@login_required_admin
def etkinlikolustur():
    if request.method == "POST":          
        event_company = request.form.get('event_company') 
        event_name = request.form.get('event_name') 
        event_description = request.form.get('event_description') 
        event_time = request.form.get('event_time') 
        event_start_time = request.form.get('event_start_time') 
        event_finish_time = request.form.get('event_finish_time') 
        event_place = request.form.get('event_place') 
        event_photo = request.form.get('event_photo') 
        event_speakers = request.form.get('event_speakers')   
        event_department = request.form.getlist('event_department')
        event_department = listToString(event_department) 
        cursor = mysql.connection.cursor()

        upload_image = request.files["event_photo"]
        event_photo = secure_filename(upload_image.filename)    # Used to store filename
        if upload_image != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"],upload_image.filename)
            upload_image.save(filepath)
            print("Resim başarıyla yüklendi! Kontrol Ediniz")
        else:
            print("Resim seçmediniz")

        sorgu = "Insert into etkinlikler(event_company,event_name,event_time,event_description,event_start_time,event_finish_time,event_place,event_photo,event_speakers,event_department) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(event_company,event_name,event_time,event_description,event_start_time,event_finish_time,event_place,event_photo,event_speakers,event_department))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("etkinlikolustur"))                   
    else:
        cursor = mysql.connection.cursor()
        sorgu = "Select company_name from firma"
        result = cursor.execute(sorgu)
        if result >= 0:
            data = cursor.fetchall()
            return render_template("etkinlikolustur.html", data = data)


def listToString(l):
    str = ""
    for elem in l:
        str += elem + ", "
    return str

@app.route("/etkinliklerigoruntuleadmin")
@login_required_admin
def etkinliklerigoruntuleadmin():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from etkinlikler"
    result = cursor.execute(sorgu)
    if result >= 0:
        data = cursor.fetchall()
        return render_template("etkinliklerigoruntuleadmin.html", data = data)
    else:
        return render_template("etkinliklerigoruntuleadmin.html")

@app.route("/etkinlikdetayadmin/<string:id>")
@login_required_admin
def etkinlikdetayadmin(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from etkinlikler where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result >= 0:
        data = cursor.fetchall()
        print("data: ", data)
        return render_template("etkinlikdetayadmin.html", data = data[0])
    else:
        return render_template("etkinlikdetayadmin.html",id = id)

@app.route("/etkinligiguncelle/<string:id>", methods=["GET","POST"])
@login_required_admin
def etkinligiguncelle(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from etkinlikler where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        data = cursor.fetchall()
        if request.method == "POST":  
            event_company = data[0]['event_company']       
            event_name = request.form.get('event_name') 
            event_description = request.form.get('event_description') 
            event_place = request.form.get('event_place') 
            event_time = request.form.get('event_time') 
            event_start_time = request.form.get('event_start_time') 
            event_finish_time = request.form.get('event_finish_time') 
            event_speakers = request.form.get('event_speakers')    
            event_department = request.form.getlist('event_department') 
            event_department = listToString(event_department)    
            upload_image = request.files["event_photo"]
            event_photo = secure_filename(upload_image.filename)    # Used to store filename
            if upload_image != "":
                filepath = os.path.join(app.config["UPLOAD_FOLDER"],upload_image.filename)
                upload_image.save(filepath)
                print("Resim başarıyla yüklendi! Kontrol Ediniz")
            else:
                print("Resim seçmediniz")  
            cursor = mysql.connection.cursor()
            sorgu = "UPDATE etkinlikler SET event_name = %s, event_description = %s, event_time = %s, event_place= %s, event_start_time = %s, event_finish_time = %s, event_speakers = %s, event_department = %s, event_photo = %s where id= %s"
            cursor.execute(sorgu,(event_name,event_description,event_time,event_place,event_start_time,event_finish_time,event_speakers,event_department,event_photo,id))
            mysql.connection.commit()
            cursor.close()
            return render_template("etkinlikdetayadmin.html", id = id, data = data[0], event_company = event_company)
        else:
            return render_template("etkinligiguncelle.html", id = id, data = data[0])
    else:
        return render_template("etkinligiguncelle.html", id = id)

@app.route("/etkinligisil/<string:id>", methods=["GET", "POST"])
@login_required_admin
def etkinligisil(id):
    cursor = mysql.connection.cursor()
    sorgu = "Delete from etkinlikler where id = %s"
    cursor.execute(sorgu,(id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("etkinliklerigoruntuleadmin"))  



@app.route("/firmaekle",methods=["GET","POST"])
@login_required_admin
def firmaekle():
    if request.method == "POST":          
        company_name = request.form.get('company_name')
        company_description = request.form.get('company_description')
        company_address = request.form.get('company_address') 
        company_authorized_person = request.form.get('company_authorized_person')     
        cursor = mysql.connection.cursor()

        upload_image = request.files["company_photo"]
        company_photo = secure_filename(upload_image.filename)    # Used to store filename
        if upload_image != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"],upload_image.filename)
            upload_image.save(filepath)
            print("Resim başarıyla yüklendi! Kontrol Ediniz")
        else:
            print("Resim seçmediniz")

        sorgu = "Insert into firma(company_name,company_description,company_address,company_authorized_person,company_photo) VALUES(%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(company_name,company_description,company_address,company_authorized_person,company_photo))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("firmalarigoruntule"))                  
    else:                                                    
        return render_template("firmaekle.html")


# Admnilerin firmaları görüntülemek için kullandığı url
@app.route("/firmalarigoruntule")
@login_required_admin
def firmalarigoruntule():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from firma"
    result = cursor.execute(sorgu)
    if result >= 0:
        data = cursor.fetchall()
        return render_template("firmalarigoruntule.html", data = data)
    else:
        return render_template("firmalarigoruntule.html")


#Adminin firma detayını görüntülemek için kullandığı url
@app.route("/firmadetayadmin/<string:id>")
@login_required_admin
def firmadetayadmin(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from firma where company_id = %s"
    result = cursor.execute(sorgu,(id,))
    if result  >= 0:
        firma = cursor.fetchall()
        return render_template("firmadetayadmin.html", firma = firma[0])
    else:
        return render_template("firmadetayadmin.html")



@app.route("/firmasil/<string:id>", methods=["GET", "POST"])
@login_required_admin
def firmasil(id):
    cursor = mysql.connection.cursor()
    sorgu = "Delete from firma where company_id = %s"
    cursor.execute(sorgu,(id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("firmalarigoruntule"))  

@app.route("/firmaguncelle/<string:id>",methods=["GET","POST"])  # BURADA HATA VAR. GÜNCELLEME SONRASI URL YÖNLENDİRMEDE. TEKRARDAN İLGİLEN!!
@login_required_admin
def firmaguncelle(id):
    if request.method == "POST":          
        company_name = request.form.get('company_name')
        company_description = request.form.get('company_description')
        company_address = request.form.get('company_address') 
        company_authorized_person = request.form.get('company_authorized_person')  
        upload_image = request.files["company_photo"]
        company_photo = secure_filename(upload_image.filename)    # Used to store filename
        if upload_image != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"],upload_image.filename)
            upload_image.save(filepath)
            print("Resim başarıyla yüklendi! Kontrol Ediniz")
        else:
            print("Resim seçmediniz")
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE firma SET company_name = %s, company_description = %s, company_address= %s, company_authorized_person = %s, company_photo = %s where company_id = %s"
        cursor.execute(sorgu,(company_name,company_description,company_address,company_authorized_person,company_photo,id))  
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("firmalarigoruntule"))                
    else:                                                   
        cursor = mysql.connection.cursor()
        sorgu = "Select * from firma where company_id = %s"
        result = cursor.execute(sorgu,(id,))
        data = cursor.fetchall()
        return render_template("firmaguncelle.html", data = data[0])


@app.route("/adminanasayfa")
@login_required_admin
def adminanasayfa():
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "SELECT * FROM etkinlikler order by event_time LIMIT 3"
    sorgu2 = "SELECT * FROM firma LIMIT 2"
    result = cursor.execute(sorgu)
    result2 = cursor2.execute(sorgu2)
    if result or result2 >= 0:
        etkinlikler = cursor.fetchall()
        firmalar = cursor2.fetchall()
        return render_template("adminanasayfa.html", etkinlikler = etkinlikler, firmalar = firmalar)
    else:
        return render_template("adminanasayfa.html", etkinlikler = etkinlikler, firmalar = firmalar)



@app.route("/sertifikagoruntule/<string:eid>")
def sertifikagoruntule(eid):
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "select DISTINCT k.name, k.surname, k.major, e.event_time, e.event_company, e.event_name, e.event_speakers, e.event_photo, e.event_department, f.company_photo from etkinlikler e, kullanicilar k, firma f, etkinlik_katilimci ek where k.id = %s and e.id = %s and f.company_name = e.event_company"
    result = cursor.execute(sorgu,(session["id"],eid))
    if result >= 0 :
        data = cursor.fetchall()
        cursor.close()
        bolumler = data[0]["event_department"]
        bolumler = bolumler.strip()
        if bolumler.endswith(","):
            bolumler = bolumler[:-1]
        else:
            bolumler = bolumler
        sorgu2 = "select DISTINCT e.event_company, e.event_name, e.event_time, e.event_speakers, f.company_photo, e.event_department from etkinlikler e, kullanicilar k, firma f ,etkinlik_katilimci ek where e.id in (Select ek.etkinlik_id from etkinlik_katilimci where ek.katilimci_id = %s) and f.company_name = e.event_company;"
        cursor2.execute(sorgu2,(session["id"],))
        data2 = cursor2.fetchall()
        
        if "," in bolumler :
            bolumler=bolumler.split(",")
        else:
            
            list1=[]
            list1.append(bolumler)
            bolumler=list1

        print(data[0]["event_speakers"])
        sertifika_speakers=data[0]["event_speakers"]

        if "," in sertifika_speakers :
            sertifika_speakers=sertifika_speakers.split(",")
        else:
            list2=[]
            list2.append(sertifika_speakers)
            sertifika_speakers=list2
        
        return render_template("sertifikagoruntule.html", sertifika_speakers=sertifika_speakers, data2 = data2, bolumler=bolumler,data=data[0]) 
    else:
        
        return render_template("sertifikagoruntule.html", sertifika_speakers=sertifika_speakers,data=data[0])
        



@app.route("/bizeulasin", methods=["GET","POST"])
def bizeulasin():
    if request.method == "POST":          
        student_id = session['student_id']
        message = request.form.get('message')     
        topic = request.form.get('topic')   
        department = request.form.get('department')   
        cursor = mysql.connection.cursor()
        sorgu = "Insert into bizeulasin(student_id,topic,message,department) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(student_id,topic,message,department))
        mysql.connection.commit()
        cursor.close()
        time.sleep(1.5)
        return redirect(url_for("kullaniciprofili"))               
    else:                                                   
        cursor = mysql.connection.cursor()
        sorgu = "Select * from kullanicilar where id = %s"
        cursor.execute(sorgu,(session["id"],))
        data = cursor.fetchall()
        return render_template("bizeulasin.html", data = data[0])


@app.route("/katilanlarigoruntule/<string:id>")
@login_required_admin
def katilanlarigoruntule(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT DISTINCT k.student_id, k.name, k.surname, k.major, k.clas, ek.etkinlik_id from etkinlikler e, kullanicilar k, etkinlik_katilimci ek where k.id in (Select ek.katilimci_id from etkinlik_katilimci where ek.etkinlik_id = %s)"
    cursor.execute(sorgu,(id,))
    data = cursor.fetchall()
    return render_template("katilanlarigoruntule.html", id = id, data = data)  

@app.route("/mesajlar")
@login_required_admin
def mesajlar():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT DISTINCT b.id,  k.name, k.surname, k.student_id, k.major, b.topic, b.department from kullanicilar k, bizeulasin b where k.student_id in (Select b.student_id from bizeulasin) and b.department = %s"
    cursor.execute(sorgu,(session["admin_major"],))
    data = cursor.fetchall()
    return render_template("mesajlar.html", data = data)  


@app.route("/mesajigoruntule/<string:id>")
@login_required_admin
def mesajigoruntule(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT DISTINCT k.name, k.surname, k.student_id, k.email, k.major, k.clas, k.phone_number, b.topic, b.message from kullanicilar k, bizeulasin b where k.student_id in (Select b.student_id from bizeulasin where b.id = %s)"
    cursor.execute(sorgu,(id,))
    data = cursor.fetchall()
    return render_template("mesajigoruntule.html", data = data[0])  


@app.route("/ara", methods=["GET","POST"])
@login_required_user
def ara():
    kelime = request.form.get("search")
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    cursor3 = mysql.connection.cursor()
    sorgu = "select distinct * from firma where company_name LIKE '%"+ kelime + "%'"
    sorgu2 = "select distinct * from etkinlikler where event_company LIKE \'%" + kelime + "%\' OR event_name LIKE \'%" + kelime + "%'"
    sorgu3 = "Select distinct * from kullanicilar where id = %s"
    result = cursor.execute(sorgu)
    result2 = cursor2.execute(sorgu2)
    result3 = cursor3.execute(sorgu3,(session["id"],))
    if result or result2 or result3 >= 0:
        firmalar = cursor.fetchall()
        etkinlikler = cursor2.fetchall()
        data = cursor3.fetchall()
        return render_template("ara.html", etkinlikler = etkinlikler, firmalar = firmalar, data = data[0])
    else:
        return render_template("ara.html", etkinlikler = etkinlikler, firmalar = firmalar, data = data[0])


@app.route("/adminara", methods=["GET","POST"])
@login_required_admin
def adminara():
    kelime = request.form.get("search")
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    sorgu = "select distinct * from firma where company_name LIKE '%"+ kelime + "%'"
    sorgu2 = "select distinct * from etkinlikler where event_company LIKE \'%" + kelime + "%\' OR event_name LIKE \'%" + kelime + "%'"
    result = cursor.execute(sorgu)
    result2 = cursor2.execute(sorgu2)
    if result or result2  >= 0:
        firmalar = cursor.fetchall()
        etkinlikler = cursor2.fetchall()
        return render_template("adminara.html", etkinlikler = etkinlikler, firmalar = firmalar)
    else:
        return render_template("adminara.html", etkinlikler = etkinlikler, firmalar = firmalar)


@app.route("/profilincele/<string:id>")
def profilincele(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from kullanicilar where student_id = %s"
    cursor.execute(sorgu,(id,))
    data = cursor.fetchall()
    return render_template("profilincele.html", data = data[0])  



if __name__ == "__main__":
    app.run(debug=True,port=5858)
