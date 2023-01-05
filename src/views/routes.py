from app import app, celery
from flask import jsonify,request,session,redirect,url_for,Blueprint,render_template,make_response,g
from flask.views import MethodView
from src.database.models import Table,UserSchema,db,Otp,Email
from werkzeug.security import generate_password_hash,check_password_hash
import jwt
import datetime
import uuid
from twilio.rest import Client
import random
from src.decorators.deco import token_required
from sendgrid import SendGridAPIClient 
from sendgrid.helpers.mail import Mail
import os
import pdfkit


app1 = Blueprint("app1", __name__)

@celery.task(name='app.add_together')
def add_together(a, b):
    print('In Celery TAsk')
    return a + b

@app1.route('/test-celery')
def test():
    add_together.delay(2,5)
    return 'Test Celery'




@app1.route('/', methods=['GET','POST'])
def welcome():
    #return redirect(url_for('app1.register'))
    return jsonify({"message" : "Welcome, This is the registration portal. To sign up please hover to register route."}), 200



class sendotp(MethodView) :
    
    def post(self):
        phone = request.json.get('phone')
        otp = random.randrange(100000,999999)
        user = Table.query.filter(Table.phone == phone).first()
        if not user:
            send_sms.delay(phone,otp)
            code = Otp(phone = phone,otp = otp)
            db.session.add(code)
            db.session.commit()
            return jsonify({"message" : "Otp sent to your phone number!"}), 200
        else :
            return jsonify({"message" : "User with given phone no. is already registered."}), 208

app1.add_url_rule('/sendotp', view_func=sendotp.as_view('sendotp'))

@celery.task(name='app.send_sms')
def send_sms(phone,otp):

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
                    body="Hello! Your otp for registration is - " + str(otp),
                    from_=os.getenv('TWILIO_NUMBER'),
                    to ='+91' + str(phone)
                )

@celery.task(name='app.send_mail')
def send_mail(email,otp):
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    message = Mail(
                    from_email=os.getenv('DEFAULT_SENDER_ID'),
                    to_emails= email,
                    subject='OTP Verification Code ',
                    html_content = "Your OTP for reset password - " + str(otp)
                    )
            
    session['response'] = str(otp)
    sg.send(message)



class verifymail(MethodView) :

    def post(self):
        otp = random.randrange(000000,999999)
        email = request.json.get('email')
        emailfound = Table.query.filter(Table.email == email).first()
        if emailfound:
            send_mail.delay(email,otp)
            print(otp)
            # print(message)
            code = Email(email = email,otp = otp)
            db.session.add(code)
            db.session.commit()
            return jsonify({"message" : "OTP sent to your Email ID!"}), 200
        else :
            return jsonify({"message" : "Invalid Email / User doesn't exist!"}), 404

app1.add_url_rule('/verifymail', view_func=verifymail.as_view('verifymail'))


@app.route('/pdf', methods = ['POST'])
# @token_required
def userData():
    fname = request.json.get('fname')
    users = Table.query.filter(Table.fname==fname).first()
    if users :
        result = UserSchema().dump(users)
        print(result)
        path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        random_no = random.randrange(000000,999999)
        file_name = f"info_{str(random_no)}.pdf"
        
        html = render_template('index.html',result = result)
        
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        save_pdf = f'D:\one more pdf/{file_name}'
        pdf = pdfkit.from_string(html,save_pdf,configuration=config)
        
        print (pdf)
        return jsonify({"message" : "PDF Created!"})
    else :
        return jsonify({"message" : "User doesn,t exist!"}), 404 


class Register(MethodView) :

    @token_required
    def get(self):
        id = request.headers.get('id')
        data = Table.query.get(id)
        result = UserSchema().dump(data)
        return jsonify({"users" : result}), 200

    def post(self) :
        body = request.get_json()
        fname, lname, email, phone = body.get('fname'), body.get('lname'), body.get('email'), body.get('phone')
        otp = body.get('otp')
        pwd = body.get('password')
        if 'fname'  not in body :
            return jsonify({"message" : "Ensure to fill all required details including your Fname, Lname, Email, Phone, OTP, Password and Confirm Password!"}), 400
        elif 'lname' not in body :
            return jsonify({"message" : "Lname is missing!"}), 400
        elif 'email' not in body :
            return jsonify({"message" : "Email is required!"}), 400 
        elif 'phone' not in body :
            return jsonify({"message" : "Phone number is required!"}), 400
        elif 'otp' not in body :
            return jsonify({"message" : "OTP is required!"}), 400
        elif 'password' not in body :
            return jsonify({"message" : "Password is required to complete the registration process!"}), 400 
        elif 'confirm_password' not in body :
            return jsonify({"message" : "Confirm_Password field can't be empty!"}), 400
        

        elif 'fname' in body and 'lname' in body and 'email' in body and 'phone' in body and 'otp'in body and 'password' in body and 'confirm_password' in body : 
            phonefoundwithotp = Otp.query.filter(Otp.phone==phone).first()
            emailfound = Table.query.filter(Table.email == email).first()
            phonefound = Table.query.filter(Table.phone == phone).first()

            if not body['confirm_password'] == body['password'] :
                return jsonify({"message" : "Password not match!"}), 400
            elif emailfound :
                return jsonify({"message" : "Email ID already registered, try with another Email."}), 208
            elif phonefound:
                return jsonify({"message" : "Phone number already registered."}), 208
             
            elif phonefoundwithotp:
                if phonefoundwithotp.otp == otp:
                    data = Table(fname = fname,lname = lname,email = email,phone = phone,password = generate_password_hash(pwd))
                    db.session.add(data)
                    db.session.commit()
                    return jsonify({"message" : "You are now registererd on the website!"}), 201
                else :
                    return jsonify({"message" : "Inavlid OTP!"}), 406
            else :
                return jsonify({"message" : "Go to sendotp route to recieve OTP on your number."}), 401

    def put(self):
        return jsonify({"message" : "Method not allowed!"}), 405

    @token_required
    def delete(self):
        id = request.headers.get('id')
        user = Table.query.filter(Table.id == id).first() 
        if user :
            db.session.delete(user)
            db.session.commit()
            return jsonify({"message" : "Your data is removed successfully"}), 200
        else :
            return jsonify({"message" : "Record doesn't exist!"}), 404

app1.add_url_rule('/register', view_func=Register.as_view('register'))

class Login(MethodView) :

    @token_required
    def get(self):
        users = []
        a = Table.query.all()
        for user in a:
            del user.__dict__['_sa_instance_state']
            users.append(user.__dict__)
        return jsonify(users), 200

    def post(self) :
            body = request.json
            if not body.get('email') and not body.get('password') :
                return jsonify({"message" : "Required Login Credentials!"}), 400
                
            user=Table.query.filter(Table.email == body.get('email')).first()
            if not user:
                return jsonify({"message" : "User doesn't exist!"}), 404
                
            elif body.get('password'):
                if check_password_hash(user.password, body.get('password')):   
                    token = jwt.encode({'id' : user.email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], 'HS256')
                    return make_response (jsonify({"message" : "You are logged in Successfully!", "token" : token})), 200
                else :
                    return jsonify({"message" : "Wrong passsword!"}), 401
            else:
                return jsonify({'Error':'Required Password!!'})
        
                

    def put(self):
            return jsonify({"message" : "Method not allowed!"}), 405

    def delete(self):
            return jsonify({"message" : "Method not allowed!"}), 405

app1.add_url_rule('/login', view_func=Login.as_view('login'))

class forgot(MethodView):

    def get(self):
            return jsonify({"message" : "Method not allowed!"}), 405

    # @token_required
    def post(self):
        body = request.get_json()
        email  = body.get('email')
        otp = body.get('otp')
        pwd = body.get('password')
        if 'email' not in body :
            return jsonify({"message" : "Enter your Email, OTP, Password to reset your old password!"}), 400
        elif 'password' not in body :
                return jsonify({"message" : "Enter new password to reset your old one!"}), 400
        elif 'otp' not in body :
                return jsonify({"message" : "Enter otp to reset your password!"}), 400
        else :
              user=Table.query.filter(Table.email == email).first()
              if user :
                    sendotp = Email.query.filter(Email.email==email).first()
                    if sendotp :
                        if sendotp.otp == otp :
                            password = generate_password_hash(pwd)
                            Table.query.filter(Table.email == email).update(dict(password = password))
                            db.session.commit()
                            return jsonify({"message" : "Password updated successfully."}), 202
                        else :
                            return jsonify({"message" : "Inavlid OTP!"}), 406
                    else :
                        return  jsonify({"message" : "Did you recived OTP on your mail, if not then go to verify-mail route."}), 401
              else :
                    return jsonify({"message" : "Record doesn't exist!"}), 404
    
    def put(self):
            return jsonify({"message" : "Method not allowed!"}), 405

    def delete(self):
            return jsonify({"message" : "Method not allowed!"}), 405

app1.add_url_rule('/forgot', view_func=forgot.as_view('forgot'))

class Logout(MethodView) :
    @token_required
    def get(self):
        session.pop('email', None)
        session.pop('passsword', None)
        return redirect(url_for('login'))
    @token_required
    def post(self):
        session.pop('email', None)
        session.pop('passsword', None)
        return redirect(url_for('login'))
    @token_required
    def put(self):
        session.pop('email', None)
        session.pop('passsword', None)
        return redirect(url_for('login'))
    @token_required
    def delete(self):
        session.pop('email', None)
        session.pop('passsword', None)
        return redirect(url_for('login'))

app1.add_url_rule('/logout', view_func=Logout.as_view('logout'))