from pathlib import Path
from kuristo.env import Env


def test_init_empty():
    env = Env()
    assert env.as_dict() == {}


def test_init_from_dict():
    env = Env({"A": 1, "B": True})
    # Values are cast to strings
    assert env["A"] == "1"
    assert env["B"] == "True"


def test_get_with_and_without_default():
    env = Env({"A": "x"})
    assert env.get("A") == "x"
    assert env.get("B") is None
    assert env.get("B", "default") == "default"


def test_set_and_setitem_casts_to_str():
    env = Env()
    env.set("A", 123)
    assert env["A"] == "123"
    env["B"] = True
    assert env["B"] == "True"


def test_update_from_file(tmp_path: Path):
    file_path = tmp_path / "envfile"
    file_path.write_text("""
    A=1
    B = two
    # this is a comment
    INVALIDLINE
    C=three=four
    """)

    env = Env()
    env.update_from_file(file_path)

    assert env["A"] == "1"
    assert env["B"] == "two"
    assert env["C"] == "three=four"


def test_update_from_file_missing(tmp_path: Path):
    env = Env({"A": "1"})
    missing_path = tmp_path / "does_not_exist"
    env.update_from_file(missing_path)  # should not raise
    assert env["A"] == "1"


def test_as_dict_returns_copy():
    env = Env({"A": "1"})
    d = env.as_dict()
    d["A"] = "changed"
    assert env["A"] == "1"


def test_contains_and_delitem():
    env = Env({"A": "1"})
    assert "A" in env
    del env["A"]
    assert "A" not in env


def test_keys_items_values():
    env = Env({"A": "1", "B": "2"})
    assert set(env.keys()) == {"A", "B"}
    assert set(env.items()) == {("A", "1"), ("B", "2")}
    assert set(env.values()) == {"1", "2"}


def test_repr_format():
    env = Env({"A": "1"})
    r = repr(env)
    assert r.startswith("Env(") and "A" in r and "1" in r
