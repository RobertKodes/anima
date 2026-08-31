"""Visual language for the graphical CLI."""

BANNER = (
    "[#e8a04a b]ANIMA[/]   one being · many brains · memory is Sibyl\n"
    "[#8a7a68]Graphical CLI  ·  same runtime as --cli  ·  nothing here is the identity[/]"
)

TUI_CSS = """
Screen {
    background: #140f0a;
    color: #f4eadc;
}

#shell {
    height: 100%;
}

#banner {
    dock: top;
    height: 5;
    background: #1e1610;
    border: heavy #c45c26;
    padding: 0 1;
}

#body {
    height: 1fr;
}

#side {
    width: 30;
    background: #1e1610;
    border: tall #3a2c20;
    padding: 0 1;
}

#why {
    width: 32;
    background: #1e1610;
    border: tall #3a2c20;
    padding: 0 1;
}

#chat-wrap {
    width: 1fr;
    border: tall #3a2c20;
}

#chat {
    height: 1fr;
    padding: 1 1 0 1;
    scrollbar-color: #c45c26;
}

#hints {
    height: 6;
    padding: 0 1;
    color: #8a7a68;
    display: none;
}

#hints.visible {
    display: block;
}

#statusbar {
    dock: bottom;
    height: 1;
    background: #2a2018;
    color: #8a7a68;
    padding: 0 1;
}

#stream {
    height: auto;
    max-height: 10;
    padding: 0 1;
    background: #18120d;
    border-top: tall #3a2c20;
    display: none;
}

#stream.active {
    display: block;
}

#stream .think {
    color: #8a7a68;
    text-style: italic;
}

#composer.busy {
    border: tall #c45c26;
}

Input {
    background: #140f0a;
    color: #f4eadc;
    border: none;
}

Input:focus {
    border: none;
}

#help-card {
    width: 80;
    height: auto;
    max-height: 32;
    background: #1e1610;
    border: heavy #e8a04a;
    padding: 1 2;
}

Footer {
    background: #1e1610;
    color: #8a7a68;
}
"""
