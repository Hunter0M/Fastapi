from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
from flask_cors import CORS
import sentry_sdk
import jwt
from functools import wraps

from flask_wtf import FlaskForm # pip install flask-wtf
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo,ValidationError

sentry_sdk.init(
    dsn="https://803ae945357ca4dcc17c7ad8d705b95b@o4507805013573632.ingest.us.sentry.io/4507811253977088",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "asdfghjlpoiuytrewqzxcvbnmkjhgfdsa"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0777@localhost/test_api'
db = SQLAlchemy(app)


class Product(db.Model):
    __tablename__='products'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable= False)
    buying_price = db.Column(db.Integer,nullable= False)
    selling_price = db.Column(db.Integer,nullable= False)
    stock_quantity= db.Column(db.Integer,nullable= False)
    sale = db.relationship('Sale',backref='product')


class Sale(db.Model):
    __tablename__ ='sales'
    id = db.Column(db.Integer,primary_key=True)
    pid =db.Column(db.Integer,db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer,nullable= False)
    created_at = db.Column(db.DateTime,server_default = func.now())

class User(db.Model):
    __tablename__= 'users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String,nullable=False)
    user_email = db.Column(db.String,nullable=False)
    user_password = db.Column(db.String,nullable=False)




with app.app_context():
    db.create_all()

CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})


# creating a login route
@app.post('/login')
def login():

    data=request.json
    u=data["username"]
    p=data["password"]

    existing_user = db.session.query(User).filter(User.username==u, User.user_password==p).first()

    if existing_user is None:
        return jsonify({"error":"invalid credentials!"}), 400
    try:

        access_token = jwt.encode({"sub":u, "exp": datetime.utcnow() + timedelta(minutes=30)}, app.config["SECRET_KEY"])

        return jsonify({"message":"user login succesful!","access_token":access_token})

    except Exception as e:
        return jsonify({"error creating access token":e})




@app.route('/user', methods=['POST'])
def create_user():
    try:
        data = request.json
        username = data["username"]
        user_password = data["user_password"]
        user_email = data["user_email"]
        user = User(username=username, user_password=user_password, user_email=user_email)
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_data = []
    for user in users:
        user_data.append({
            "id": user.id,
            "username": user.username,
            "user_password": user.user_password,
            "user_email": user.user_email
        })
    return jsonify({"users": user_data}), 200



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get the token from the Authorization header
        token = request.headers.get("Authorization")

        # Check if the token is missing
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        # Try to decode the token
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        # If the token is valid, call the decorated function
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/product',methods=['GET','POST'])
@token_required
def product(current_user):
    if request.method == 'POST':
        try:
            data = request.json
            name = data['name']
            buying_price = data['buying_price']
            selling_price = data['selling_price']
            stock_quantity = data['stock_quantity']

            product = Product(name=name,buying_price=buying_price,selling_price=selling_price,stock_quantity=stock_quantity)
            db.session.add(product)
            db.session.commit()
            return jsonify({"message":"product added successfully"}),201
        except Exception as e:
            return jsonify({'error':str(e)}),500
    elif request.method == 'GET':
        products = db.session.execute(db.select(Product).order_by(Product.id)).scalars()
        prods =[]
        for product in products:
            prods.append({
                
                "id":product.id,
                "name":product.name,
                "buying_price":product.buying_price,
                "selling_price":product.selling_price,
                "stock_quantity":product.stock_quantity

            })
        return jsonify({"products": prods}) ,200

@app.route('/sales', methods=['GET', 'POST'])
@token_required
def sales(current_user):
    if request.method == 'POST':
        try:
            data = request.json
            pid = data['pid']
            quantity = data['quantity']
            sale = Sale(pid=pid, quantity=quantity)
            db.session.add(sale)
            db.session.commit()
            return jsonify({"message": "Sale made successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == 'GET':
        try:
            sales = Sale.query.order_by(Sale.pid).all()
            sales_data = []
            for sale in sales:
                sales_data.append({
                    'product': sale.pid,
                    'quantity': sale.quantity,
                    'created_at': sale.created_at
                })
            return jsonify({"sales": sales_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/dashboard', methods=['GET'])
# @token_required
def dashboard():
    try:
        sales_per_day = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.sum(Sale.quantity * Product.selling_price).label('sales_per_day')
        ).join(Product).group_by(func.date(Sale.created_at)).all()

        profit_per_day = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.sum((Sale.quantity * Product.selling_price) - (Sale.quantity * Product.buying_price)).label("profit")
        ).join(Product).group_by(func.date(Sale.created_at)).all()

        sales_data = [{'date': str(date), "total_sales": total_sales} for date, total_sales in sales_per_day]
        profit_data = [{'date': str(date), "total_profit": total_profit} for date, total_profit in profit_per_day]

        return jsonify({"sales_data": sales_data, "profit_data": profit_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/login", methods=['POST'])
def login_user():
    data = request.json
    u = data['username']
    p = data['password']
    existing_user = User.query.filter_by(username=u, user_password=p).first()

    if not existing_user:
        return jsonify({"Login failed": "Confirm credentials"}), 401
    try:
        access_token = jwt.encode({"sub": u, "exp": datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({"message": "Login successful", "access_token": access_token})
    except Exception as e:
        return jsonify({"error": "Error creating access token", "details": str(e)}), 500



# @app.route("/login", methods=["POST"])
# def login():
#     data = request.json
#     email = data["email"]
#     password = data["password"]
#     user = User.query.filter_by(user_email=email).first()
#     if user and user.user_password == password:
#         access_token = jwt.encode({"sub": email, "exp": datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])
#         return jsonify({"message": "Login successful", "access_token": access_token})
#     else:
#         return jsonify({"error": "Login Unsuccessful. Please check credentials"}), 401



# @app.route('/register', methods=['POST'])
# def register():
#     data = request.json
#     fname = data["fname"]
#     email = data["email"]
#     password = data["password"]
#     hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#     user = User(fname=fname, email=email, user_password=hashed_password)
#     db.session.add(user)
#     db.session.commit()
#     return jsonify({"message": "Account created successfully"}), 201








@app.route('/sentry_error')
def sentry_error():
    try:
        division_by_zero = 1 / 0
        return jsonify({"result": division_by_zero})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
