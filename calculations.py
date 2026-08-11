"""
Kalori/makro toplama ve kisi basi bolme mantigi.
Bilerek AI'dan bagimsiz tutuldu: hesaplama hep kodda yapilir, AI sadece
malzeme basina tahmini deger uretir. Bu sayede sonuclar deterministik olur.
"""

MACRO_KEYS = ("calories", "protein_g", "carbs_g", "fat_g")


def compute_totals(ingredients: list[dict]) -> dict:
    """Malzeme listesindeki kalori/makrolari toplar.

    ingredients: [{"calories": .., "protein_g": .., "carbs_g": .., "fat_g": ..}, ...]
    """
    totals = {key: 0.0 for key in MACRO_KEYS}
    for ingredient in ingredients:
        for key in MACRO_KEYS:
            totals[key] += ingredient.get(key, 0) or 0
    return {key: round(value, 1) for key, value in totals.items()}


def divide_per_portion(totals: dict, portion_count: int) -> dict:
    """Toplam degerleri porsiyon sayisina boler."""
    if portion_count <= 0:
        raise ValueError("portion_count 0'dan buyuk bir sayi olmalidir")
    return {key: round(value / portion_count, 1) for key, value in totals.items()}
