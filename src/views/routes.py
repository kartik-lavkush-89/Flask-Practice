"""""""""""""""""""""""""""""""""""""""""""""""""ROUTES"""""""""""""""""""""""""""""""""""""""""""""""""""""""

from app import app, celery, cache
from flask import jsonify,request,Blueprint,render_template,make_response,g
from flask.views import MethodView
from src.database.models import Table,UserSchema,db,Otp,Email
from src.celery.celery_functions import send_otp, send_mail, make_pdf, add_together, delete_expired_otp
from werkzeug.security import generate_password_hash,check_password_hash
import jwt
import datetime
import random
from src.decorators.deco import token_required
import pdfkit


app1 = Blueprint("app1", __name__)



"""Testing Celery task"""
@app1.route('/test-celery')
def test(): 
    add_together.delay(2,5)
    return 'Test Celery'


"""Sending OTP to verify user's phonr number at the time of Registration"""
class Sendotp(MethodView) :
    
    def post(self):
        phone = request.json.get('phone')
        otp = random.randrange(000000,999999)
        user = Table.query.filter(Table.phone == phone).first()
        if not user:
            send_otp.delay(phone,otp)
            print(otp)
            code = Otp(phone = phone,otp = otp)
            db.session.add(code)
            db.session.commit()
            return jsonify({"Message" : "Otp sent to your phone number!"}), 200
        else :
            return jsonify({"Message" : "User with given phone no. is already registered."}), 208

app1.add_url_rule('/sendotp', view_func=Sendotp.as_view('sendotp'))



"""Sending OTP to user email id to reset password"""
class Verifymail(MethodView) :

    def post(self):
        otp = random.randrange(000000,999999)
        email = request.json.get('email')
        emailfound = Table.query.filter(Table.email == email).first()
        if emailfound:
            send_mail.delay(email,otp)
            print(otp)
            code = Email(email = email,otp = otp)
            db.session.add(code)
            db.session.commit()
            return jsonify({"message" : "OTP sent to your Email ID!"}), 200
        else :
            return jsonify({"message" : "Invalid Email / User doesn't exist!"}), 404

app1.add_url_rule('/verifymail', view_func=Verifymail.as_view('verifymail'))


"""Creating PDF of user details stored at the time of registration"""
class Pdf(MethodView) : 

    @token_required
    def get(self):
        result = UserSchema().dump(g.user)
        pdf = pdfkit.from_string(render_template('index.html',result = result),f'D:\Flask Practice\one_more_generated_pdf/{f"info_{str(random.randrange(000000,999999))}.pdf"}',configuration= pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"))
        make_pdf.delay(result,pdf)
        return jsonify({"Message" : "PDF created"})

app1.add_url_rule('/pdf', view_func=Pdf.as_view('/pdf'))


"""Deleting expired OTPs"""
class Delete(MethodView):

    def delete(self):
        delete_expired_otp.delay()
        return jsonify({'Success': "All Expiry OTPs deleted!"}), 200
    
app1.add_url_rule('/deleteotp', view_func=Delete.as_view('deleteotp'))



"""REGISTER  Route"""
class Register(MethodView) :


    """Getting Uesr profile"""
    @token_required
    def get(self):
        result = UserSchema().dump(g.user)
        return jsonify({"User" : result}), 200


    """Registration of new users"""
    def post(self) :
        body = request.get_json()
        fname, lname, email, phone = body.get('fname'), body.get('lname'), body.get('email'), body.get('phone')
        otp = body.get('otp')
        pwd = body.get('password')
        if 'fname'  not in body :
            return jsonify({"Message" : "Ensure to fill all required details including your Fname, Lname, Email, Phone, OTP, Password and Confirm Password!"}), 400
        elif 'lname' not in body :
            return jsonify({"Message" : "Lname is missing!"}), 400
        elif 'email' not in body :
            return jsonify({"message" : "Email is required!"}), 400 
        elif 'phone' not in body :
            return jsonify({"Message" : "Phone number is required!"}), 400
        elif 'otp' not in body :
            return jsonify({"Message" : "OTP is required!"}), 400
        elif 'password' not in body :
            return jsonify({"Message" : "Password is required to complete the registration process!"}), 400 
        elif 'confirm_password' not in body :
            return jsonify({"Message" : "Confirm_Password field can't be empty!"}), 400
        

        elif 'fname' in body and 'lname' in body and 'email' in body and 'phone' in body and 'otp'in body and 'password' in body and 'confirm_password' in body : 
            phonefoundwithotp = Otp.query.filter(Otp.phone==phone).first()
            emailfound = Table.query.filter(Table.email == email).first()
            phonefound = Table.query.filter(Table.phone == phone).first()

            if not body['confirm_password'] == body['password'] :
                return jsonify({"Message" : "Password not match!"}), 400
            elif emailfound :
                return jsonify({"Message" : "Email ID already registered, try with another Email."}), 208
            elif phonefound:
                return jsonify({"Message" : "Phone number already registered."}), 208
             
            elif phonefoundwithotp:
                if phonefoundwithotp.otp == otp:
                    data = Table(fname = fname,lname = lname,email = email,phone = phone,password = generate_password_hash(pwd))
                    db.session.add(data)
                    db.session.commit()
                    return jsonify({"Message" : "You are now registererd on the website!"}), 201
                else :
                    return jsonify({"Error" : "Inavlid OTP!"}), 406
            else :
                return jsonify({"Message" : "Go to sendotp route to recieve OTP on your number."}), 401

    

    """Deleting single user data"""
    @token_required
    def delete(self):
        id = request.headers.get('id')
        user = Table.query.filter(Table.id == id).first() 
        if user :
            db.session.delete(user)
            db.session.commit()
            return jsonify({"Message" : "Your data is removed successfully"}), 200
        else :
            return jsonify({"Message" : "Record doesn't exist!"}), 404

app1.add_url_rule('/register', view_func=Register.as_view('register'))


"""LOGIN  Route"""
class Login(MethodView) :


    """Getting whole data stored in database model"""
    @token_required
    def get(self):
        users = []
        a = Table.query.all()
        for user in a:
            del user.__dict__['_sa_instance_state']
            users.append(user.__dict__)
        return jsonify(users), 200


    """LOGIN user with email id and password and token generation"""
    def post(self) :
            body = request.json
            if not body.get('email') and not body.get('password') :
                return jsonify({"Message" : "Required Login Credentials!"}), 400
                
            user=Table.query.filter(Table.email == body.get('email')).first()
            if not user:
                return jsonify({"Error" : "User doesn't exist!"}), 404
                
            elif body.get('password'):
                if check_password_hash(user.password, body.get('password')):   
                    token = jwt.encode({'id' : user.email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], 'HS256')
                    return make_response (jsonify({"Message" : "You are logged in Successfully!", "token" : token})), 200
                else :
                    return jsonify({"Error" : "Wrong passsword!"}), 401
            else:
                return jsonify({'Error':'Required Password!!'})

app1.add_url_rule('/login', view_func=Login.as_view('login'))



"""Forgot Password Route"""
class Forgot(MethodView):


    """Reset passowrd with the help of OTP recieved on user's Email ID"""
    def post(self):
        body = request.get_json()
        email  = body.get('email')
        otp = body.get('otp')
        pwd = body.get('password')
        if 'email' not in body :
            return jsonify({"Message" : "Enter your Email, OTP, Password to reset your old password!"}), 400
        elif 'password' not in body :
                return jsonify({"Message" : "Enter new password to reset your old one!"}), 400
        elif 'otp' not in body :
                return jsonify({"Message" : "Enter otp to reset your password!"}), 400
        else :
              user=Table.query.filter(Table.email == email).first()
              if user :
                    sendotp = Email.query.filter(Email.email==email).first()
                    if sendotp :
                        if sendotp.otp == otp :
                            password = generate_password_hash(pwd)
                            Table.query.filter(Table.email == email).update(dict(password = password))
                            db.session.commit()
                            return jsonify({"Message" : "Password updated successfully."}), 202
                        else :
                            return jsonify({"Error" : "Inavlid OTP!"}), 406
                    else :
                        return  jsonify({"Message" : "Did you recived OTP on your mail, if not then go to verify-mail route."}), 401
              else :
                    return jsonify({"Error" : "Record doesn't exist!"}), 404

app1.add_url_rule('/forgot', view_func=Forgot.as_view('forgot'))


"""CACHING"""
@app1.route('/cache-demo')
@cache.cached(timeout=5)
def cacheDemo():
    randnom =random.randrange(0000,9999)
    return jsonify({'The Number is ': randnom}), 200

class Getinfo(MethodView) :

    @cache.cached(timeout=5)
    def get(self):
        users = Table.query.all()
        rand_user = random.choice(users)
        result = UserSchema().dump(rand_user)
        return jsonify({'users': result}), 200

app1.add_url_rule('/getinfo', view_func=Getinfo.as_view('getinfo'))