from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.user import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default="Created")
    blockchain_id = db.Column(db.Integer, nullable=True)
    qr_code_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "manufacturer_id": self.manufacturer_id,
            "blockchain_id": self.blockchain_id,
            "qr_code": self.qr_code_path 
        }