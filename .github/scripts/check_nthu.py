name: Check NTHU OGA Posts
on:
  schedule:
    - cron: '0 8 * * *'  # Runs at 8:00 UTC (adjust as needed)
  workflow_dispatch:  # Allows manual triggering

permissions:
  contents: write
  actions: write

jobs:
  check_changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Create data directory
        run: mkdir -p data
        
      - name: Check NTHU OGA posts
        run: |
          # Run the script and capture both stdout and stderr
          python scripts/check_nthu.py > output.txt 2>&1
          cat output.txt
          
          # Check if the script identified any updates
          if grep -q "Updates in NTHU OGA Posts" output.txt; then
            # Extract only the notification part
            notification_content=$(sed -n '/Updates in NTHU OGA Posts/,$p' output.txt)
            echo "NOTIFICATION_CONTENT<<EOF" >> $GITHUB_ENV
            echo "$notification_content" >> $GITHUB_ENV
            echo "EOF" >> $GITHUB_ENV
            echo "CHANGES_DETECTED=true" >> $GITHUB_ENV
          fi

      - name: Send email
        if: env.CHANGES_DETECTED == 'true'
        uses: dawidd6/action-send-mail@v4
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: Updates in NTHU OGA Posts
          to: ${{ secrets.EMAIL_USERNAME }}
          from: GitHub Action
          body: ${{ env.NOTIFICATION_CONTENT }}
