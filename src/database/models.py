from app import db
from marshmallow import Schema, fields

class Table(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(40), nullable=False)
    lname = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    phone = db.Column(db.String(20), nullable = False)
    password = db.Column(db.String(1000), nullable=False)

    def __init__(self,fname,lname,email,phone,password) :
        self.fname = fname
        self.lname = lname
        self.email = email
        self.phone = phone
        self.password = password  

       
class UserSchema(Schema):
    fname = fields.String()
    lname = fields.String()
    email = fields.String()
    phone = fields.String()

class Otp(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    phone = db.Column(db.String, nullable = False)
    otp = db.Column(db.String(20), nullable = False)  

    def __init__(self,phone,otp) :
        self.phone = phone
        self.otp = otp
    
    def to_json(self):
        return {'phone': self.phone,'otp':self.otp}

        with self.app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()

class Email(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(40), nullable = False)
    otp = db.Column(db.String(20), nullable = False) 

    def __init__(self,email,otp) :
        self.email = email
        self.otp = otp

    def to_json(self):
        return {'email': self.email,'otp':self.otp}
        

               