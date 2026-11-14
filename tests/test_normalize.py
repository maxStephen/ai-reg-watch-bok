from regwatch.normalize import html_to_text

PAGE = b"""<html><head><style>.x{}</style><script>var a=1;</script></head>
<body><header>Site header</header><nav>Menu</nav>
<main><h1>AI RMF</h1><p>The   framework
is voluntary.</p></main>
<footer>Footer links</footer></body></html>"""


def test_html_strips_furniture_and_collapses_whitespace():
    text = html_to_text(PAGE)
    assert text == "AI RMF\nThe framework\nis voluntary."


def test_html_without_main_uses_body():
    text = html_to_text(b"<html><body><nav>Menu</nav><p>Content</p></body></html>")
    assert text == "Content"
