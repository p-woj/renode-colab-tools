from IPython.display import HTML, Audio, display
from google.colab.output import eval_js
from base64 import b64decode
from scipy.io.wavfile import read as wav_read
from scipy.io.wavfile import write as wav_write
import io
import ffmpeg
import ipywidgets as w
import pyaudioconvert as pac
import wave
from shutil import copyfile

AUDIO_HTML = """
<script>
var my_div = document.createElement("DIV");
var my_p = document.createElement("P");
var my_btn = document.createElement("BUTTON");
var t = document.createTextNode("Press to start recording");

my_btn.appendChild(t);
my_div.appendChild(my_btn);
document.body.appendChild(my_div);

var base64data = 0;
var reader;
var recorder, gumStream;
var recordButton = my_btn;

var handleSuccess = function(stream) {
  gumStream = stream;
  var options = {
    bitsPerSecond: 16000, //chrome seems to ignore, always 48k
    mimeType : 'audio/webm;codecs=pcm'
  };            
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = function(e) {            
    var url = URL.createObjectURL(e.data);
    var preview = document.createElement('audio');
    preview.controls = true;
    preview.src = url;
    document.body.appendChild(preview);

    reader = new FileReader();
    reader.readAsDataURL(e.data); 
    reader.onloadend = function() {
      base64data = reader.result;
    }
  };
  };

recordButton.innerText = "Start recording";
navigator.mediaDevices.getUserMedia({audio: true}).then(handleSuccess);

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

var data = new Promise(resolve=>{
    recordButton.onclick = () => {
      recordButton.innerText = "Recording...";
      recorder.start();
      sleep(1000).then(() => {
        recorder.stop();
        gumStream.getAudioTracks()[0].stop();
        recordButton.style.display = "none"
      });
      sleep(2000).then(() => {
            resolve(base64data.toString())
    });
    };
});
      
</script>
"""

def get_audio():
  display(HTML(AUDIO_HTML))
  data = eval_js("data")
  binary = b64decode(data.split(',')[1])
  
  process = (ffmpeg
    .input('pipe:0')
    .output('pipe:1', format='wav')
    .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True, quiet=True, overwrite_output=True)
  )
  output, err = process.communicate(input=binary)
  
  riff_chunk_size = len(output) - 8
  # Break up the chunk size into four bytes, held in b.
  q = riff_chunk_size
  b = []
  for i in range(4):
      q, r = divmod(q, 256)
      b.append(r)

  # Replace bytes 4:8 in proc.stdout with the actual size of the RIFF chunk.
  riff = output[:4] + bytes(b) + output[8:]
  sr, audio = wav_read(io.BytesIO(riff))
  return audio, sr

def audio_options():
  copyfile('binary_yes', 'audio_bin')
  grid = w.GridspecLayout(1, 4)
  grid[0,0] = w.Button(description='Default YES')
  grid[0,1] = w.Button(description='Default NO')
  grid[0,2] = w.Button(description='Microphone')
  grid[0,3] = w.FileUpload(accept='.wav')

  grid[0,0].on_click(default_yes)
  grid[0,1].on_click(default_no)
  grid[0,2].on_click(handle_microphone)
  grid[0,3].observe(upload_wav, 'data')
  return grid

def default_yes(obj):
  copyfile('binary_yes', 'audio_bin')
  convert_bin_to_wav()
  display(Audio(filename="audio.wav"))

def default_no(obj):
  copyfile('binary_no', 'audio_bin')
  convert_bin_to_wav()
  display(Audio(filename="audio.wav"))

def handle_microphone(obj):
  audio, sr = get_audio()
  wav_write('audio.wav', sr, audio)
  pac.convert_wav_to_16bit_mono('audio.wav', 'converted.wav')
  sr, audio = wav_read('converted.wav')
  audio.tofile('audio_bin')

def upload_wav(obj):
  uploader = obj['owner']
  with open('audio.wav', 'wb') as f:
        f.write(uploader.data[0])
  convert_wav_to_binary()
  display(Audio(filename="audio.wav"))

def convert_wav_to_binary():
  sr, audio = wav_read('audio.wav')
  audio.tofile('audio_bin')

def convert_bin_to_wav():
  with open("audio_bin", "rb") as inp_f:
    data = inp_f.read()
    with wave.open("audio.wav", "wb") as out_f:
        out_f.setnchannels(1)
        out_f.setsampwidth(2) # number of bytes
        out_f.setframerate(16000)
        out_f.writeframesraw(data)