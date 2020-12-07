from IPython.display import HTML, Audio, IFrame, display, Javascript
from google.colab.output import eval_js
from base64 import b64decode
from scipy.io.wavfile import read as wav_read
from plotly.offline import init_notebook_mode, iplot
import plotly.graph_objects as go
import pandas as pd
import io
import ffmpeg

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

def configure_plotly_browser_state():
  import IPython
  display(IPython.core.display.HTML('''
        <script src="/static/components/requirejs/require.js"></script>
        <script>
          requirejs.config({
            paths: {
              base: '/static/base',
              plotly: 'https://cdn.plot.ly/plotly-latest.min.js?noext',
            },
          });
        </script>
        '''))

def show_executed_instructions(metricsParser):
  cpus, instructionEntries = metricsParser.get_instructions_entries()

  data = pd.DataFrame(instructionEntries, columns=['realTime', 'virtualTime', 'cpuId', 'executedInstruction'])
  fig = go.Figure()

  for cpuId, cpuName in cpus.items():
      entries = data[data['cpuId'] == bytes([cpuId])]
      if entries.empty:
          continue
      fig.add_trace(go.Scatter(x=entries['virtualTime'], y=entries['executedInstruction'], name=cpuName))

  fig.update_layout(title='Executed Instructions',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Instructions count')
  
  iplot(fig)

def show_memory_access(metricsParser):
  memoryEntries = metricsParser.get_memory_entries()
  data = pd.DataFrame(memoryEntries, columns=['realTime', 'virtualTime', 'operation'])

  reads = data[data['operation'] == bytes([2])]
  writes = data[data['operation'] == bytes([3])]

  fig = go.Figure()
  fig.add_trace(go.Scatter(x=writes['virtualTime'], y=[*range(0, len(writes))], name='Writes'))
  fig.add_trace(go.Scatter(x=reads['virtualTime'], y=[*range(0, len(reads))], name='Reads'))
  fig.update_layout(title='Memory access',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Memory access operations')
  
  iplot(fig)

def show_peripheral_access(metricsParser):
  peripherals, peripheralEntries = metricsParser.get_peripheral_entries()
  data = pd.DataFrame(peripheralEntries, columns=['realTime', 'virtualTime', 'operation', 'address'])

  figWrites = go.Figure()
  figReads = go.Figure()

  for key, value in peripherals.items():
    tempData = data[data.address >= value[0]]
    peripheralEntries = tempData[tempData.address <= value[1]]
    readOperationFilter = peripheralEntries['operation'] == bytes([0])
    writeOperationFilter = peripheralEntries['operation'] == bytes([1])
    readEntries = peripheralEntries[readOperationFilter]
    writeEntries = peripheralEntries[writeOperationFilter]
    if not writeEntries.empty:
      figWrites.add_trace(go.Scatter(x=writeEntries['virtualTime'], y=[*range(0, len(writeEntries))], name=key))
    if not readEntries.empty:
      figReads.add_trace(go.Scatter(x=readEntries['virtualTime'], y=[*range(0, len(readEntries))], name=key))

  figWrites.update_layout(title='Peripheral writes',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Peripheral write operations')
  
  figReads.update_layout(title='Peripheral reads',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Peripheral read operations')

  iplot(figWrites)
  iplot(figReads)

def show_exceptions(metricsParser):
  exceptionEntries = metricsParser.get_exceptions_entries()
  data = pd.DataFrame(exceptionEntries, columns=['realTime', 'virtualTime', 'number'])
  fig = go.Figure()

  for index in data['number'].drop_duplicates():
    entries = data[data['number'] == index]
    fig.add_trace(go.Scatter(x=entries['virtualTime'], y=[*range(0, len(entries))], name=index))

  fig.update_layout(title='Exceptions',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Exception operations')

  iplot(fig)

def take_photo(filename='photo.jpg', quality=0.8):
  js = Javascript('''
    async function takePhoto(quality) {
      const div = document.createElement('div');
      const capture = document.createElement('button');
      capture.textContent = 'Capture';
      div.appendChild(capture);

      const video = document.createElement('video');
      video.style.display = 'block';
      const stream = await navigator.mediaDevices.getUserMedia({video: true});

      document.body.appendChild(div);
      div.appendChild(video);
      video.srcObject = stream;
      await video.play();

      // Resize the output to fit the video element.
      google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);

      // Wait for Capture to be clicked.
      await new Promise((resolve) => capture.onclick = resolve);

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      stream.getVideoTracks()[0].stop();
      div.remove();
      return canvas.toDataURL('image/jpeg', quality);
    }
    ''')
  display(js)
  data = eval_js('takePhoto({})'.format(quality))
  binary = b64decode(data.split(',')[1])
  with open(filename, 'wb') as f:
    f.write(binary)
  return filename