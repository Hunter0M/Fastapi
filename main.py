from flask import Flask,render_template,redirect,url_for,request,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,select
from datetime import datetime,timedelta
from flask_cors import CORS
import sentry_sdk
import jwt
from functools import wraps




import os

sentry_sdk.init(
    dsn="https://803ae945357ca4dcc17c7ad8d705b95b@o4507805013573632.ingest.us.sentry.io/4507811253977088",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

app = Flask(__name__)

app.config["SECRET_KEY"] = "asdfghjlpoiuytrewqzxcvbnmkjhgfdsa"
app =  Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql://postgres:0777@localhost/test_api'
db = SQLAlchemy(app)




class Product(db.Model):
    __tablename__='products'
    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    name = db.Column(db.String,nullable= False)
    buying_price = db.Column(db.Integer,nullable= False)
    selling_price = db.Column(db.Integer,nullable= False)
    stock_quantity= db.Column(db.Integer,nullable= False)
    sale = db.relationship('Sale',backref='product')
    uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Sale(db.Model):
    __tablename__ ='sales'
    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    pid =db.Column(db.Integer,db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer,nullable= False)
    created_at = db.Column(db.DateTime,server_default = func.now())
    uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)



class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, db.Identity(always=True), primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(80), nullable=False, unique=True)

     # relationship
    product=db.relationship('Product', backref='products')
    sale=db.relationship('Sale', backref='sales')


with app.app_context():
    db.create_all()


CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# This route will allow users to post data to our API.
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

# This route will allow users to retrieve all users.
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
        token=request.headers.get("Authorization")

        if token is None:
            return jsonify({"message" : "couldn't validate user,token is missing"}), 401
        
        try:
            data=jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user= data["sub"]

            return f(current_user,*args,**kwargs)
        except Exception as e:
            return jsonify({"error":"error decoding token. Confirm your secret key"}),401


    return decorated





# @app.route('/users', methods=['POST','GET'])
# def users():

#     if request.method == 'POST':
#         try:
#             data = request.json
#             username = data["username"]
#             user_password = data["user_password"]
#             user_email = data["user_eamil"]
#             user = User(username=username,user_password=user_password,user_email=user_email)
#             db.session.add(user)
#             db.session.commit()
#             return jsonify({"message": "User created successfully"}), 201
#         except Exception as e:
#             return jsonify({"message": "Error creating user"}), 400
#     elif request.method == 'GET':
#         users = User.query.all()
#         user =[]
#         for user in users:
#             user.append({
#                         "id": user.id,
#                         "username":user.username,
#                         "user_password":user.user_password,
#                         "user_email":user.user_email
#                          })
            
#             return jsonify({"users": user}),200
        


@app.route('/products', methods=['GET','POST'])
@token_required
def products(current_user):
    if request.method=='POST':
        try:
            data=request.json

            existing_product=db.session.query(Product).filter(Product.product_name==data['product_name'],
                                                      Product.product_price==data['product_price'],
                                                      Product.uid==data['uid']).first()
            
            if existing_product:
                return jsonify({'error': 'product already exists!'}),409
            
            new_product=Product(
                uid=data['uid'],
                name=data['name'],
                buying_price=data['buying_price'],
                selling_price=data['selling_price'],
                stock_quantity=data['stock_quantity']
            )
            db.session.add(new_product)
            db.session.commit()
            db.session.refresh(new_product)
            
            return jsonify({'product added succesfully!':new_product.id}),201

        except Exception as e:
            db.session.rollback()  # In general, db.session.rollback() is used to:
            # 1. Undo changes made by a previous transaction. 2.Restore the database to its previous state
            # 3. Prevent data inconsistencies. 4.Ensure database consistency and integrity
            return jsonify({'error adding product': str(e)}),500
        
    elif request.method=='GET':
        try:
            user=db.session.query(User).filter(User.username==current_user).first()
            if not user:
                return jsonify({"message": "user not found"})
            
            products=db.session.query(Product).all()
            prods=[]
            for product in products:
                prods.append({
                "id":product.id,
                "uid":product.uid,
                "product_name":product.product_name,
                "product_price":product.product_price,
                "stock_quantity":product.stock_quantity
            })
            return jsonify({"products": prods}),200
        
        except Exception as e:
            return jsonify({'error fetching products': str(e)}),500



# @app.route('/product',methods=['GET','POST'])
# def product():
#     if request.method == 'POST':
#         try:
#             data = request.json
#             name = data['name']
#             buying_price = data['buying_price']
#             selling_price = data['selling_price']
#             stock_quantity = data['stock_quantity']
#             product = Product(name=name,buying_price=buying_price,selling_price=selling_price,stock_quantity=stock_quantity)
#             db.session.add(product)
#             db.session.commit()
#             return jsonify({"message":"product added successfully"}),201
#         except Exception as e:
#             return jsonify({'error':str(e)}),500
#     elif request.method == 'GET':
#         products = db.session.execute(db.select(Product).order_by(Product.name)).scalars()
#         prods =[]
#         for product in products:
            
#             prods.append({
#                 "id":product.id,
#                 "name":product.name,
#                 "buying_price":product.buying_price,
#                 "selling_price":product.selling_price,
#                 "stock_quantity":product.stock_quantity

#             })
#         return jsonify({"products": prods}),200



@app.route('/sales',methods=['GET','POST'])
def sales():
    if request.method == 'POST':
        try:
            data = request.json
            pid = data['pid']
            quantity = data['quantity']
            sale = Sale(pid=pid,quantity=quantity)
            db.session.add(sale)
            db.session.commit()
            return jsonify({"message":"Sale made successfully"}),201
        except Exception as e:
            return jsonify({"error":str(e)}),500
    elif request.method == 'GET':
        try:
            sales = db.session.execute(db.select(Sale).order_by(Sale.pid)).scalars()
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


@app.route("/make_sale", methods=['POST'])
def make_sale():
    try:
        data = request.json
        pid = data['pid']
        quantity = data['quantity']

        product = Product.query.get(pid)
        if not product:
            return jsonify({"error": "Invalid product ID"}), 400

        stock = product.stock_quantity
        if quantity <= 0 or quantity > stock:
            return jsonify({"error": "Invalid quantity"}), 400

        product.stock_quantity -= quantity
        sale = Sale(pid=pid, quantity=quantity)
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message": "Sale made successfully"}), 201

    except ValueError:
        return jsonify({"error": "Invalid quantity"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app. route('/dashboard',methods=['GET','POST'] )
def dashboard():

    sales_per_day = db.session.query(
    func.date(Sale.created_at).label('date'),
    func.sum(Sale.quantity * Product.selling_price).label('sales_per_day')
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    profit_per_day = db.session.query(
    func.date(Sale.created_at).label('date'),
    func.sum( (Sale.quantity * Product.selling_price)-
    (Sale.quantity * Product.buying_price) ).label("profit")
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    # profit_per_day = db.session.query(
    #     func.DATE(Sale.created_at).label('date_only'),
    #     (func.sum(Product.selling_price - Product.buying_price)).label('profits')
    # ).join(product, Sale.pid == Product.id).group_by('date_only').order_by('date_only')


    sales_data= [ {'date':str(date),"total_sales": total_sales }
    for date, total_sales in sales_per_day]
    
    profit_data = [ {'date':str(date),"total_profit": total_profit }
                   for total_profit, date in profit_per_day]
    return jsonify({"sales_data": sales_data, "profit_data": profit_data}), 200
    


# @app.post("/login")
# def login_user():
#     data = request.json
#     u = data["username"]
#     p = data["password"]
#     existing_user = db.session.query(User).filter(User.username==u,User.password==p).first()
#     if not existing_user:
#         return jsonify({"error": "Invalid username or password"}), 401
    
#     return jsonify({"message": "Login successful"}), 200




# creating a login route
# @app.post('/login')
# def login():
#     data = request.json
#     u = data["username"]
#     p = data["user_password"]
#     existing_user = db.session.query(User).filter(User.username==u, User.user_password==p).first()

#     if existing_user is None:
#         return jsonify({"error": "invalid credentials!"}), 400
#     try:
#         access_token = jwt.encode({"sub":u, "exp": datetime.utcnow() + timedelta(minutes=30)}, app.config["SECRET_KEY"])

#         return jsonify({"message": "user login succesful!", "access_token": access_token})

#     except Exception as e:
#         return jsonify({"error creating access token": str(e)})




@app.post("/login")
def login_user():
    data = request.json

    u = data['username']
    p = data['password']
    existing_user = db.session.query(User).filter(User.username ==u,User.user_password==p).first()

    if not existing_user:
        return jsonify({"Login failed": "confirm credentials"}),401
    try :
        access_token = jwt.encode({"sub":u,"exp":datetime.utcnow()+ timedelta(minutes=30)},app.config['SECRET_KEY'])
        return jsonify({"message":"login sucessful","access token":access_token})
    except Exception as e:
        return jsonify({"error creating access token": e})


    
# testing sentry  
@app.route('/sentry_error')
def hello_world():
    try:
        division_by_zero = 1 / 0
        return jsonify({"result": division_by_zero})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return jsonify({"error":str(e)})
        
    

if __name__ == '__main__':
    app.run(debug=True)