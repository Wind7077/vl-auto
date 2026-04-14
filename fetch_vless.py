name: update-vless

on:
  workflow_dispatch:
  schedule:
    - cron: "0 */2 * * *"

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install requests

      - name: Run parser
        run: python fetch_vless.py

      - name: Commit results
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "github-actions@github.com"
          git add vless_normal_vpn.txt || true
          git commit -m "update vpn list" || true
          git push || true
