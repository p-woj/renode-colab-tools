import IPython
from IPython.display import display
from pathlib import Path
import shutil


def display_asciicast(path):
    colab_dir = Path(Path.home() / ".ipython/nbextensions/google.colab")
    colab_dir.mkdir(parents=True, exist_ok=True)

    mod_path = Path(__file__).parent.resolve() / 'asciinema'
    for file in ['asciinema-player.css', 'asciinema-player.min.js']:
        shutil.copy(mod_path / file, colab_dir / file)

    name = Path(path).name
    shutil.copy(path, colab_dir / name)

    content = """
<div id="asciinema-cast-player-{name}"></div>
<link rel="stylesheet" type="text/css" href="/nbextensions/google.colab/asciinema-player.css" />
<script>
    async function startTerm() {{
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = `/nbextensions/google.colab/asciinema-player.min.js`;
        script.onload = async function() {{
            console.log("init done");
            AsciinemaPlayer.create('/nbextensions/google.colab/{name}', document.getElementById('asciinema-cast-player-{name}'));
        }}
        document.body.appendChild(script);
    }}
    startTerm();
</script>
""".format(name=name)
    display(IPython.display.HTML(content))

