import plotly.graph_objects as go
import pandas as pd
from plotly.offline import init_notebook_mode, iplot
from IPython.display import display

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

def show_executed_instructions(metricsParser, fraction=1):
  cpus, instructionEntries = metricsParser.get_instructions_entries()

  data = pd.DataFrame(instructionEntries, columns=['realTime', 'virtualTime', 'cpuId', 'executedInstruction'])
  fig = go.Figure()

  for cpuId, cpuName in cpus.items():
      entries = _reduce_sample(data[data['cpuId'] == bytes([cpuId])], fraction)
      if entries.empty:
          continue
      fig.add_trace(go.Scatter(x=entries['virtualTime'], y=entries['executedInstruction'], name=cpuName))

  fig.update_layout(title='Executed Instructions',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Instructions count')
  
  iplot(fig)

def show_memory_access(metricsParser, fraction=1):
  memoryEntries = metricsParser.get_memory_entries()
  data = pd.DataFrame(memoryEntries, columns=['realTime', 'virtualTime', 'operation'])

  reads = _reduce_sample(data[data['operation'] == bytes([2])], fraction)
  writes = _reduce_sample(data[data['operation'] == bytes([3])], fraction)

  fig = go.Figure()
  fig.add_trace(go.Scatter(x=writes['virtualTime'], y=writes.index, name='Writes'))
  fig.add_trace(go.Scatter(x=reads['virtualTime'], y=reads.index, name='Reads'))
  fig.update_layout(title='Memory access',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Memory access operations')
  
  iplot(fig)

def show_peripheral_access(metricsParser, fraction=1):
  peripherals, peripheralEntries = metricsParser.get_peripheral_entries()
  data = pd.DataFrame(peripheralEntries, columns=['realTime', 'virtualTime', 'operation', 'address'])

  figWrites = go.Figure()
  figReads = go.Figure()

  for key, value in peripherals.items():
    tempData = data[data.address >= value[0]]
    peripheralEntries = tempData[tempData.address <= value[1]]
    readOperationFilter = peripheralEntries['operation'] == bytes([0])
    writeOperationFilter = peripheralEntries['operation'] == bytes([1])
    readEntries = _reduce_sample(peripheralEntries[readOperationFilter], fraction)
    writeEntries = _reduce_sample(peripheralEntries[writeOperationFilter], fraction)
    if not writeEntries.empty:
      figWrites.add_trace(go.Scatter(x=writeEntries['virtualTime'], y=writeEntries.index, name=key))
    if not readEntries.empty:
      figReads.add_trace(go.Scatter(x=readEntries['virtualTime'], y=writeEntries.index, name=key))

  figWrites.update_layout(title='Peripheral writes',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Peripheral write operations')
  
  figReads.update_layout(title='Peripheral reads',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Peripheral read operations')

  iplot(figWrites)
  iplot(figReads)

def show_exceptions(metricsParser, fraction=1):
  exceptionEntries = metricsParser.get_exceptions_entries()
  data = pd.DataFrame(exceptionEntries, columns=['realTime', 'virtualTime', 'number'])
  fig = go.Figure()

  for index in data['number'].drop_duplicates():
    entries = _reduce_sample(data[data['number'] == index], fraction)
    fig.add_trace(go.Scatter(x=entries['virtualTime'], y=entries.index, name=index))

  fig.update_layout(title='Exceptions',
                  xaxis_title='Virtual Time [ms]',
                  yaxis_title='Exception operations')

  iplot(fig)


def _reduce_sample(data, fraction):
  return data.reset_index(drop=True).sample(frac=fraction).sort_index()
