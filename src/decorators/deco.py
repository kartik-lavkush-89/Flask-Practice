import jwt
from functools import wraps
from flask import jsonify,request,g
from app import app
from src.database.models import Table


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token :
            return jsonify({"message" : "Token is  missing or expired."}), 403
        
        try :
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # g.user = Table.query.filter(lname = data['lname']).first()
        except Exception as e :
            return jsonify({
                "message" : f"Token is invalid due to {e}!"
            }),401
        
        return f(*args, **kwargs)
    return decorator
