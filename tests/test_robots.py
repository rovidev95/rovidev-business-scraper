from scraper.robots import is_allowed, robots_url_for


def test_robots_url_for():
    assert robots_url_for("https://shop.example.com/a/b?c=1") == "https://shop.example.com/robots.txt"


def test_disallowed_path_is_blocked():
    txt = "User-agent: *\nDisallow: /private/"
    assert is_allowed(txt, "https://shop.example.com/private/x", "RoviDevBot") is False
    assert is_allowed(txt, "https://shop.example.com/public/x", "RoviDevBot") is True


def test_missing_robots_allows_everything():
    assert is_allowed(None, "https://shop.example.com/x", "RoviDevBot") is True
    assert is_allowed("", "https://shop.example.com/x", "RoviDevBot") is True
