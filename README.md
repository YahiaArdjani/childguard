# ChildGuard — Frontend MVP v0.1

An offline, browser-only prototype for demonstrating a mock message-safety analysis flow. It does not send, save, or classify messages using real NLP.

## Run it

Open `index.html` in a modern browser. No installation, server, or external service is required.

## Demo behavior

- Type a message to enable **Analyze message**.
- The prototype shows a brief loading state, then mock data.
- Messages containing demo keywords such as `stupid`, `hate`, `hurt you`, or `threat` show the potentially harmful result. Other messages show Safe.
- For visual testing of the error state, run `ChildGuard.showError()` in the browser console.

The keyword matching exists only to preview the interface; it is not real content classification.
