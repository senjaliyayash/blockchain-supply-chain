import qrcode
import os
from blockchain import Blockchain
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
from models.user import db, User
from models.product import Product

app = Flask(__name__)
CORS(app) 

# Initialize Blockchain
blockchain = Blockchain()

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///supplychain.db'
app.config['SECRET_KEY'] = 'yash_secret_key_123'

db.init_app(app)

with app.app_context():
    db.create_all()

# --- ROUTE: Home ---
@app.route('/')
def home():
    return jsonify({"status": "Database Connected", "System": "Ready"})

# --- ROUTE: Register User ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists!"}), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role'],
        password_hash="fakehash123"
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User Registered Successfully!"}), 201

# --- ROUTE: Login ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user:
        return jsonify({
            "message": "Login Successful",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }), 200
    
    return jsonify({"message": "Invalid Credentials"}), 401

# --- ROUTE: Create Product (FIXED: QR + Blockchain combined) ---
@app.route('/product/create', methods=['POST'])
def create_product():
    data = request.json
    user = User.query.get(1)
    if not user:
        return jsonify({"error": "No User Found!"}), 404

    # 1. Create Product in DB first
    new_product = Product(
        name=data['name'],
        description=data['description'],
        manufacturer_id=user.id,
        current_owner_id=user.id,
        status="Created"
    )
    db.session.add(new_product)
    db.session.commit()

    # 2. Generate QR Code
    if not os.path.exists('static/qrcodes'):
        os.makedirs('static/qrcodes') # Safety check

    qr_data = f"ID:{new_product.id}|Name:{new_product.name}|Owner:{user.username}"
    qr = qrcode.make(qr_data)
    filename = f"{new_product.id}.png"
    save_path = os.path.join('static', 'qrcodes', filename)
    qr.save(save_path)
    
    # Save Path to DB
    new_product.qr_code_path = filename

    # 3. BLOCKCHAIN STEP
    blockchain.new_transaction(
        sender=user.username,
        recipient="Supply Chain Network",
        product_id=new_product.id,
        action="Created"
    )
    
    last_block = blockchain.last_block
    blockchain.new_block(proof=12345, previous_hash=blockchain.hash(last_block))
    
    # Save Block Index to DB
    new_product.blockchain_id = last_block['index'] + 1
    db.session.commit()

    return jsonify({"message": "Product & QR Created!", "product": new_product.to_dict()}), 201

# --- ROUTE: Get Products ---
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

# --- ROUTE: Update Status (FIXED: Adds Blockchain Record) ---
@app.route('/product/ship', methods=['POST'])
def ship_product():
    data = request.json
    product_id = data.get('product_id')
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # 1. Update SQLite Database
    product.status = "Shipped"
    db.session.commit()
    
    # 2. BLOCKCHAIN: Create Transaction
    blockchain.new_transaction(
        sender="Yash Corp", 
        recipient="Distributor", 
        product_id=product.id, 
        action="Shipped"
    )
    
    # 3. BLOCKCHAIN: Mine the Block
    last_block = blockchain.last_block
    blockchain.new_block(proof=12345, previous_hash=blockchain.hash(last_block))
    
    return jsonify({
        "message": "Product Shipped & Recorded on Blockchain!", 
        "new_status": product.status
    }), 200

# --- ROUTE: Get Full Blockchain ---
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)