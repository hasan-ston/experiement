from datetime import datetime, timedelta
from random import randint
from typing import List, TypedDict


class Transaction(TypedDict):
    amount: float
    description: str
    category: str
    posted_at: str


def fetch_transactions(user_id: int) -> List[Transaction]:
    # Mocked transactions; in a real service, swap with bank API SDK calls.
    base_time = datetime.utcnow()
    categories = ["groceries", "transportation", "entertainment", "rent", "other"]
    transactions: List[Transaction] = []
    for idx in range(5):
        amount = round(randint(5, 300) + randint(0, 99) / 100, 2)
        category = categories[idx % len(categories)]
        transactions.append(
            {
                "amount": float(amount),
                "description": f"Mock transaction {idx + 1}",
                "category": category,
                "posted_at": (base_time - timedelta(days=idx)).isoformat(),
            }
        )
    return transactions
