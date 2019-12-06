from localite.flow import has_poison


def test_has_poison():
    payload = ({"cmd": "poison-pill"}, 12345)
    assert has_poison(payload)
    payload = ({"Cmd": "Poison-Pill"}, 12345)
    assert has_poison(payload)


def test_has_no_poison():
    payload = ({"cmd": "poisonpill"}, 12345)
    assert not has_poison(payload)
    payload = ({"command": "poison-pill"}, 12345)
    assert not has_poison(payload)

