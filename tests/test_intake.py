from dinner_crew.intake import DinnerRequest, RequestParser

parser = RequestParser()


def test_extracts_preferences_restrictions_city_user():
    r = parser.parse("Quero um prato vegetariano com cogumelo e ervas no Rio, sou u1")
    req = r.request
    assert req.preferences == ["cogumelos", "ervas"]
    assert req.restrictions == ["vegetariano"]
    assert req.city == "Rio de Janeiro"
    assert req.user_id == "u1"
    assert any("cogumelos" in u for u in r.understood)


def test_accents_and_multiword_restrictions():
    req = parser.parse("algo com salmão, sem glúten e sem lactose").request
    assert req.preferences == ["salmao"]
    assert req.restrictions == ["sem_gluten", "sem_lactose"]


def test_price_words():
    assert parser.parse("um jantar barato").request.price == "baixa"
    assert parser.parse("algo sofisticado").request.price == "alta"


def test_carne_is_not_read_as_caro():
    req = parser.parse("quero carne").request
    assert req.price == "media"
    assert req.preferences == ["carne"]


def test_follow_up_keeps_context():
    first = parser.parse("massa com tomate, sou u2").request
    second = parser.parse("e um vinho mais barato?", first)
    assert second.request.preferences == ["massa", "tomate"]
    assert second.request.user_id == "u2"
    assert second.request.price == "baixa"
    assert second.understood == ["preço: baixa"]


def test_dish_name_pins_dish():
    req = parser.parse("quero bife ancho com chimichurri").request
    assert req.dish == "Bife ancho com chimichurri"


def test_new_preferences_unpin_dish():
    pinned = DinnerRequest(dish="Feijoada")
    assert parser.parse("agora quero peixe", pinned).request.dish is None


def test_nothing_understood():
    r = parser.parse("olá!")
    assert r.understood == []
    assert r.request == DinnerRequest()
