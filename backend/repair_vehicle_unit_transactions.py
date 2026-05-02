import argparse
from math import isclose

from database import SessionLocal
import models
from services.transaction_amount_service import VEHICLE_UNIT


def _signed_amount(item, raw_amount: float) -> float:
    return -abs(raw_amount) if item.category == models.CategoryEnum.waste else abs(raw_amount)


def _detect_fix(tx):
    if tx.item.unit != VEHICLE_UNIT or tx.unit_price == 0:
        return None

    expected_one_truck = _signed_amount(tx.item, tx.unit_price)
    quantity_priced = _signed_amount(tx.item, tx.quantity * tx.unit_price)

    if tx.vehicle_count is None:
        if isclose(tx.total_amount, expected_one_truck, rel_tol=0, abs_tol=0.5):
            return {
                "vehicle_count": 1,
                "total_amount": expected_one_truck,
                "reason": "missing_vehicle_count_only",
            }
        if isclose(tx.total_amount, quantity_priced, rel_tol=0, abs_tol=0.5):
            return {
                "vehicle_count": 1,
                "total_amount": expected_one_truck,
                "reason": "quantity_priced_bug",
            }
        return None

    expected_amount = _signed_amount(tx.item, tx.vehicle_count * tx.unit_price)
    if not isclose(tx.total_amount, expected_amount, rel_tol=0, abs_tol=0.5):
        return {
            "vehicle_count": tx.vehicle_count,
            "total_amount": expected_amount,
            "reason": "recalc_from_vehicle_count",
        }
    return None


def main():
    parser = argparse.ArgumentParser(
        description="원/대 거래의 차량 대수/금액 이상치를 점검하고 보정합니다."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="미리보기 대신 실제 DB 값을 수정합니다.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        txs = (
            db.query(models.Transaction)
            .join(models.Transaction.item)
            .filter(models.Item.unit == VEHICLE_UNIT)
            .order_by(models.Transaction.date.asc(), models.Transaction.id.asc())
            .all()
        )

        fixes = []
        for tx in txs:
            fix = _detect_fix(tx)
            if fix:
                fixes.append((tx, fix))

        if not fixes:
            print("수정 대상이 없습니다.")
            return

        print(f"수정 후보 {len(fixes)}건")
        for tx, fix in fixes:
            print(
                f"- id={tx.id} date={tx.date} item={tx.item.report_name or tx.item.name} "
                f"qty={tx.quantity} vehicles={tx.vehicle_count} unit_price={tx.unit_price} "
                f"amount={tx.total_amount} -> vehicles={fix['vehicle_count']} "
                f"amount={fix['total_amount']} reason={fix['reason']}"
            )

        if not args.apply:
            print("\n미리보기만 실행했습니다. 실제 반영은 --apply 옵션으로 실행하세요.")
            return

        for tx, fix in fixes:
            tx.vehicle_count = fix["vehicle_count"]
            tx.total_amount = fix["total_amount"]

        db.commit()
        print(f"\n{len(fixes)}건을 수정했습니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
