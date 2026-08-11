import pytest
from calculations import compute_totals, divide_per_portion


def test_compute_totals_sums_multiple_ingredients():
    ingredients = [
        {"calories": 330, "protein_g": 62, "carbs_g": 0, "fat_g": 7},
        {"calories": 200, "protein_g": 4, "carbs_g": 44, "fat_g": 0.5},
    ]
    result = compute_totals(ingredients)
    assert result == {"calories": 530.0, "protein_g": 66.0, "carbs_g": 44.0, "fat_g": 7.5}


def test_compute_totals_handles_empty_list():
    assert compute_totals([]) == {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}


def test_compute_totals_handles_missing_keys_gracefully():
    ingredients = [{"calories": 100}]  # protein_g/carbs_g/fat_g yok
    result = compute_totals(ingredients)
    assert result["calories"] == 100.0
    assert result["protein_g"] == 0.0


def test_divide_per_portion_splits_correctly():
    totals = {"calories": 530.0, "protein_g": 66.0, "carbs_g": 44.0, "fat_g": 7.5}
    result = divide_per_portion(totals, 4)
    assert result == {"calories": 132.5, "protein_g": 16.5, "carbs_g": 11.0, "fat_g": 1.9}


def test_divide_per_portion_raises_on_zero():
    with pytest.raises(ValueError):
        divide_per_portion({"calories": 100.0}, 0)


def test_divide_per_portion_raises_on_negative():
    with pytest.raises(ValueError):
        divide_per_portion({"calories": 100.0}, -2)
