from regwatch.normalize import html_to_text

PAGE = b"""<html><head><style>.x{}</style><script>var a=1;</script></head>
<body><header>Site header</header><nav>Menu</nav>
<main><h1>AI RMF</h1><p>The   framework
is voluntary.</p></main>
<footer>Footer links</footer></body></html>"""


def test_html_strips_furniture_and_collapses_whitespace():
    text = html_to_text(PAGE)
    assert text == "AI RMF\nThe framework is voluntary."


def test_html_without_main_uses_body():
    text = html_to_text(b"<html><body><nav>Menu</nav><p>Content</p></body></html>")
    assert text == "Content"


def test_inline_elements_stay_on_one_line():
    text = html_to_text(b"<main><p>A <a href='#'>.gov</a> website <strong>belongs</strong> to an agency.</p></main>")
    assert text == "A .gov website belongs to an agency."


def test_blocks_and_br_start_new_lines():
    text = html_to_text(b"<main><h2>Title</h2><ul><li>One</li><li>Two<br>lines</li></ul></main>")
    assert text == "Title\nOne\nTwo\nlines"


def test_gov_banner_and_breadcrumbs_removed():
    page = (b"<body><section class='usa-banner'>An official website of the United States government</section>"
            b"<div class='breadcrumb'>Home / ITL</div><p>Content</p></body>")
    assert html_to_text(page) == "Content"


def test_comments_are_not_included():
    assert html_to_text(b"<main><p>Text<!-- hidden note --></p></main>") == "Text"
