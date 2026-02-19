#!/bin/bash
cd /home/kavia/workspace/code-generation/voice-assistant-platform-223119/voice_assistant_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

