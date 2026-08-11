from db import init_db, log_meal, get_today_totals


def test_log_and_get_today_totals(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    log_meal(user_id=1, totals={"calories": 300, "protein_g": 20, "carbs_g": 30, "fat_g": 10}, portion_count=2, db_path=db_path)
    log_meal(user_id=1, totals={"calories": 150, "protein_g": 10, "carbs_g": 15, "fat_g": 5}, portion_count=None, db_path=db_path)

    totals, count = get_today_totals(1, db_path=db_path)
    assert count == 2
    assert totals["calories"] == 450.0
    assert totals["protein_g"] == 30.0


def test_get_today_totals_returns_zero_when_empty(tmp_path):
    db_path = str(tmp_path / "empty.db")
    init_db(db_path)

    totals, count = get_today_totals(999, db_path=db_path)
    assert count == 0
    assert totals == {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}


def test_different_users_are_isolated(tmp_path):
    db_path = str(tmp_path / "users.db")
    init_db(db_path)

    log_meal(1, {"calories": 100, "protein_g": 1, "carbs_g": 1, "fat_g": 1}, db_path=db_path)
    log_meal(2, {"calories": 200, "protein_g": 2, "carbs_g": 2, "fat_g": 2}, db_path=db_path)

    totals_user1, count_user1 = get_today_totals(1, db_path=db_path)
    assert count_user1 == 1
    assert totals_user1["calories"] == 100.0


def test_init_db_is_idempotent(tmp_path):
    """init_db birden fazla kez cagrilsa da hata vermemeli (CREATE TABLE IF NOT EXISTS)."""
    db_path = str(tmp_path / "repeat.db")
    init_db(db_path)
    init_db(db_path)  # ikinci cagri hata firlatmamali
