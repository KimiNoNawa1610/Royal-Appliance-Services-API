import json
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS, cross_origin
import configparser
import pdfkit as pdf
from datetime import datetime
import os
import psycopg2
import jwt

app = Flask(__name__)
cors = CORS(app, support_credentials=True)
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
@cross_origin(support_credentials=True)
def generate_internal_invoice():
    if "token" not in request.headers:
            return jsonify("no token in the header")
    else:
        # print(request.headers["token"])
        try:
            profile = jwt.decode(request.headers["token"], key=app_conf.get(
                "key", "secret_key"), algorithms=["HS256"])

            print(profile)

        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError, json.decoder.JSONDecodeError) as e:
            return jsonify("Token Error")

        if not request.args:

            return jsonify("Please include all necessary attributes")

        else:

            content_type = request.headers.get('Content-Type')

            # print(content_type)

            if (content_type == 'application/json'):

                if "invoice_number" not in request.args:

                    return jsonify("Please include the invoice number")

                date_string = ""

                if "date" not in request.args:

                    date = datetime.now()

                    date_string = f"{str(date.month)}/{str(date.day)}/{str(date.year)}"

                else:

                    date_string = request.args["date"]

                info = request.get_json()

                invoice_number = request.args["invoice_number"]

                try:

                    with open('templates\internal_invoice.html', "r") as f:

                        html_string = f.read()

                        # print(app_conf.get("client_info","name"))

                        html_string = html_string.replace(
                            "{{company_name}}", app_conf.get("client_info", "name"))

                        html_string = html_string.replace(
                            "{{client}}", info["client"])

                        html_string = html_string.replace(
                            "{{street_address}}", app_conf.get("client_info", "street_address"))

                        html_string = html_string.replace(
                            "{{city_zipcode}}", app_conf.get("client_info", "city_zipcode"))

                        html_string = html_string.replace(
                            "{{phone_number}}", app_conf.get("client_info", "phone"))

                        html_string = html_string.replace(
                            "{{date}}", date_string)

                        t_string = ""

                        rows = ""

                        values = {'id': invoice_number, 'total': 0, 'net': 0, 'shipping': 0, 'my_part': 0,
                                'labor': 0, 'tax': 0, 'sell': 0, 'part_installed': "", 'paid_by': ""}

                        with open('templates\internal_tableRow.html', "r") as t:

                            t_string = t.read()

                            for row in info["rows"]:

                                rows += t_string.replace("{{item}}", str(row["item"])).replace("{{my_part}}", str(row["my_part"])).replace("{{labor}}", str(row["labor"])).replace("{{tax}}", str(row["tax"])).replace("{{shipping}}", str(
                                    row["shipping"])).replace("{{sell}}", str(row["sell"])).replace("{{paid_by}}", row["paid_by"]).replace("{{net}}", str(row["total"]-row["my_part"]-row["tax"])).replace("{{total}}", str(row["total"]))

                                # print(row)

                                values['total'] += row["total"]

                                values['net'] += row["total"] - \
                                    row["my_part"]-row["tax"]

                                values['shipping'] += row["shipping"]

                                values['my_part'] += row["my_part"]

                                values['labor'] += row["labor"]

                                values['tax'] += row['tax']

                                values['sell'] += row['sell']

                                values['part_installed'] += row["item"]+", "

                                values['paid_by'] += row["paid_by"]+", "

                        html_string = html_string.replace("{{rows}}", rows)

                        html_string = html_string.replace(
                            "{{total}}", str(values['total']))

                        html_string = html_string.replace(
                            "{{paid}}", str(info["paid"]))

                        html_string = html_string.replace(
                            "{{due}}", str(values['total'] - info["paid"]))

                        html_string = html_string.replace(
                            "{{invoice_number}}", invoice_number)

                        html_string = html_string.replace(
                            "{{note}}", info["note"])

                    with open("templates\internal_invoice_out.html", "w") as outf:

                        # print("written")

                        outf.write(html_string)

                    save_path1 = f"internal_invoices\invoice_{str(invoice_number)}.pdf"

                    if not os.path.exists(save_path1):

                        with open(save_path1, "w") as outp:

                            # print("written")

                            outp.write(" ")

                    # client invoice

                    with open('templates\client_invoice.html', "r") as f:

                        html_string = f.read()

                        # print(app_conf.get("client_info","name"))

                        html_string = html_string.replace(
                            "{{company_name}}", app_conf.get("client_info", "name"))

                        html_string = html_string.replace(
                            "{{client}}", info["client"])

                        html_string = html_string.replace(
                            "{{street_address}}", app_conf.get("client_info", "street_address"))

                        html_string = html_string.replace(
                            "{{city_zipcode}}", app_conf.get("client_info", "city_zipcode"))

                        html_string = html_string.replace(
                            "{{phone_number}}", app_conf.get("client_info", "phone"))

                        html_string = html_string.replace(
                            "{{date}}", date_string)

                        t_string = ""

                        rows = ""

                        values = {'id': invoice_number, 'total': 0, 'net': 0, 'shipping': 0, 'my_part': 0,
                                'labor': 0, 'tax': 0, 'sell': 0, 'part_installed': "", 'paid_by': ""}

                        with open('templates\client_tableRow.html', "r") as t:

                            t_string = t.read()

                            for row in info["rows"]:

                                rows += t_string.replace("{{item}}", str(row["item"])).replace("{{tax}}", str(row["tax"])).replace(
                                    "{{shipping}}", str(row["shipping"])).replace("{{paid_by}}", row["paid_by"]).replace("{{total}}", str(row["total"]))

                                # print(row)

                                values['total'] += row["total"]

                                values['shipping'] += row["shipping"]

                                values['tax'] += row['tax']

                                values['part_installed'] += row["item"]+", "

                                values['paid_by'] += row["paid_by"]+", "

                        html_string = html_string.replace("{{rows}}", rows)

                        html_string = html_string.replace(
                            "{{total}}", str(values['total']))

                        html_string = html_string.replace(
                            "{{paid}}", str(info["paid"]))

                        html_string = html_string.replace(
                            "{{due}}", str(values['total'] - info["paid"]))

                        html_string = html_string.replace(
                            "{{invoice_number}}", invoice_number)

                    # print(html_string)

                    

                    with open("templates\client_invoice_out.html", "w") as outf:

                        # print("written")

                        outf.write(html_string)

                    
                    save_path2 = f"client_invoices\invoice_{str(invoice_number)}.pdf"



                    if not os.path.exists(save_path2):

                        with open(save_path2, "w") as outp:

                            # print("written")

                            outp.write(" ")

                    pdf.from_file(
                        "templates\internal_invoice_out.html", save_path1)

                    pdf.from_file("templates\client_invoice_out.html", save_path2)

                    postgres_insert_query = """ INSERT INTO "Invoices".invoices(id, total, my_part, labor, tax, shipping, net, part_installed, client_sell, paid_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                    cur.execute(postgres_insert_query, (values["id"], values["total"], values["my_part"], values["labor"], values["tax"],
                                values["shipping"], values["net"], values["part_installed"][:-2], values["sell"], values["paid_by"][:-2]))

                    conn.commit()

                    count = cur.rowcount

                    print(count, "Record inserted successfully into invoices table")

                    return jsonify("Invoice Generated")

                except Exception as e:

                    return jsonify(e)

            else:

                return 'Content-Type not supported!'

#FIXED
@app.route("/get_invoice/<_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_invoice(_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")
            columns = []
            postgres_invoice_query = f'SELECT * FROM "Invoice"."Invoices" WHERE "invoiceID" =  {_id}'
            cur.execute(postgres_invoice_query)
            row = cur.fetchone()
            cols = cur.description
            for col in cols:
                columns.append(col[0])
            return jsonify(dict(zip(columns, row)))
    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/get_all_employees/", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_employees():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                try:
                    profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                    print(profile)

                except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                    return jsonify("Token Error")


                postgres_employee_search = f"""SELECT * FROM "Employee"."Employees" WHERE email='{profile['email']}';"""

                cur.execute(postgres_employee_search)

                row = cur.fetchone()

                if row:
            
                    columns = []
                    out = []
                    get_employees_query = f'SELECT * FROM "Employee"."Employees" ORDER BY "employeeID" ASC'
                    cur.execute(get_employees_query)
                    row = cur.fetchall()
                    cols = cur.description
                    for col in cols:
                        columns.append(col[0])
                    for ele in row:
                        out.append(dict(zip(columns, ele)))
                    return jsonify(out)

                else:
                    return jsonify("incorrect token")

            except Exception as e:
                return jsonify(e)

    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/get_employee/<_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_employee(_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            columns = []
            get_employee_query = f'SELECT * FROM "Employee"."Employees" WHERE "employeeID" = {_id}'
            cur.execute(get_employee_query)
            row = cur.fetchone()
            cols = cur.description
            for col in cols:
                columns.append(col[0])
            return jsonify(dict(zip(columns, row)))

    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/add_employee/", methods=["POST"])
@cross_origin(support_credentials=True)
def add_employee():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            info = request.get_json()

            postgres_employee_search = f"""SELECT "employeeID", name, email, password, "isAdmin" FROM "Employee"."Employees" WHERE "employeeID"={info["employeeID"]};"""

            cur.execute(postgres_employee_search)

            row = cur.fetchone()

            print(row)

            if row:

                postgres_employee_update = """UPDATE "Employee"."Employees" SET "employeeID"=%s, name=%s, email=%s, password=%s, "isAdmin"=%s WHERE "employeeID" = %s;"""

                cur.execute(postgres_employee_update,  (info["employeeID"], info["name"], info["email"], info["password"], info["isAdmin"],info["employeeID"]))

                conn.commit()

                return jsonify(f"Employee {info['name']} is updated")

            else:

                postgres_employee_query = """INSERT INTO "Employee"."Employees"("employeeID", name, email, password, "isAdmin") VALUES (%s, %s, %s, crypt(%s, gen_salt('md5')),%s)"""

                cur.execute(postgres_employee_query,
                            (info["employeeID"], info["name"], info["email"], info["password"], info["isAdmin"]))

                conn.commit()

                return jsonify("New employee added")

    except Exception as e:
        return jsonify(e)

@app.route("/get_all_jobs/", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_jobs():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")
                
            columns = []
            postgres_jobs_query = f'SELECT "jobID", "clientID", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs";'
            cur.execute(postgres_jobs_query)
            rows = cur.fetchall()
            cols = cur.description
            for col in cols:
                columns.append(col[0])
            out = []
            for row in rows:
                out.append(dict(zip(columns, row)))
            return jsonify(out)
            
    except Exception as e:
        return jsonify(e)

@app.route("/get_jobs/<_employee_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_jobs(_employee_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")
            columns = []
            postgres_jobs_query = f'SELECT "EmployeeJobs"."employeeID","Jobs"."jobID", "clientID", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs" INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID" WHERE "EmployeeJobs"."employeeID" = {_employee_id};'
            cur.execute(postgres_jobs_query)
            rows = cur.fetchall()
            cols = cur.description
            for col in cols:
                columns.append(col[0])
            out = []
            for row in rows:
                out.append(dict(zip(columns, row)))
            return jsonify(out)

    except Exception as e:
        return jsonify(e)

#Working
@app.route("/assign_job/<_client_id>/<_employee_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def assign_job(_client_id,_employee_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

    except Exception as e:
        return jsonify(e)
#Fixed
@app.route("/delete_employee/<_id>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_employee(_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            postgres_employee_query = f'DELETE FROM "Employee"."Employees" WHERE "employeeID" = {_id}'
            cur.execute(postgres_employee_query)
            conn.commit()
            count = cur.rowcount
            print(count)
            return jsonify("EMPLOYEE DELETED")

    except Exception as e:
        return jsonify(e)


@app.route("/authentication/", methods=["POST", "OPTIONS"])
@cross_origin(support_credentials=True)
def get_authentication():
    print(request.method)

    try:
        print(request)
        info = request.get_json()

        email = info["email"]

        password = info["password"]

        postgres_invoice_query = 'SELECT * FROM "Employee"."Employees" WHERE email = %s AND password = crypt(%s, password)'

        cur.execute(postgres_invoice_query, (email, password))

        result = cur.fetchone()

        if result:
            print("verified")
            out = {"name": None, "email": None, "isAdmin": None, "token": None}
            token = jwt.encode(payload=info, key=app_conf.get("key", "secret_key"), algorithm="HS256")
            out["name"] = result[1]
            out["email"] = result[2]
            out["isAdmin"] = result[4]
            out["token"] = token
            return jsonify(out)
        else:
            return jsonify(False)

    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/get_all_invoices/", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_invoices():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            columns = []
            out = []
            postgres_invoice_query = f'SELECT * FROM "Invoice"."Invoices"'
            cur.execute(postgres_invoice_query)
            row = cur.fetchall()
            cols = cur.description
            for col in cols:
                columns.append(col[0])
            for ele in row:
                out.append(dict(zip(columns, ele)))
            return jsonify(out)
    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/delete_invoice/<_id>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_invoice(_id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                    return jsonify("Token Error")

            file_path1 = f"internal_invoices\\invoice_{_id}.pdf"
            file_path2 = f"client_invoices\\invoice_{_id}.pdf"
            postgres_invoice_query = f'DELETE FROM "Invoice"."Invoices" WHERE "Invoices"."invoiceID" = {_id}'
            cur.execute(postgres_invoice_query)
            conn.commit()
            count = cur.rowcount
            os.remove(file_path1)
            os.remove(file_path2)
            print(count)
            return jsonify("INVOICE DELETED")
    except Exception as e:
        return jsonify(e)

#FIXED
@app.route("/download_invoice/<_folder>/<_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def download_invoice(_folder, _id):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            #print(request.headers["token"])
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            if _folder == "internal":
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


@app.route("/connection_test", methods=["GET", "POST"])
@cross_origin(support_credentials=True)
def connection_test():
    return jsonify("Rest API is running")

#FIXED
@app.route("/get_invoice_test", methods=["GET"])
@cross_origin(support_credentials=True)
def get_invoice_test():
    try:

        html_string = ""

        with open('templates\internal_invoice.html', "r") as f:

            html_string = f.read()

            # print(app_conf.get("client_info","name"))

            html_string = html_string.replace(
                "{{company_name}}", app_conf.get("client_info", "name"))

            html_string = html_string.replace("{{client}}", "tester")

            html_string = html_string.replace(
                "{{street_address}}", app_conf.get("client_info", "street_address"))

            html_string = html_string.replace(
                "{{city_zipcode}}", app_conf.get("client_info", "city_zipcode"))

            html_string = html_string.replace(
                "{{phone_number}}", app_conf.get("client_info", "phone"))

            date = datetime.now()

            date_string = f"{str(date.month)}/{str(date.day)}/{str(date.year)}"

            html_string = html_string.replace("{{date}}", date_string)

            t_string = ""

            with open('templates\internal_tableRow.html', "r") as t:

                t_string = t.read()

                t_string = t_string.replace("{{item}}", "Drain Pump").replace("{{total}}", "2368").replace("{{my_part}}", "313").replace("{{labor}}", "1415").replace(
                    "{{tax}}", "56.25").replace("{{shipping}}", "36").replace("{{sell}}", "893").replace("{{paid_by}}", "cash").replace("{{net}}", "1999")

            html_string = html_string.replace("{{rows}}", t_string)

            html_string = html_string.replace("{{total}}", "699")

            html_string = html_string.replace("{{paid}}", "0")

            html_string = html_string.replace("{{due}}", "699")

            html_string = html_string.replace("{{invoice_number}}", "16102000")

            html_string = html_string.replace("{{note}}", "Testing")

        # print(html_string)
        with open("templates\internal_invoice_out.html", "w") as outf:
            # print("written")
            outf.write(html_string)

        pdf.from_file("templates\internal_invoice_out.html",
                      "internal_invoices\\file.pdf")

        return send_file("internal_invoices\\file.pdf", as_attachment=True)
    except Exception as e:
        return jsonify(e)

'''BRIANS QUERIES'''
# @app.route("/get_invoice/<_id>", methods=["GET"])
# @cross_origin(support_credentials=True)
# def get_invoice(_id):
#     try:
#         if "token" not in request.headers:
#             return jsonify("no token in the header")
#         else:
#             #print(request.headers["token"])
#             try:
#                 profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])

#                 print(profile)

#             except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
#                 return jsonify("Token Error")
#             columns = []
#             postgres_invoice_query = f'SELECT * FROM "Invoice"."Invoices" WHERE "invoiceID" =  {_id}'
#             cur.execute(postgres_invoice_query)
#             row = cur.fetchone()
#             cols = cur.description
#             for col in cols:
#                 columns.append(col[0])
#             return jsonify(dict(zip(columns, row)))
#     except Exception as e:
#         return jsonify(e)

@app.route("/create_job/", methods=["POST"])
@cross_origin(support_credentials=True)
def create_job():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get("key", "secret_key"), algorithms=["HS256"])
                print(profile)

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError,json.decoder.JSONDecodeError) as e:
                return jsonify("Token Error")

            info = request.get_json()

            postgres_create_job = f"""SELECT "jobID", clientID, description, dateStart, dateEnd, isCompleted FROM "Job"."Jobs" WHERE "jobID"={info["jobID"]};"""

            cur.execute(postgres_create_job)

            row = cur.fetchone()

            print(row)

            if row:

                postgres_employee_update = """UPDATE "Job"."Jobs" SET "jobID"=%s, clientID=%s, description=%s, dateStart=%s, "dateEnd"=%s, "isCompleted"=%s WHERE "jobID" = %s;"""

                cur.execute(postgres_employee_update,  (info["jobID"], info["clientID"], info["description"], info["dateStart"], info["dateEnd"],info["isCompleted"]))

                conn.commit()

                return jsonify(f"Job {info['jobID']} is updated")

            else:

                postgres_employee_query = """INSERT INTO "Job"."Jobs"("jobID", clientID, description, dateStart, dateEnd, "isCompleted") VALUES (%s, %s, %s, %s,%s, %s)"""

                cur.execute(postgres_employee_query,
                            (info["jobID"], info["clientID"], info["description"], info["dateStart"], info["dateEnd"], info["isCompleted"]))

                conn.commit()

                return jsonify("New job added")
            
            

    except Exception as e:
        return jsonify(e)    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5020, debug=True)
