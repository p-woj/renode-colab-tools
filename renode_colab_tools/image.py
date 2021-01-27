from IPython.display import Image, display, Javascript
from google.colab.output import eval_js
from base64 import b64decode
from shutil import copyfile
import ipywidgets as w

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

def image_options():
  copyfile('default.jpg', 'photo.jpg')
  grid = w.GridspecLayout(1, 3)
  grid[0,0] = w.Button(description='Default')
  grid[0,1] = w.Button(description='Camera')
  grid[0,2] = w.FileUpload(accept='.jpg')

  grid[0,0].on_click(default_photo)
  grid[0,1].on_click(handle_camera)
  grid[0,2].observe(upload_photo, 'data')
  return grid

def default_photo(obj):
  copyfile('default.jpg', 'photo.jpg')
  display(Image('photo.jpg'))

def handle_camera(obj):
  photo = take_photo()
  display(Image(photo))

def upload_photo(obj):
  uploader = obj['owner']
  with open('photo.jpg', 'wb') as f:
        f.write(uploader.data[0])
  display(Image('photo.jpg'))