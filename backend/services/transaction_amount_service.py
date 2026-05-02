from fastapi import HTTPException

import models


VEHICLE_UNIT = "원/대"


def get_item_or_404(item_id: int, db):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    return item


def normalize_transaction_payload(data: dict, item: models.Item) -> dict:
    quantity = float(data.get("quantity") or 0)
    unit_price = float(data.get("unit_price") or 0)

    if item.unit == VEHICLE_UNIT:
        vehicle_count = data.get("vehicle_count")
        if vehicle_count is None:
            raise HTTPException(
                status_code=422,
                detail=f"{item.report_name or item.name} 품목은 차량 대수가 필요합니다",
            )
        data["vehicle_count"] = int(vehicle_count)
        raw_amount = data["vehicle_count"] * unit_price
    else:
        data["vehicle_count"] = None
        raw_amount = quantity * unit_price

    if item.category == models.CategoryEnum.waste:
        data["total_amount"] = -abs(raw_amount)
    else:
        data["total_amount"] = abs(raw_amount)

    return data
