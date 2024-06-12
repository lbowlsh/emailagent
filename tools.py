import os
from dotenv import load_dotenv
from crewai_tools import BaseTool
import requests
import json

load_dotenv()

print("LOCAL_OLLAMA_URL:", os.getenv('LOCAL_OLLAMA_URL'))
print("LOCAL_MODEL:", os.getenv('LOCAL_MODEL'))

class OllamaTool(BaseTool):
    name: str = "OllamaTool"
    description: str = "Tool to interact with local Ollama API to generate text using specific models."

    def _run(self, prompt: str) -> str:
        api_url = os.getenv('LOCAL_OLLAMA_URL')
        model = os.getenv('LOCAL_MODEL')
        # 确保 prompt 是字符串
        if not isinstance(prompt, str):
            prompt = str(prompt)

        payload = {
            "prompt": prompt,
            "model": model
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers, stream=True)
        print("Response status code:", response.status_code)  # 打印状态码
        
        if response.status_code == 200:
            full_response = ""
            try:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        print("Decoded line:", decoded_line)  # 打印解码后的每行内容
                        try:
                            json_line = json.loads(decoded_line)
                            full_response += json_line.get('response', '')
                            if json_line.get('done', False):
                                break
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {str(e)}")
                            continue  # 继续处理下一行
                return full_response if full_response else 'No text returned from model'
            except Exception as e:
                print(f"Error: {str(e)}")
                print("Raw response content:", response.content.decode())  # 打印原始响应内容进行调试
                return f"Error: {response.content.decode()}"  # 返回原始响应内容进行调试
        else:
            return f"Error: {response.status_code}, {response.text}"
        
    def bind(self, stop=None):
        # This method should return a function that takes a prompt and returns a response
        def run_prompt(prompt):
            return self._run(prompt)
        return run_prompt
        

# if __name__=="__main__":
#     tool = OllamaTool()
#     result = tool._run("why is the ocean blue?")
#     print(result) 