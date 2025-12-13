from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Expense, db
from services.mock_bank import fetch_transactions

imports_bp = Blueprint("imports", __name__, url_prefix="/api/imports")


@imports_bp.post("/mock")
@jwt_required()
def import_mock_transactions():
    user_id = int(get_jwt_identity())
    transactions = fetch_transactions(user_id)
    created = []
    for tx in transactions:
        expense = Expense(
            user_id=user_id,
            category=tx["category"],
            description=tx["description"],
            amount=tx["amount"],
        )
        db.session.add(expense)
        created.append(expense)
    db.session.commit()

    return jsonify({"imported": len(created), "expenses": [e.id for e in created]})
