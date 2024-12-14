- add message store functionality from ask.py
- add to_chat function which opens interactive chat
- add save_to_obsidian function (and abstract that to its own script in Leviathan, so we can import here)

### Example usage:

Twig allows you to construct prompts in this structure:
```xml
<head>
<context>
<tail>
```

Debugging my python test scripts with OpenAI's o1-preview model:
```bash
$ echo "# chain.py\n$(cat ../chain/chain.py)\n\n# test_chain.py\n$(cat ../tests/test_chain.py)\n\n# model.py\n$(cat model.py)\n\n# test_model.py\n$(cat ../tests/test_model.py)" | twig "Look at my scripts and their associated pytest scripts below." -a "I am new to unit testing, please critique my test scripts. The goal is to teach me, so introduce concepts related to testing and overall provide me with a tutorial for best practices for testing python code. Your response should be substantial, with short code examples, but do NOT rewrite my code. Your response should be around 1,500 words in length." -m "o1-preview"
```
Explanation of above:
- I echo the contents of my scripts and test scripts and pipe it to twig.
- twig intakes the stdin (this is the context)
- I write the beginning of the prompt (the head)
- -a appends text to the bottom of the prompt (the tail)

Resulting prompt:
```python
"""
<head>
Look at my scripts and their associated pytest scripts below.
</head>

<context>
# chain.py
... [all of the code]
[my other scripts as well]
</context>

<tail>
I am new to unit testing, please critique my test scripts. The goal is to teach me, so introduce concepts related to testing and overall provide me with a tutorial for best practices for testing python code. Your response should be substantial, with short code examples, but do NOT rewrite my code. Your response should be around 1,500 words in length.
</tail>
"""
```
