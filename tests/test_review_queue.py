import pandas as pd
import pytest

from src.review_queue import (
    calculate_review_priority,
    build_review_queue,
    explain_review_priority,
)


def sample_transactions():

    return pd.DataFrame([
        {
            "transaction_id": 1,
            "risk_probability": 0.90,
            "amount": 1000,
        },
        {
            "transaction_id": 2,
            "risk_probability": 0.10,
            "amount": 100000,
        },
        {
            "transaction_id": 3,
            "risk_probability": 0.50,
            "amount": 5000,
        },
        {
            "transaction_id": 4,
            "risk_probability": 0.25,
            "amount": 20000,
        },
        {
            "transaction_id": 5,
            "risk_probability": 0.05,
            "amount": 200000,
        },
    ])


def test_review_priority_calculation():

    priority = calculate_review_priority(
        risk_probability=0.10,
        amount=100000,
    )

    assert priority == 10000.0


def test_review_queue_respects_capacity():

    transactions = sample_transactions()

    queue = build_review_queue(
        transactions,
        review_capacity=3,
    )

    assert len(queue) == 3


def test_review_queue_is_sorted_by_priority():

    transactions = sample_transactions()

    queue = build_review_queue(
        transactions,
        review_capacity=5,
    )

    priorities = (
        queue["review_priority"]
        .tolist()
    )

    assert priorities == sorted(
        priorities,
        reverse=True,
    )


def test_review_rank_is_sequential():

    transactions = sample_transactions()

    queue = build_review_queue(
        transactions,
        review_capacity=5,
    )

    assert queue["review_rank"].tolist() == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_highest_economic_priority_is_first():

    transactions = sample_transactions()

    queue = build_review_queue(
        transactions,
        review_capacity=3,
    )

    # Transactions 2 and 5 both have
    # economic priority of 10,000.
    assert queue.iloc[0]["review_priority"] == 10000.0
    assert queue.iloc[1]["review_priority"] == 10000.0


def test_required_columns_are_preserved():

    transactions = sample_transactions()

    queue = build_review_queue(
        transactions,
        review_capacity=3,
    )

    required_columns = {
        "transaction_id",
        "risk_probability",
        "amount",
        "review_priority",
        "review_rank",
    }

    assert required_columns.issubset(
        queue.columns
    )


def test_invalid_capacity_raises_error():

    transactions = sample_transactions()

    with pytest.raises(ValueError):

        build_review_queue(
            transactions,
            review_capacity=0,
        )


def test_missing_columns_raise_error():

    transactions = pd.DataFrame([
        {
            "transaction_id": 1,
            "risk_probability": 0.5,
        }
    ])

    with pytest.raises(ValueError):

        build_review_queue(
            transactions,
            review_capacity=5,
        )


def test_review_explanation_is_human_readable():

    explanation = explain_review_priority(
        risk_probability=0.10,
        amount=100000,
        review_priority=10000,
    )

    assert isinstance(
        explanation,
        str,
    )

    assert "10.00%" in explanation
    assert "100,000.00" in explanation
    assert "10,000.00" in explanation