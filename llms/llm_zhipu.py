from zhipuai import ZhipuAI
from plugins.common import settings

import os
import re
import base64
import jupyter_client
from io import BytesIO
from PIL import Image
from subprocess import PIPE
# 能力类型
ability_type = "chatGLM"
# 引擎类型
engine_type = "chatGLM"
IPYKERNEL = os.environ.get('IPYKERNEL', 'chatglm3-demo')
SYSTEM_PROMPT = '你是一位智能AI助手，你叫ChatGLM，你连接着一台电脑，但请注意不能联网。在使用Python解决任务时，你可以运行代码并得到结果，如果运行结果有错误，你需要尽可能对代码进行改进。'

client: ZhipuAI = None
kernel = None
Api_key=''
if os.environ['ZHIPU_API_KEY']:
    Api_key=os.environ['ZHIPU_API_KEY']
else:
    Api_key=settings.ZHIPU_API_KEY
     

def chat_init(history):
    history_data = []
    if history is not None:
        history_data = []
        for i, old_chat in enumerate(history):
                print(old_chat)
                history_data.append(
                    {
                        "role" : "assistant" if old_chat['role']=='AI' else old_chat['role'], 
                        "content": old_chat['content']
                    }
                )
    return history_data


def chat_one(prompt, history_formatted, max_length, top_p, temperature, data):
    yield str(len(prompt))+'字正在计算'
    history_formatted = history_formatted if history_formatted else []
    if len(history_formatted)==0 :
        history_formatted.append({"role": "user", "content": prompt})
    stop_sequences = []
    print(data)
    if 'func_mode' in data and data['func_mode']=='ci':
        history_formatted.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        stop_sequences.append("<|observation|>")
    print(history_formatted)
    response = client.chat.completions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=history_formatted,
        stream=True,
        temperature=0.01,
        top_p=0.01,
        stop=stop_sequences
    )
    if 'func_mode' in data and data['func_mode']=='ci':
        res = ""
        for chunk in response:
            res = res + chunk.choices[0].delta.content
        print(res)
        code = extract_code(res)
        print("Code:",code)
        if(code==""):
            yield "请换个方式重新提问"
            return
        yield "开始执行代码..."
        try:
            res_type, res = execute(code, get_kernel())
            yield res
        except Exception as e:
            yield (f'Error when executing code: {e}')
    else:
        res = ""
        for chunk in response:
            res = res + chunk.choices[0].delta.content
            yield res

class CodeKernel(object):
    def __init__(self,
                 kernel_name='kernel',
                 kernel_id=None,
                 kernel_config_path="",
                 python_path=None,
                 ipython_path=None,
                 init_file_path="./startup.py",
                 verbose=1):

        self.kernel_name = kernel_name
        self.kernel_id = kernel_id
        self.kernel_config_path = kernel_config_path
        self.python_path = python_path
        self.ipython_path = ipython_path
        self.init_file_path = init_file_path
        self.verbose = verbose

        if python_path is None and ipython_path is None:
            env = None
        else:
            env = {"PATH": self.python_path + ":$PATH", "PYTHONPATH": self.python_path}

        # Initialize the backend kernel
        self.kernel_manager = jupyter_client.KernelManager(kernel_name=IPYKERNEL,
                                                           connection_file=self.kernel_config_path,
                                                           exec_files=[self.init_file_path],
                                                           env=env)
        if self.kernel_config_path:
            self.kernel_manager.load_connection_file()
            self.kernel_manager.start_kernel(stdout=PIPE, stderr=PIPE)
            print("Backend kernel started with the configuration: {}".format(
                self.kernel_config_path))
        else:
            self.kernel_manager.start_kernel(stdout=PIPE, stderr=PIPE)
            print("Backend kernel started with the configuration: {}".format(
                self.kernel_manager.connection_file))

        if verbose:
            print(self.kernel_manager.get_connection_info())

        # Initialize the code kernel
        self.kernel = self.kernel_manager.blocking_client()
        # self.kernel.load_connection_file()
        self.kernel.start_channels()
        print("Code kernel started.")

    def execute(self, code):
        self.kernel.execute(code)
        try:
            shell_msg = self.kernel.get_shell_msg(timeout=30)
            io_msg_content = self.kernel.get_iopub_msg(timeout=30)['content']
            while True:
                msg_out = io_msg_content
                ### Poll the message
                try:
                    io_msg_content = self.kernel.get_iopub_msg(timeout=30)['content']
                    if 'execution_state' in io_msg_content and io_msg_content['execution_state'] == 'idle':
                        break
                except queue.Empty:
                    break

            return shell_msg, msg_out
        except Exception as e:
            print(e)
            return None

    def execute_interactive(self, code, verbose=False):
        shell_msg = self.kernel.execute_interactive(code)
        if shell_msg is queue.Empty:
            if verbose:
                print("Timeout waiting for shell message.")
        self.check_msg(shell_msg, verbose=verbose)

        return shell_msg

    def inspect(self, code, verbose=False):
        msg_id = self.kernel.inspect(code)
        shell_msg = self.kernel.get_shell_msg(timeout=30)
        if shell_msg is queue.Empty:
            if verbose:
                print("Timeout waiting for shell message.")
        self.check_msg(shell_msg, verbose=verbose)

        return shell_msg

    def get_error_msg(self, msg, verbose=False) -> str | None:
        if msg['content']['status'] == 'error':
            try:
                error_msg = msg['content']['traceback']
            except:
                try:
                    error_msg = msg['content']['traceback'][-1].strip()
                except:
                    error_msg = "Traceback Error"
            if verbose:
                print("Error: ", error_msg)
            return error_msg
        return None

    def check_msg(self, msg, verbose=False):
        status = msg['content']['status']
        if status == 'ok':
            if verbose:
                print("Execution succeeded.")
        elif status == 'error':
            for line in msg['content']['traceback']:
                if verbose:
                    print(line)

    def shutdown(self):
        # Shutdown the backend kernel
        self.kernel_manager.shutdown_kernel()
        print("Backend kernel shutdown.")
        # Shutdown the code kernel
        self.kernel.shutdown()
        print("Code kernel shutdown.")

    def restart(self):
        # Restart the backend kernel
        self.kernel_manager.restart_kernel()
        # print("Backend kernel restarted.")

    def interrupt(self):
        # Interrupt the backend kernel
        self.kernel_manager.interrupt_kernel()
        # print("Backend kernel interrupted.")

    def is_alive(self):
        return self.kernel.is_alive()


def b64_2_img(data):
    buff = BytesIO(base64.b64decode(data))
    return Image.open(buff)


def clean_ansi_codes(input_string):
    ansi_escape = re.compile(r'(\x9B|\x1B\[|\u001b\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', input_string)


def execute(code, kernel: CodeKernel) -> tuple[str, str | Image.Image]:
    res = ""
    res_type = None
    code = code.replace("<|observation|>", "")
    code = code.replace("<|assistant|>interpreter", "")
    code = code.replace("<|assistant|>", "")
    code = code.replace("<|user|>", "")
    code = code.replace("<|system|>", "")
    msg, output = kernel.execute(code)

    if msg['metadata']['status'] == "timeout":
        return res_type, 'Timed out'
    elif msg['metadata']['status'] == 'error':
        return res_type, clean_ansi_codes('\n'.join(kernel.get_error_msg(msg, verbose=True)))

    if 'text' in output:
        res_type = "text"
        res = output['text']
    elif 'data' in output:
        for key in output['data']:
            if 'text/plain' in key:
                res_type = "text"
                res = output['data'][key]
            elif 'image/png' in key:
                res_type = "image"
                res = output['data'][key]
                break

    if res_type == "image":
        return res_type, "[Image]" + res
    elif res_type == "text" or res_type == "traceback":
        res = res

    return res_type, res


def get_kernel():
    return kernel


def extract_code(text: str) -> str:
    pattern = r'```([^\n]*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    if len(matches)==0 or len(matches[-1])<2:
        return ""
    return matches[-1][1]


def load_model():
    global client, kernel
    client = ZhipuAI(api_key=Api_key) # 填写您自己的APIKey
    kernel = CodeKernel()

class Lock:
    def __init__(self):
        pass

    def get_waiting_threads(self):
        return 0

    def __enter__(self): 
        pass

    def __exit__(self, exc_type, exc_val, exc_tb): 
        pass