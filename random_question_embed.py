name: Build Windows EXE

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller

      - name: Build EXE
        run: pyinstaller -F -w random_question_embed.py

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: random_name
          path: dist/random_question_embed.exe
