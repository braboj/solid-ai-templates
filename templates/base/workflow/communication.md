# Communication Preferences
[ID: base-communication]

How the agent communicates with the user during a session. These are
override-friendly defaults — a downstream project MAY add its own
shorthand verbs and MUST preserve these if it references this template.

## Defaults

- Concise, direct answers — no filler, no preamble, no restating the
  request before answering
- State your preferred option after presenting suggestions — do not make
  the user choose when you have a view
- Ask before assuming scope on an ambiguous instruction — do not silently
  expand it

## Shorthand verbs

- **"next"** — move to the next item without asking for confirmation
- **"stop"** — stop working; this does NOT mean save or commit
- **"yes"** — proceed; do not summarise what you are about to do, just
  do it
