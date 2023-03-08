import base64
import IPython
from IPython.display import display
from pathlib import Path

def display_asciicast(path):
    # the name is used to uniquely identify container divs
    name = Path(path).name
    text = base64.b64encode(Path(path).read_text().encode('ascii')).decode('ascii')

    content = """
<div id="asciinema-cast-player-{name}" style="width: 50%"></div>
<link rel="stylesheet" type="text/css" href="https://unpkg.com/asciinema-player@3.1.2/dist/bundle/asciinema-player.css" />
<script>
    async function startPlayer() {{
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = `https://unpkg.com/asciinema-player@3.1.2/dist/bundle/asciinema-player.min.js`;
        script.onload = async function() {{
            AsciinemaPlayer.create('data:text/plain;base64,{text}', document.getElementById('asciinema-cast-player-{name}'));
            console.log("asciinema player init done");
        }}
        document.body.appendChild(script);
    }}
    startPlayer();
</script>
""".format(text=text, name=name)
    display(IPython.display.HTML(content))

