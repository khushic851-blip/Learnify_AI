import requests

url = "http://localhost:11434/api/generate"

data = {
    "model": "llama3.2",
    "prompt": "Explain Artificial Intelligence in very easy language for a student.",
    "stream": False
}

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print("\n===== LEARNIFY AI =====\n")
    print(result["response"])
else:
    print("Error:", response.status_code)
    print(response.text)