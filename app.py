import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import configparser
import pdfkit as pdf
from datetime import datetime
import os
import psycopg2

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = 'Content-Type'
app.config["SECRET_KEY"] = 'ROYALAPPLIANCE2022!'

app_conf = configparser.ConfigParser()
app_conf.read("app.config")

db = {}
if app_conf.has_section("postgresql"):
    params = app_conf.items("postgresql")
    for param in params:
        db[param[0]] = param[1]
else:
    raise Exception('Section not found in the file')

print('Connecting to the PostgreSQL database...')

conn = psycopg2.connect(**db)

cur = conn.cursor()

print('Connected to PostgreSQL database version:')

cur.execute('SELECT version()')

db_version = cur.fetchone()

print(db_version)

"""
args ex:
params = {"invoice_number":00000,"date": (optional)} 
json = {"amount_due","rows":[{"item":"name","description":"something","rate":"pay rate","quantity":1,"price":699}],"total":total,
"paid":,"due","note":(optional)}
""" 
@app.route("/generate_invoice", methods=["POST"])
@cross_origin()
def generate_internal_invoice():
    
    if not request.args:
        
        return jsonify("Please include all necessary attributes")

    else:

        content_type = request.headers.get('Content-Type')
        
        #print(content_type)

        if (content_type == 'application/json'):

            if "invoice_number" not in request.args:

                return jsonify ("Please include the invoice number")

            date_string = ""

            if "date" not in request.args:

                date = datetime.now()

                date_string = f"{str(date.month)}/{str(date.day)}/{str(date.year)}"

            else:

                date_string = request.args["date"]

            info = request.get_json()

            invoice_number = request.args["invoice_number"]

            try:

                with open('templates\internal_invoice.html',"r") as f:

                    html_string = f.read()

                    #print(app_conf.get("client_info","name"))

                    html_string = html_string.replace("{{company_name}}",app_conf.get("client_info","name"))

                    html_string = html_string.replace("{{client}}",info["client"])

                    html_string = html_string.replace("{{street_address}}",app_conf.get("client_info","street_address"))

                    html_string = html_string.replace("{{city_zipcode}}",app_conf.get("client_info","city_zipcode"))

                    html_string = html_string.replace("{{phone_number}}",app_conf.get("client_info","phone"))

                    html_string = html_string.replace("{{date}}",date_string)

                    t_string = ""

                    rows = ""

                    values ={'id': invoice_number,'total': 0,'net': 0,'shipping': 0,'my_part': 0,'labor' : 0,'tax' : 0,'sell' : 0,'part_installed' : "",'paid_by' : ""}

                    with open('templates\internal_tableRow.html',"r") as t:

                        t_string = t.read()

                        for row in info["rows"]:
                            
                            rows += t_string.replace("{{item}}",str(row["item"])).replace("{{my_part}}",str(row["my_part"])).replace("{{labor}}",str(row["labor"])).replace("{{tax}}",str(row["tax"])).replace("{{shipping}}",str(row["shipping"])).replace("{{sell}}",str(row["sell"])).replace("{{paid_by}}",row["paid_by"]).replace("{{net}}",str(row["total"]-row["my_part"]-row["tax"])).replace("{{total}}",str(row["total"]))
                           
                            #print(row)

                            values['total'] += row["total"]

                            values['net'] +=row["total"]-row["my_part"]-row["tax"]

                            values['shipping']+=row["shipping"]

                            values['my_part']+=row["my_part"]

                            values['labor']+=row["labor"]

                            values['tax']+=row['tax']

                            values['sell']+=row['sell']

                            values['part_installed'] += row["item"]+", "

                            values['paid_by'] += row["paid_by"]+", "

                    html_string = html_string.replace("{{rows}}",rows)

                    html_string = html_string.replace("{{total}}",str(values['total']))

                    html_string = html_string.replace("{{paid}}",str(info["paid"]))

                    html_string = html_string.replace("{{due}}",str(values['total'] - info["paid"]))

                    html_string = html_string.replace("{{invoice_number}}",invoice_number)

                    html_string = html_string.replace("{{note}}",info["note"])
                
                #client invoice

                with open('templates\client_invoice.html',"r") as f:

                    html_string = f.read()

                    #print(app_conf.get("client_info","name"))

                    html_string = html_string.replace("{{company_name}}",app_conf.get("client_info","name"))

                    html_string = html_string.replace("{{client}}",info["client"])

                    html_string = html_string.replace("{{street_address}}",app_conf.get("client_info","street_address"))

                    html_string = html_string.replace("{{city_zipcode}}",app_conf.get("client_info","city_zipcode"))

                    html_string = html_string.replace("{{phone_number}}",app_conf.get("client_info","phone"))

                    html_string = html_string.replace("{{date}}",date_string)

                    t_string = ""

                    rows = ""

                    values ={'id': invoice_number,'total': 0,'net': 0,'shipping': 0,'my_part': 0,'labor' : 0,'tax' : 0,'sell' : 0,'part_installed' : "",'paid_by' : ""}

                    with open('templates\client_tableRow.html',"r") as t:

                        t_string = t.read()

                        for row in info["rows"]:
                            
                            rows += t_string.replace("{{item}}",str(row["item"])).replace("{{tax}}",str(row["tax"])).replace("{{shipping}}",str(row["shipping"])).replace("{{paid_by}}",row["paid_by"]).replace("{{total}}",str(row["total"]))
                           
                            #print(row)

                            values['total'] += row["total"]
                         
                            values['shipping']+=row["shipping"]

                            values['tax']+=row['tax']

                            values['part_installed'] += row["item"]+", "

                            values['paid_by'] += row["paid_by"]+", "

                    html_string = html_string.replace("{{rows}}",rows)

                    html_string = html_string.replace("{{total}}",str(values['total']))

                    html_string = html_string.replace("{{paid}}",str(info["paid"]))

                    html_string = html_string.replace("{{due}}",str(values['total'] - info["paid"]))

                    html_string = html_string.replace("{{invoice_number}}",invoice_number)

                #print(html_string)

                with open ("templates\internal_invoice_out.html","w") as outf:

                    #print("written")

                    outf.write(html_string)
                
                with open ("templates\client_invoice_out.html","w") as outf:

                    #print("written")

                    outf.write(html_string)
                
                save_path1 = f"internal_invoices\invoice_{str(invoice_number)}.pdf"
                save_path2 = f"client_invoices\invoice_{str(invoice_number)}.pdf"

                if not os.path.exists(save_path1):

                    with open (save_path1,"w") as outp:

                        #print("written")

                        outp.write(" ")

                if not os.path.exists(save_path2):

                    with open (save_path2,"w") as outp:

                        #print("written")

                        outp.write(" ")
                
                pdf.from_file("templates\internal_invoice_out.html",save_path1)

                pdf.from_file("templates\client_invoice_out.html",save_path2)

                postgres_insert_query = """ INSERT INTO "Invoices".invoices(id, total, my_part, labor, tax, shipping, net, part_installed, client_sell, paid_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                cur.execute(postgres_insert_query,(values["id"],values["total"],values["my_part"],values["labor"],values["tax"],values["shipping"],values["net"],values["part_installed"][:-2],values["sell"],values["paid_by"][:-2]))

                conn.commit()

                count = cur.rowcount

                print(count, "Record inserted successfully into invoices table")

                return jsonify("Invoice Generated")

            except Exception as e:

                return jsonify(e)

        else:

            return 'Content-Type not supported!'

@app.route("/get_invoice/<_id>", methods=["GET"])
@cross_origin()
def get_invoice(_id):
    try:
        columns=[]
        postgres_invoice_query = f'SELECT * FROM "Invoices".invoices WHERE id = {_id}'
        cur.execute(postgres_invoice_query)
        row = cur.fetchone()
        cols = cur.description
        for col in cols:
            columns.append(col[0])
        return jsonify(dict(zip(columns,row)))
    except Exception as e:
        return jsonify(e)

@app.route("/get_all_employees/", methods=["GET"])
@cross_origin()
def get_all_employees():
    try:
        columns=[]
        out = []
        get_employees_query = f'SELECT * FROM "Employees"."Employee" ORDER BY "employeeID" ASC'
        cur.execute(get_employees_query)
        row = cur.fetchall()
        cols = cur.description
        for col in cols:
            columns.append(col[0])
        for ele in row:
            out.append(dict(zip(columns,ele)))
        return jsonify(out)
    except Exception as e:
        return jsonify(e)

@app.route("/get_employee/<_id>", methods=["GET"])
@cross_origin()
def get_employee(_id):
    try:
        columns=[]
        get_employee_query = f'SELECT * FROM "Employees"."Employee" WHERE "employeeID" = {_id}'
        cur.execute(get_employee_query)
        row = cur.fetchone()
        cols = cur.description
        for col in cols:
            columns.append(col[0])
        return jsonify(dict(zip(columns,row)))
    except Exception as e:
        return jsonify(e)

@app.route("/add_employee/", methods=["POST"])
@cross_origin()
def add_employee():
    try:

        info = request.get_json()
        
        postgres_employee_query = """INSERT INTO "Employees"."Employee"("employeeID", name, email, password, "isAdmin") VALUES (%s, %s, %s, crypt(%s, gen_salt('md5')),%s)"""

        cur.execute(postgres_employee_query,(info["employeeID"],info["name"],info["email"],info["password"],info["isAdmin"]))

        conn.commit()
        
        return jsonify("New employee added")
    except Exception as e:
        return jsonify(e)

@app.route("/get_authentication/", methods=["GET"])
@cross_origin()
def get_authentication():
    try:
        info = request.get_json()

        email = info["email"]

        password = info["password"]
        
        postgres_invoice_query = 'SELECT * FROM "Employees"."Employee" WHERE email = %s AND password = crypt(%s, password)'

        cur.execute(postgres_invoice_query,(email,password))

        out = cur.fetchone()

        if len(out)==1:
            return jsonify(out)
        else:
            return jsonify(False)

    except Exception as e:
        return jsonify(e)

@app.route("/get_all_invoices/", methods=["GET"])
@cross_origin()
def get_all_invoices():
    try:
        columns=[]
        out = []
        postgres_invoice_query = f'SELECT * FROM "Invoices".invoices'
        cur.execute(postgres_invoice_query)
        row = cur.fetchall()
        cols = cur.description
        for col in cols:
            columns.append(col[0])
        for ele in row:
            out.append(dict(zip(columns,ele)))
        return jsonify(out)
    except Exception as e:
        return jsonify(e)

@app.route("/delete_invoice/<_id>", methods=["POST"])
@cross_origin()
def delete_invoice(_id):
    try:
        file_path1 = f"internal_invoices\\invoice_{_id}.pdf"
        file_path2 = f"client_invoices\\invoice_{_id}.pdf"
        postgres_invoice_query = f'DELETE FROM "Invoices".invoices WHERE id = {_id}'
        cur.execute(postgres_invoice_query)
        conn.commit()
        count = cur.rowcount
        os.remove(file_path1)
        os.remove(file_path2)
        print(count)
        return jsonify("INVOICE DELETED")
    except Exception as e:
        return jsonify(e)

@app.route("/download_invoice/<_folder>/<_id>", methods=["GET"])
@cross_origin()
def download_invoice(_folder,_id):
    try:
        if _folder =="internal":
            file_path = f"internal_invoices\\invoice_{_id}.pdf"
        else:
            file_path = f"client_invoices\\invoice_{_id}.pdf"
        print(file_path)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify("Invoice with that id does not exist")
    except Exception as e:
        return jsonify(e)

@app.route("/connection_test",methods = ["GET","POST"])
@cross_origin()
def connection_test():
    return jsonify("Rest API is running")

@app.route("/get_invoice_test",methods = ["GET"])
@cross_origin()
def get_invoice_test():
    try:

        html_string =""

        with open('templates\invoice.html',"r") as f:

            html_string = f.read()

            #print(app_conf.get("client_info","name"))

            html_string = html_string.replace("{{company_name}}",app_conf.get("client_info","name"))

            html_string = html_string.replace("{{client}}","tester")

            html_string = html_string.replace("{{street_address}}",app_conf.get("client_info","street_address"))

            html_string = html_string.replace("{{city_zipcode}}",app_conf.get("client_info","city_zipcode"))

            html_string = html_string.replace("{{phone_number}}",app_conf.get("client_info","phone"))

            date = datetime.now()

            date_string = f"{str(date.month)}/{str(date.day)}/{str(date.year)}"

            html_string = html_string.replace("{{date}}",date_string)

            t_string = ""

            with open('templates\\tableRow.html',"r") as t:
            
                t_string = t.read()
                
                t_string = t_string.replace("{{item}}","Drain Pump").replace("{{total}}","2368").replace("{{my_part}}","313").replace("{{labor}}","1415").replace("{{tax}}","56.25").replace("{{shipping}}","36").replace("{{sell}}","893").replace("{{paid_by}}","cash").replace("{{net}}","1999")
            
            html_string = html_string.replace("{{rows}}",t_string)

            html_string = html_string.replace("{{total}}","699")

            html_string = html_string.replace("{{paid}}","0")

            html_string = html_string.replace("{{due}}","699")

            html_string = html_string.replace("{{invoice_number}}","16102000")

            html_string = html_string.replace("{{note}}","Testing")

        #print(html_string)
        with open ("templates\invoice_out.html","w") as outf:
            #print("written")
            outf.write(html_string)
        
        pdf.from_file("templates\invoice_out.html","internal_invoices\\file.pdf")
        
        return send_file("internal_invoices\\file.pdf", as_attachment=True)
    except Exception as e:
        return jsonify(e)

if __name__ == '__main__':
    app.run(host= "0.0.0.0",port=5020,debug=True)





        
