# Scale customer app (frontend branch, demo)

A phone-sized banking app for the demo: home (balance and activity), a payment detail, and the
Scale assistant in the bottom-right. Conversations are scripted from the organisers' practice
cases (Banking 002, 001, 015, 023). Each one plays out as a live case history in history.md style,
then a reply read aloud by an ElevenLabs voice (pre-generated in `audio/`). No live AI calls.

```bash
python3 -m http.server 8765 --directory app
```

Then open http://localhost:8765.
