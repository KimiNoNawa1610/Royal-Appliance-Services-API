from os.path import basename
from email.utils import formatdate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS, cross_origin
import configparser
import pdfkit as pdf
from datetime import datetime
import os
import psycopg2
import jwt
from waitress import serve
import smtplib

#initialize API
app = Flask(__name__)
cors = CORS(app, support_credentials=True)
app.config["CORS_HEADERS"] = 'Content-Type'
app.config["SECRET_KEY"] = 'ROYALAPPLIANCE2022!'#secret key of the api, for future deployment

#read the config file
app_conf = configparser.ConfigParser()
app_conf.read("app.config")

#connect to the database
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

#print our the database information
print(db_version)

"""
send_mail function:
params: 

send_to: the list of senders
subject: the string for the email subject
text: the text in the email body
files: a list of files name to attach to that email

return: none
"""

def send_mail(send_to, subject, text, files):

    assert isinstance(send_to, list)
    #print(files)

    msg = MIMEMultipart()
    msg['From'] = app_conf["email"]["user"]
    msg['To'] = ", ".join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    smtp = smtplib.SMTP('smtp.gmail.com', 587)

    smtp.starttls()
    print(app_conf["email"]["user"],app_conf["email"]["password"])
    # Authentication
    smtp.login(app_conf["email"]["user"], app_conf["email"]["password"])
    smtp.sendmail(app_conf["email"]["user"], send_to, msg.as_string())
    smtp.close()

"""
args ex:
params = {"invoice_number":00000,"date": (optional)}
json = {"amount_due","rows":[{"item":"name","description":"something","rate":"pay rate","quantity":1,"price":699}],"total":total,
"paid":,"due","note":(optional)}
"""

"""
get_employee_id end point

method: GET

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_name: the name of the employee that we want to get the id

return: the id of an employee if that employee exist else, return error message.

"""
@app.route("/get_employee_id/<_employee_name>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_employee_id(_employee_name):
    try:
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

            postgres_employee_name_search = f'''SELECT "employeeID" FROM "Employee"."Employees" WHERE name = '{_employee_name}';'''
            cur.execute(postgres_employee_name_search)
            row = cur.fetchone()
            if len(row)>0:
                return jsonify({"employeeID": row[0]})
            else:
                return jsonify("The employee does not exist.")

    except Exception as e:
        return jsonify(e)

"""
get_client_id end point

method: GET

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_client_name: the name of the client that we want to get the id

return: the id of an client if that employee exist else, return error message.

"""
@app.route("/get_client_id/<_client_name>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_client_id(_client_name):
    try:
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

            postgres_client_name_search = f'''SELECT "clientID" FROM "Client"."Clients" WHERE name = '{_client_name}';'''
            cur.execute(postgres_client_name_search)
            row = cur.fetchone()
            if len(row)>0:
                return jsonify({"clientID": row[0]})
            else:
                return jsonify("The client does not exist.")

    except Exception as e:
        return jsonify(e)

"""
add_client end point

method: POST

add the new client to the database and update if that client already exist

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
json string: the dictionary contains all required information about the client

return: the message of the action
"""
@app.route("/add_client", methods=["POST"])
@cross_origin(support_credentials=True)
def add_client():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])
            try:
                try:
                    profile = jwt.decode(request.headers["token"], key=app_conf.get(
                        "key", "secret_key"), algorithms=["HS256"])

                    print(profile)

                except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError, json.decoder.JSONDecodeError) as e:
                    return jsonify("Token Error")
                info = request.get_json()

                postgres_client_search = f"""SELECT "clientID" FROM "Client"."Clients" WHERE name='{info["name"]}' OR address='{info["address"]}' OR phone ='{info["phone"]}';"""

                cur.execute(postgres_client_search)

                row = cur.fetchone()

                print(row)

                if row:

                    postgres_client_update = """UPDATE "Client"."Clients" SET name=%s, address=%s, phone=%s, notes=%s, email=%s WHERE "clientID" = %s;"""

                    cur.execute(postgres_client_update,  (
                        info["name"], info["address"], info["phone"], info["notes"], info["email"], row[0]))

                    conn.commit()

                    return jsonify(f"Client {info['name']} is updated")

                else:

                    postgres_employee_query = """INSERT INTO "Client"."Clients"(name, address, phone, notes, email) VALUES (%s, %s, %s, %s, %s)"""

                    cur.execute(postgres_employee_query, (
                        info["name"], info["address"], info["phone"], info["notes"], info["email"]))

                    conn.commit()

                    return jsonify("New Client Added")

            except Exception as e:
                return jsonify(e)

    except Exception as e:
        return jsonify(e)

"""
job_is_finished end point

method: POST

Update the job status

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_job_id: the id of the job that we want to update the status
_completed: the status of the job completion (true or false)

return: the message of the action
"""
@app.route("/job_is_finished/<_job_id>/<_completed>", methods=["POST"])
@cross_origin(support_credentials=True)
def job_is_finished(_job_id, _completed):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])
            try:
                try:
                    profile = jwt.decode(request.headers["token"], key=app_conf.get(
                        "key", "secret_key"), algorithms=["HS256"])

                    print(profile)

                except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError, json.decoder.JSONDecodeError) as e:
                    return jsonify("Token Error")

                set_job_finish = """UPDATE "Job"."Jobs" SET "isCompleted"= %s WHERE "jobID"= %s;"""

                cur.execute(set_job_finish, (_completed, _job_id))

                conn.commit()

                return jsonify("JOB IS FINISHED")

            except Exception as e:
                return jsonify(e)

    except Exception as e:
        return jsonify(e)


"""
get_all_employees end point

method: POST

Update the job status

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_job_id: the id of the job that we want to update the status
_completed: the status of the job completion (true or false)

return: the list of all employees
"""
@app.route("/get_all_employees/", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_employees():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])
            try:
                try:
                    profile = jwt.decode(request.headers["token"], key=app_conf.get(
                        "key", "secret_key"), algorithms=["HS256"])

                    print(profile)

                except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError, json.decoder.JSONDecodeError) as e:
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

"""
get_all_clients end point

method: GET

get the list of all clients

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
none

return: the list of all client
"""
@app.route("/get_all_clients/", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_clients():
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])
            try:
                try:
                    profile = jwt.decode(request.headers["token"], key=app_conf.get(
                        "key", "secret_key"), algorithms=["HS256"])

                    print(profile)

                except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError, json.decoder.JSONDecodeError) as e:
                    return jsonify("Token Error")

                columns = []
                out = []
                get_employees_query = f'SELECT * FROM "Client"."Clients" ORDER BY "clientID" ASC'
                print(get_employees_query)
                cur.execute(get_employees_query)
                row = cur.fetchall()
                cols = cur.description
                for col in cols:
                    columns.append(col[0])
                for ele in row:
                    out.append(dict(zip(columns, ele)))
                return jsonify(out)

            except Exception as e:
                return jsonify(e)

    except Exception as e:
        return jsonify(e)


"""
get_employee end point

method: GET

get the information of the employee by id

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_id: the id of the employee

return: a dictionary with all employee information
"""
@app.route("/get_employee/<_id>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_employee(_id):
    try:
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

"""
add_employee end point

method: POST

add the new employee to the database or update the employee if that employee already exist

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
json string: the dictionary contain all required information about the employee want to add or update

return: the message of the action of the end point
"""
@app.route("/add_employee/", methods=["POST"])
@cross_origin(support_credentials=True)
def add_employee():
    try:
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

            info = request.get_json()

            postgres_employee_search = f"""SELECT "employeeID" FROM "Employee"."Employees" WHERE email='{info["email"]}' OR name='{info["name"]}';"""

            cur.execute(postgres_employee_search)

            row = cur.fetchone()

            print(row)

            if row:

                postgres_employee_update = """UPDATE "Employee"."Employees" SET name=%s, email=%s, password = crypt(%s, gen_salt('md5')), "isAdmin"=%s WHERE "employeeID" = %s;"""

                cur.execute(postgres_employee_update,
                            (info["name"], info["email"], info["password"], info["isAdmin"], row[0]))

                conn.commit()

                return jsonify(f"Employee {info['name']} is updated")

            else:

                postgres_employee_query = """INSERT INTO "Employee"."Employees"(name, email, password, "isAdmin") VALUES (%s, %s, crypt(%s, gen_salt('md5')),%s)"""

                cur.execute(postgres_employee_query,
                            (info["name"], info["email"], info["password"], info["isAdmin"]))

                conn.commit()

                return jsonify("New employee added")

    except Exception as e:
        return jsonify(e)

"""
get_all_jobs end point

method: GET

get the all the jobs from a specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_start_date: the first day of the job
_end_date: the last day of the job

return: the list of jobs information
"""
@app.route("/get_all_jobs/<_start_date>/<_end_date>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_jobs(_start_date, _end_date):
    try:
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

            columns = []
            postgres_jobs_query = f'''SELECT "jobID", "clientID", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs" WHERE "dateStart" BETWEEN '{_start_date}' AND '{_end_date}';'''
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

"""
get_jobs end point

method: GET

get the information about the jobs of an employee

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the id of an employee
_start_date: the first day of the job
_end_date: the last day of the job
_completed: the completion status of the job

return: the list of jobs information
"""
@app.route("/get_jobs/<_employee_id>/<_start_date>/<_end_date>/<_completed>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_jobs(_employee_id, _start_date, _end_date, _completed):
    try:
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
            columns = []

            if not _completed or _completed == "None":
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID" WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateStart" BETWEEN '{_start_date}' AND '{_end_date}';'''

            else:
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
    INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
    INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID" WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateStart" BETWEEN '{_start_date}' AND '{_end_date}' AND "isCompleted"={_completed};'''
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

"""
delete_jobs end point

method: POST

delete jobs from specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_start_date: the first day of the job
_end_date: the last day of the job

return: the message of the action
"""
@app.route("/delete_jobs/<_start_date>/<_end_date>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_jobs(_start_date, _end_date):
    try:
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

            postgres_employee_query = f'''DELETE FROM "Job"."Jobs" WHERE  "dateStart" BETWEEN '{_start_date}' AND '{_end_date}' '''
            cur.execute(postgres_employee_query)
            conn.commit()
            count = cur.rowcount
            print(count)
            return jsonify("JOB DELETED")

    except Exception as e:
        return jsonify(e)

"""
assign_job end point

method: POST

assign a job to specific employee

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_client_id: the id of the client
_employee_id: the id of the employee
json string: the dictionary contains all required information of the job

return: the message of the action
"""
@app.route("/assign_job/<_client_id>/<_employee_id>", methods=["POST"])
@cross_origin(support_credentials=True)
def assign_job(_client_id, _employee_id):
    try:
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

            content_type = request.headers.get('Content-Type')

            if (content_type == 'application/json'):
                # print("sad")
                """
                "description" text,
                "dateStart" date,
                "dateEnd" date,
                """
                info = request.get_json()

                dateStart = info["dateStart"]
                dateEnd = info["dateEnd"]
                description = info["description"]
                isCompleted = False

                postgres_job_query = f'''INSERT INTO "Job"."Jobs" ("clientID", description, "dateStart", "dateEnd", "isCompleted") VALUES (%s, %s, %s, %s, %s) RETURNING "jobID";'''

                cur.execute(postgres_job_query, (_client_id,
                            description, dateStart, dateEnd, isCompleted))

                conn.commit()

                row = cur.fetchone()

                postgres_employee_job_query = f'''INSERT INTO "EmployeeJob"."EmployeeJobs" ("employeeID", "jobID") VALUES (%s, %s);'''

                cur.execute(postgres_employee_job_query,
                            (_employee_id, row[0]))

                conn.commit()

                return jsonify("Job Added")

            else:
                return jsonify("Please include a JSON body")

    except Exception as e:
        return jsonify(e)

"""
delete_employee end point

method: POST

delete an employee from the database

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_id: the employee id

return: the message of the action
"""
@app.route("/delete_employee/<_id>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_employee(_id):
    try:
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

            postgres_employee_query = f'DELETE FROM "Employee"."Employees" WHERE "employeeID" = {_id}'
            cur.execute(postgres_employee_query)
            conn.commit()
            count = cur.rowcount
            print(count)
            return jsonify("EMPLOYEE DELETED")

    except Exception as e:
        return jsonify(e)

"""
generate_tech_income_sheet end point

method: POST, OPTIONS

generate an income sheet that contains income information for an employee with specific invoice

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the employee id
invoice_id: the id of the invoice that the employee want to report income
json string: the dicionary contains all information about the income detail

return: the message of the action
"""
@app.route("/generate_tech_income_sheet/<_employee_id>/<invoice_id>", methods=["POST", "OPTIONS"])
@cross_origin(support_credentials=True)
def generate_tech_income_sheet(_employee_id, invoice_id):
    """
    json={
        total:num,
        my_part:num,
        labor:num,
        tax:num,
        shipping:num,
        net:num,
        part_installed:string,
        client_sell:num,
        paid_by:string,
        datecreated:date,
    }
    """
    try:
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

            if not request.get_json():

                return jsonify("Please include income information")

            else:

                info = request.get_json()

                insert_income_query = '''INSERT INTO "Invoice"."TechIncome"("invoiceID",total, my_part, labor, tax, shipping, net, part_installed, client_sell, datecreated, paid_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

                cur.execute(insert_income_query, (invoice_id, info["total"], info["my_part"], info["labor"], info["tax"],
                            info["shipping"], info["net"], info["part_installed"], info["client_sell"], info["datecreated"], info["paid_by"]))

                conn.commit()

                insert_employee_invoice = '''INSERT INTO "EmployeeInvoice"."EmployeeInvoices"("employeeID", "invoiceID") VALUES (%s, %s);'''

                cur.execute(insert_employee_invoice,
                            (_employee_id, invoice_id))

                conn.commit()

                return jsonify("Add New Income Sheet")

    except Exception as ex:
        return jsonify(ex)

"""
get_tech_income_sheet end point

method: GET

get the information of the income with specific timestamp of an employee

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the employee id
day_start: the first day that we want to search
day_end: the last day that we want to search

return: the list of income sheet for that employee
"""
@app.route("/get_tech_income_sheet/<_employee_id>/<day_start>/<day_end>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_tech_income_sheet(_employee_id, day_start, day_end):
    try:
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

            get_income_query = '''SELECT "EmployeeInvoices"."employeeID", "EmployeeInvoices"."invoiceID", "TechIncome".net,
    "TechIncome".total, "TechIncome".datecreated, "TechIncome".labor,"TechIncome".my_part,
	"TechIncome".part_installed, "TechIncome".tax,"TechIncome".shipping, "TechIncome".client_sell,
	"TechIncome".paid_by
	FROM "EmployeeInvoice"."EmployeeInvoices"
	INNER JOIN "Invoice"."TechIncome"
	ON "TechIncome"."invoiceID" = "EmployeeInvoices"."invoiceID"
	WHERE "employeeID" = %s AND "TechIncome".datecreated BETWEEN %s AND %s ORDER BY "TechIncome".datecreated DESC;'''

            cur.execute(get_income_query,
                        (int(_employee_id), day_start, day_end))

            columns = []
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

"""
get_all_jobs_withoutdate end point

method: GET

get all jobs 

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
none

return: the list of all the jobs
"""
@app.route("/get_all_jobs_withoutdate", methods=["GET"])
@cross_origin(support_credentials=True)
def get_all_jobs_withoutdate():
    try:
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

            columns = []
            postgres_jobs_query = f'''SELECT "jobID", "clientID", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs";'''
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

"""
generate_invoice end point

method: POST

generate and send the invoice from the finished job

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
json string: a dictionary that contain all information about the job and related details.

return: the message of the action
"""
@app.route("/generate_invoice", methods=["POST"])
@cross_origin(support_credentials=True)
def generate_invoice():
    try:
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

            if not request.get_json():

                return jsonify("Please include income information")

            else:
                """
                Object {
                    "all_work_cod": "54",
                    "authorization_number": "3584",
                    "balance_due": "87884",
                    "card_number": "575",
                    "card_type": "Visa",
                    "city": "Long Beach",
                    "customer_complaint": "Complaining ",
                    "customer_name": "Name",
                    "cvc": "67548",
                    "date": "10/11/2022",
                    "deposit": "678",
                    "email_address": "email@email.com",
                    "exp_date": "6754",
                    "invoice_number": 5546888,
                    "item_to_be_serviced": "warranty",
                    "job_estimate": "10.78",
                    "labor": "491",
                    "labor_warranty": "Warranty",
                    "make": "makehsvd",
                    "material_costs": "10.75",
                    "material_warranty": "warranty",
                    "model_no": "kahevjd",
                    "part_rows": Array [
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "kahrb",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "sheba",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "bdvdb",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "ndhdb",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "bch be",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "jahvrbxjdu ",
                        },
                        Object {
                        "cost": "0",
                        "quantity": "3",
                        "part_material": "jshbrb",
                        },
                    ],
                    "phone": "5484",
                    "pick_up_delivery": "9484",
                    "serial_no": "msnbf",
                    "service_call": "64",
                    "street": "S Daisy",
                    "tax": "10",
                    "tech_name": "Geo",
                    "tech_report": "nah f",
                    "work_order_number": "6542884",
                    "Signature": ”client name”
                    }
                """

                info = request.get_json()

                # print(info)

                html_string = ""

                with open('templates\invoices.html', "r") as f:
                    html_string = f.read()

                html_string = html_string.replace(
                    "{invoice_number}", str(info["invoice_number"])).replace(
                    "{customer}", str(info["customer_name"])).replace(
                    "{date}", str(info["date"])).replace(
                    "{phone}", str(info["phone"])).replace(
                    "{street}", str(info["street"])).replace(
                    "{city}", str(info["city"])).replace(
                    "{labor_warranty}", str(info["labor_warranty"])).replace(
                    "{material_warranty}", str(info["material_warranty"])).replace(
                    "{item_service}", str(info["item_to_be_serviced"])).replace(
                    "{make}", str(info["make"])).replace(
                    "{model}", str(info["model_no"])).replace(
                    "{serial}", str(info["serial_no"])).replace(
                    "{customer_complaint}", str(info["customer_complaint"])).replace(
                    "{email}", str(info["email_address"])).replace(
                    "{work_order}", str(info["work_order_number"])).replace(
                    "{authorization}", str(info["authorization_number"])).replace(
                    "{job_estimate}", str(info["job_estimate"])).replace(
                    "{tech_name}", str(info["tech_name"])).replace(
                    "{material}", str(info["material_costs"])).replace(
                    "{tax}", str(info["tax"])).replace(
                    "{service_call}", str(info["service_call"])).replace(
                    "{labor}", str(info["labor"])).replace(
                    "{deposit}", str(info["deposit"])).replace(
                    "{delivery}", str(info["pick_up_delivery"])).replace(
                    "{cod}", str(info["all_work_cod"])).replace(
                    "{balance_due}", str(info["balance_due"])).replace(
                    "{report}", str(info["tech_report"])).replace(
                    "{card_number}", str(info["card_number"])).replace(
                    "{exp_date}", str(info["exp_date"])).replace(
                    "{cvc}", str(info["cvc"]))

                parts = list(filter(None, info["part_rows"]))

                print(parts)

                while len(parts) < 7:
                    parts.append(
                        {"cost": "", "quantity": "", "part_material": ""})

                for i in range(len(parts)):
                    html_string = html_string.replace(
                        "{q"+str(i)+"}", parts[i]["quantity"]).replace(
                        "{p"+str(i)+"}", parts[i]["part_material"]).replace(
                        "{c"+str(i)+"}", parts[i]["cost"])

                is_signed = False

                signature = ""

                if "signature" in info:

                    html_string = html_string.replace(
                        "{signature}", info["signature"])

                    signature = info["signature"]

                    is_signed = True

                else:

                    html_string = html_string.replace(
                        "{signature}", " Not Signed Yet")

                if info["card_type"] == "Visa":
                    html_string = html_string.replace("{visa}", "checked")
                elif info["card_type"] == "Mastercard":
                    html_string = html_string.replace("{mc}", "checked")
                elif info["card_type"] == "AMEX":
                    html_string = html_string.replace("{amex}", "checked")
                elif info["card_type"] == "Discover":
                    html_string = html_string.replace("{disc}", "checked")

                with open(f'templates\invoices_{info["invoice_number"]}.html', "w") as wf:
                    wf.write(html_string)

                with open(f'internal_invoices\invoice_{info["invoice_number"]}.pdf', 'w') as outf:
                    outf.write("")

                try:
                    pdf.from_file(f'templates\invoices_{info["invoice_number"]}.html',
                                  f'internal_invoices\invoice_{info["invoice_number"]}.pdf')

                except Exception as ex:
                    print(ex)

                invoice_insert_query = """INSERT INTO "Invoice"."ClientInvoice"(
	"invoiceID", customer, created_date, phone, street, city, labor_warranty, material_warranty, serviced_item, make, model, serial_number, customer_complaint, email, work_order, auth_num, job_est, tech_name, q_table, tech_report, check_type, card_number, exp_date, cvc, is_signed, signature)
	VALUES (%s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'), %s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), %s, %s, %s, %s, %s, %s, %s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), %s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'), %s, %s, %s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), PGP_SYM_ENCRYPT(%s, 'AES_KEY'), %s, PGP_SYM_ENCRYPT(%s, 'AES_KEY'));"""

                cur.execute(invoice_insert_query, (info["invoice_number"], info["customer_name"],
                info["date"], info["phone"], info["street"], info["city"], info["labor_warranty"], info["material_warranty"],
                info["item_to_be_serviced"], info["make"], info["model_no"], info["serial_no"], info["customer_complaint"],
                info["email_address"], info["work_order_number"], info["authorization_number"], info["job_estimate"], info["tech_name"],
                json.dumps(info["part_rows"]), info["tech_report"], info["card_type"], info["card_number"], info["exp_date"], info["cvc"], is_signed, signature))

                conn.commit()

                try:
                    
                    send_mail(send_to=[info["email_address"]],text="This is a copy of the invoice.",subject=f"Invoice {info['invoice_number']} From Royal Appliance Service",files=[f"internal_invoices\invoice_{info['invoice_number']}.pdf"])
                    pass
                except Exception as ex:
                    print(ex)

                return jsonify(f"Invoice {info['invoice_number']} Is Generated")

    except Exception as e:
        return jsonify(e)

"""
sign_invoice end point

method: POST

for the client to sign an invoice

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
invoiceID: the id of the invoice
signature: the string signature

return: the message of the action
"""
@app.route("/sign_invoice/<invoiceID>/<signature>", methods=["POST"])
@cross_origin(support_credentials=True)
def sign_invoice(invoiceID, signature):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get(
                    "key", "secret_key"), algorithms=["HS256"])

                print(profile)
            except Exception as e:
                return jsonify(e)

            sign_query = """UPDATE "Invoice"."ClientInvoice" SET  is_signed=%s, signature=crypt(%s, gen_salt('md5')) WHERE "invoiceID" = %s;"""

            cur.execute(sign_query, (True, signature, invoiceID))

            conn.commit()

            html_string = ""

            with open(f'templates\invoices_{invoiceID}.html', "r") as f:
                html_string = f.read()

                html_string = html_string.replace("Not Signed Yet", signature)
            
            with open(f'templates\invoices_{invoiceID}.html', "w") as wf:
                wf.write(html_string)

            try:

                pdf.from_file(f'templates\invoices_{invoiceID}.html',
                                  f'internal_invoices\invoice_{invoiceID}.pdf')

            except Exception as ex:
                print(ex)

            return jsonify("ok")

    except Exception as e:
        return jsonify(e)

"""
delete_invoice end point

method: POST

delete a specific invoice with an id

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
invoiceID: the id of the invoice

return: the message of the action
"""
@app.route("/delete_invoice/<invoiceID>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_invoice(invoiceID):
    import os

    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get(
                    "key", "secret_key"), algorithms=["HS256"])

                print(profile)
            except Exception as e:
                return jsonify(e)

            delete_query = f"""DELETE FROM "Invoice"."ClientInvoice" WHERE "invoiceID" = {invoiceID};"""

            cur.execute(delete_query)

            conn.commit()

            os.remove(f'templates\invoices_{invoiceID}.html')

            os.remove(f'internal_invoices\invoice_{invoiceID}.pdf')

            return jsonify(f"Invoice {invoiceID} Is Deleted")

    except Exception as e:
        return jsonify(e)

"""
delete_invoices end point

method: POST

delete invoices with specific time stamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
start_date: the first day to delete
end_date: the last day to delete

return: the message of the action
"""
@app.route("/delete_invoices/<start_date>/<end_date>", methods=["POST"])
@cross_origin(support_credentials=True)
def delete_invoices(start_date,end_date):
    import os

    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get(
                    "key", "secret_key"), algorithms=["HS256"])

                print(profile)
            except Exception as e:
                return jsonify(e)

            select_query = f"""SELECT "invoiceID" FROM "Invoice"."ClientInvoice" WHERE created_date BETWEEN '{start_date}' AND '{end_date}';"""

            cur.execute(select_query)

            rows = cur.fetchall()

            delete_query = f"""DELETE FROM "Invoice"."ClientInvoice" WHERE created_date BETWEEN '{start_date}' AND '{end_date}';"""

            cur.execute(delete_query)

            conn.commit()

            for id in rows:

                os.remove(f'templates\invoices_{id[0]}.html')

                os.remove(f'internal_invoices\invoice_{id[0]}.pdf')

            return jsonify(f"Invoices From {start_date} To {end_date}  Are Deleted")

    except Exception as e:
        return jsonify(e)

"""
get_invoice end point

method: GET

get an invoice informaton for specific invoice with specific return type

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
invoiceID: the id of an invoice
return_type: the type that the invoice should be return (pdf or base 64 string)

return: the invoice information or a pdf of the invoice
"""
@app.route("/get_invoice/<invoiceID>/<return_type>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_invoice(invoiceID,return_type):
    import os
    from pdf2image import convert_from_path
    import base64
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get(
                    "key", "secret_key"), algorithms=["HS256"])

                print(profile)
            except Exception as e:
                return jsonify(e)
            if not os.path.exists(f"internal_invoices\invoice_{invoiceID}.pdf"):
                return jsonify(f"The invoice with ID# {invoiceID} does not exist")
            else:
                #print(request.headers)
                if return_type == "base64":

                    images = convert_from_path(pdf_path=f"internal_invoices\invoice_{invoiceID}.pdf",size=(720, 900))

                    for page in images:
                        page.save('temp_img.jpg', 'JPEG')
                    b64_string =""

                    with open("temp_img.jpg", "rb") as img_file:
                        b64_string = base64.b64encode(img_file.read())
                    print("ok")

                    return jsonify(b64_string.decode('ascii'))

                elif return_type == "pdf":
                    return send_file(f"internal_invoices\invoice_{invoiceID}.pdf",as_attachment=False)

    except Exception as e:
        return jsonify(e)

"""
get_invoices_info end point

method: GET

get invoices informaton for specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
start_date: the first day we want to search
end_date: the last day we want to search

return: the invoices information
"""
@app.route("/get_invoices_info/<start_date>/<end_date>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_invoices_info(start_date,end_date):
    try:
        if "token" not in request.headers:
            return jsonify("no token in the header")
        else:
            # print(request.headers["token"])

            try:
                profile = jwt.decode(request.headers["token"], key=app_conf.get(
                    "key", "secret_key"), algorithms=["HS256"])

                print(profile)
            except Exception as e:
                return jsonify(e)

            select_query = f"""SELECT "invoiceID", PGP_SYM_DECRYPT(customer::bytea, 'AES_KEY') as customer, created_date, serviced_item, PGP_SYM_DECRYPT(tech_name::bytea, 'AES_KEY') as tech_name,  is_signed FROM "Invoice"."ClientInvoice" WHERE created_date BETWEEN '{start_date}' AND '{end_date}';"""

            cur.execute(select_query)

            rows = cur.fetchall()

            cols = cur.description

            columns = []

            for col in cols:
                columns.append(col[0])
            out = []

            for row in rows:
                out.append(dict(zip(columns, row)))
            
            return jsonify(out)

    except Exception as e:
        return jsonify(e)

"""
authentication end point

method: POST, OPTIONS

authenticate and assign a token to a login session depend on the user type (admin or normal user)

headers:
none

params:
json_string: contains email and password for the login information

return: the basic information if the user exist with correct password and an authentication token for that sessions
note: the token will expire after logout, and cannot be used again.
"""
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
            token = jwt.encode(payload=info, key=app_conf.get(
                "key", "secret_key"), algorithm="HS256")
            out["name"] = result[1]
            out["email"] = result[2]
            out["isAdmin"] = result[4]
            out["token"] = token
            return jsonify(out)
        else:
            return jsonify(False)

    except Exception as e:
        return jsonify(e)

"""
connection_test end point

method: GET, POST

test authentication to the server

headers:
none

params:
none

return: Rest API is running or error out
"""
@app.route("/connection_test", methods=["GET", "POST"])
@cross_origin(support_credentials=True)
def connection_test():
    return jsonify("Rest API is running")

"""
get_past_jobs end point

method: GET

get past jobs for an employee with specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the employee id
_end_date: the date finish of the job
_completed: the job status

return: list of jobs information
"""
@app.route("/get_past_jobs/<_employee_id>/<_end_date>/<_completed>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_past_jobs(_employee_id, _end_date, _completed):
    try:
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
            columns = []

            if not _completed or _completed == "None":
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID"
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateEnd" < '{_end_date}';'''

            else:
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID" 
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateEnd"  < '{_end_date}' AND "isCompleted"={_completed};'''
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

"""
get_present_jobs end point

method: GET

get current jobs for an employee with specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the employee id
_end_date: the date finish of the job
_completed: the job status

return: list of jobs information
"""
@app.route("/get_present_jobs/<_employee_id>/<_start_date>/<_end_date>/<_completed>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_present_jobs(_employee_id, _start_date, _end_date, _completed):
    try:
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
            columns = []

            if not _completed or _completed == "None":
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID"
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateEnd" > '{_start_date}';'''

            else:
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID" 
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateEnd"  > '{_start_date}' AND "isCompleted"={_completed};'''
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
    
"""
get_future_jobs end point

method: GET

get future jobs for an employee with specific timestamp

headers:
token: an authentication token to identify if the user is allow to perform this action

params:
_employee_id: the employee id
_end_date: the date finish of the job
_completed: the job status

return: list of jobs information
"""
@app.route("/get_future_jobs/<_employee_id>/<_start_date>/<_completed>", methods=["GET"])
@cross_origin(support_credentials=True)
def get_future_jobs(_employee_id, _start_date, _completed):
    try:
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
            columns = []

            if not _completed or _completed == "None":
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID"
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateStart" > '{_start_date}';'''

            else:
                postgres_jobs_query = f'''SELECT "Jobs"."jobID","Clients"."address","Clients"."name", description, "dateStart", "dateEnd", "isCompleted" FROM "Job"."Jobs"
                INNER JOIN "EmployeeJob"."EmployeeJobs" ON "Jobs"."jobID" = "EmployeeJobs"."jobID"
                INNER JOIN "Client"."Clients" ON "Clients"."clientID"="Jobs"."clientID" 
                WHERE "EmployeeJobs"."employeeID" = {_employee_id} AND "dateStart"  > '{_start_date}' AND "isCompleted"={_completed};'''
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
    
    
# running driver
if __name__ == '__main__':
    #app.run(host="0.0.0.0", port=5020, debug=True)
    serve(app,host="0.0.0.0", port=5020)
