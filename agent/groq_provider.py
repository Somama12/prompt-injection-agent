"""Groq chat-completion transport; never upgrades billing or switches providers."""
import os
import requests

ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'
REASONING_EFFORT = 'low'


def complete(prompt, *, system_instruction, model, temperature, max_output_tokens):
    key = os.environ.get('GROQ_API_KEY')
    if not key:
        raise RuntimeError('GROQ_API_KEY is not configured in the local .env file.')
    if os.environ.get('GROQ_FREE_PLAN_CONFIRMED') != '1':
        raise RuntimeError('Confirm the Groq account is on the free plan, then set GROQ_FREE_PLAN_CONFIRMED=1. This flag does not enforce account billing.')
    messages = []
    if system_instruction:
        messages.append({'role':'system','content':system_instruction})
    messages.append({'role':'user','content':prompt})
    payload = dict(model=model, messages=messages, temperature=temperature,
                   max_completion_tokens=max_output_tokens, stream=False)
    if model.startswith('openai/gpt-oss-'):
        payload['reasoning_effort'] = REASONING_EFFORT
    response = requests.post(ENDPOINT, headers={'Authorization':f'Bearer {key}'},
                             json=payload, timeout=(10,60), allow_redirects=False)
    # Do not expose response bodies or credentials in provider errors.
    if response.status_code == 429:
        raise RuntimeError('Groq free-plan allowance reached; stop and wait for quota reset. No paid fallback.')
    if response.status_code != 200:
        raise RuntimeError(f'Groq HTTP {response.status_code}; request did not complete.')
    try:
        data = response.json()
        choice = data['choices'][0]
        if choice.get('finish_reason') == 'length':
            raise RuntimeError('Groq completion exhausted the output budget; not a valid completed reply.')
        content = choice['message'].get('content')
        if not isinstance(content,str) or not content.strip():
            raise RuntimeError('Groq returned no usable answer text.')
        return content.strip()
    except (KeyError,IndexError,TypeError,ValueError) as exc:
        raise RuntimeError('Groq returned an invalid completion envelope.') from exc
