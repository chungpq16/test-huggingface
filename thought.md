We have a LLM farm. We can trigger llm by api endpoint. This is curl command when we want to test a user input.

```
curl -X 'POST' \
 'https://dummy.chat/it/application/llamashared/prod/v1/chat/completions' \
 -H 'accept: application/json' \
 -H 'KeyId: <token>' \
 -H 'Content-Type: application/json' \
 -d '{
 "messages": [{"role": "user", "content": "Hello"}],
 "max_tokens": 2048,
 "model": "meta-llama/Meta-Llama-3-70B-Instruct"
 }'
````


Because this api endpoint end with  `/chat/completions` so I think it is compatiable with OPENAI API ? If so, can we use langchain library to make a chatbot ? If yes, please help me to create a very simple chatbot:

- use langchain for llm integrate
- use streamlit for frontend API
- a hello tool (very simple tool)
- bind tool to llm
- let llm decide if we need call tools, or directly call LLM
- make everything minimal, don't make it too complicated.

