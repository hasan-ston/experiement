from collections import defaultdict
from typing import Dict, List

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Expense, db
from services.cache import get_cache, set_cache

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


@expenses_bp.post("")
@jwt_required()
def create_expense():
    data = request.get_json() or {}
    category = data.get("category")
    description = data.get("description", "")
    amount = data.get("amount")
    if not category or amount is None:
        return jsonify({"error": "Category and amount required"}), 400

    user_id = int(get_jwt_identity())
    expense = Expense(
        user_id=user_id,
        category=category,
        description=description,
        amount=float(amount),
    )
    db.session.add(expense)
    db.session.commit()
    _invalidate_summary_cache(user_id)

    return jsonify({"expense": _serialize_expense(expense)}), 201


@expenses_bp.get("")
@jwt_required()
def list_expenses():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.created_at.desc()).limit(100).all()
    return jsonify({"expenses": [_serialize_expense(e) for e in expenses]})


@expenses_bp.get("/summary")
@jwt_required()
def expense_summary():
    user_id = int(get_jwt_identity())
    cache_key = f"summary:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return jsonify({"summary": cached, "cached": True})

    expenses = Expense.query.filter_by(user_id=user_id).all()
    summary: Dict[str, float] = defaultdict(float)
    for exp in expenses:
        summary[exp.category] += float(exp.amount)
    summary_payload = [{"category": cat, "total": total} for cat, total in summary.items()]

    set_cache(cache_key, summary_payload)
    return jsonify({"summary": summary_payload, "cached": False})


def _serialize_expense(expense: Expense) -> Dict:
    return {
        "id": expense.id,
        "category": expense.category,
        "description": expense.description,
        "amount": float(expense.amount),
        "created_at": expense.created_at.isoformat(),
    }


def _invalidate_summary_cache(user_id: int) -> None:
    # Avoid import cycles by lazy import
    try:
        from services.cache import get_redis_client

        client = get_redis_client()
        client.delete(f"summary:{user_id}")
    except Exception:
        pass
