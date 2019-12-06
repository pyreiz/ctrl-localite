from localite.flow.payload import has_poison, Payload


def test_has_poison():
    payload = Payload("cmd", "poison-pill", 12345)
    assert has_poison(payload)


def test_has_no_poison():
    payload = Payload("Cmd", "Poison-Pill", 12345)
    assert not has_poison(payload)
    payload = Payload("cmd", "poisonpill", 12345)
    assert not has_poison(payload)
    payload = Payload("command", "poison-pill", 12345)
    assert not has_poison(payload)

