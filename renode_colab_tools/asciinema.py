import base64
import IPython
from IPython.display import display
from pathlib import Path
import shutil

# we do this every time, because it doesn't hurt
def provision_asciinema():
    colab_dir = Path(Path.home() / ".ipython/nbextensions/google.colab")
    colab_dir.mkdir(parents=True, exist_ok=True)

    mod_path = Path(__file__).parent.resolve() / 'asciinema'
    for file in ['asciinema-player.css', 'asciinema-player.min.js']:
        shutil.copy(mod_path / file, colab_dir / file)


def display_asciicast(path):

    provision_asciinema()

    # the name is used to uniquely identify container divs
    name = Path(path).name
    text = base64.b64encode(Path(path).read_text().encode('ascii')).decode('ascii')

    content = """
<div id="asciinema-cast-player-{name}" style="width: 50%"></div>
<link rel="stylesheet" type="text/css" href="/nbextensions/google.colab/asciinema-player.css" />
<script>
    async function startPlayer() {{
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = `/nbextensions/google.colab/asciinema-player.min.js`;
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

