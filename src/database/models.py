"""""""""""""""""""""""""""""""""""""""""""""""""DATABASE  MODELS"""""""""""""""""""""""""""""""""""""""""""""""""""""""

from app import db
import datetime
from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Table(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String(40), nullable=False)
    lname = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(40), unique =True, nullable=False)
    phone = db.Column(db.String(20), unique=True,nullable = False)
    password = db.Column(db.String(1000), nullable=False)

    def __init__(self,fname,lname,email,phone,password) :
        self.fname = fname
        self.lname = lname
        self.email = email
        self.phone = phone
        self.password = password 

    def to_json(self):
        return {'id': self.id,'fname': self.fname, 'lname': self.lname,'email': self.email,'phone':self.phone , 
                'password':self.password 
                }
        
        with self.app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()

class UserSchema(SQLAlchemyAutoSchema):
    fname = fields.String()
    lname = fields.String()
    email = fields.String()
    phone = fields.String()
 


class Otp(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    phone = db.Column(db.String, nullable = False)
    otp = db.Column(db.String(20), nullable = False)  
    expiry = db.Column(db.TIMESTAMP(timezone=True))
    created_at = db.Column(db.TIMESTAMP(timezone = True),default = datetime.datetime.utcnow())

    def __init__(self,phone,otp) :
        self.phone = phone
        self.otp = otp
    
    def to_json(self):
        return {'phone': self.phone,'otp':self.otp}

        with self.app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()

class OtpSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Otp



class Email(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(40), nullable = False)
    otp = db.Column(db.String(20), nullable = False) 

    def __init__(self,email,otp) :
        self.email = email
        self.otp = otp

    def to_json(self):
        return {'email': self.email,'otp':self.otp}
        

               