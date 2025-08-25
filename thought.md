We have a LLM farm. We can trigger llm by api endpoint. This is simple verison of curl command when we want to test a user input.

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


The full request body is 

```
{
 "messages": [
 {
 "content": "string",
 "role": "string",
 "name": "string"
 },
 {
 "content": "string",
 "role": "string",
 "name": "string"
 },
 {
 "role": "string",
 "content": "string",
 "function_call": {
 "arguments": "string",
 "name": "string"
 },
 "name": "string",
 "tool_calls": [
 {
 "id": "string",
 "function": {
 "arguments": "string",
 "name": "string"
 },
 "type": "string"
 }
 ]
 },
 {
 "content": "string",
 "role": "string",
 "tool_call_id": "string"
 },
 {
 "content": "string",
 "name": "string",
 "role": "string"
 },
 {
 "role": "string",
 "content": "string",
 "name": "string"
 }
 ],
 "model": "string",
 "frequency_penalty": 0,
 "logit_bias": "string",
 "logprobs": false,
 "top_logprobs": 0,
 "max_tokens": "string",
 "n": 1,
 "presence_penalty": 0,
 "response_format": {
 "type": "text"
 },
 "seed": 9223372036854776000,
 "stop": "string",
 "stream": false,
 "stream_options": {
 "include_usage": "string"
 },
 "temperature": 0.7,
 "top_p": 1,
 "tools": [
 {
 "type": "function",
 "function": {
 "name": "string",
 "description": "string",
 "parameters": "string",
 "additionalProp1": "string",
 "additionalProp2": "string",
 "additionalProp3": "string"
 }
 }
 ],
 "tool_choice": "none",
 "user": "string",
 "best_of": "string",
 "use_beam_search": false,
 "top_k": -1,
 "min_p": 0,
 "repetition_penalty": 1,
 "length_penalty": 1,
 "early_stopping": false,
 "ignore_eos": false,
 "min_tokens": 0,
 "stop_token_ids": [
 "string"
 ],
 "skip_special_tokens": true,
 "spaces_between_special_tokens": true,
 "echo": false,
 "add_generation_prompt": true,
 "add_special_tokens": false,
 "include_stop_str_in_output": false,
 "guided_json": "string",
 "guided_regex": "string",
 "guided_choice": [
 "string"
 ],
 "guided_grammar": "string",
 "guided_decoding_backend": "string",
 "guided_whitespace_pattern": "string",
 "additionalProp1": "string",
 "additionalProp2": "string",
 "additionalProp3": "string"
}
```
  
Due to when they use vllm to serve local model, they didn't use --enable-auto-tool-choice and --tool-call-parser  --> so by default, this api endpoint is not support for function calling

Because this api endpoint end with  `/chat/completions` so I think it is compatiable with OPENAI API ? 

Please read carefully full body of payload, and remember all options we can use for our application.  Please build application with below requirement:

- option to disable verify of ssl certificate when call API endpoint 
- use streamlit for frontend API
- a hello tool (very simple tool) and one other dummy tool
- Use LangChain’s create_react_agent function allows binding tools explicitly to an LLM and manages the interaction.
- let AI Agent decide if we need call tools, or directly call LLM
- make everything minimal, don't make it too complicated.
- enable debug log for easier troubleshooting
- make folder structure for each componenet (llm, tools, streamlit,... ) for easier further development and maintainance.
- create gitignore for .env file
- api endpoint, key,...  should load from .env file
