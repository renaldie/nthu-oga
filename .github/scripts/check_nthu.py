import json
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def send_notification(changes):
    """
    Send a single consolidated notification for all changes
    changes: list of new or updated items
    """
    if not changes:
        print("No changes to notify")
        return
        
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = [f"Updates in NTHU OGA Posts ({current_time})\n\n"]
    
    body.append("New updates in OGA Posts:\n")
    body.append("https://oga.site.nthu.edu.tw/p/403-1524-8945-1.php?Lang=en\n")
    
    for item in changes:
        body.append(f"{item['title']} - {item['url']}\n")
    
    # Print the notification content directly (will be captured for email)
    print(''.join(body))

def scrape_nthu_oga():
    """Scrape NTHU OGA website for posts"""
    print("Starting scraping NTHU OGA website...")
    
    URL = 'https://oga.site.nthu.edu.tw/p/403-1524-8945-1.php?Lang=en'
    
    try:
        # Add headers to make request more like a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        resp = requests.get(URL, headers=headers, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        current_data = []
        for div in soup.find_all('div', class_='mtitle'):
            if div.a:
                title = div.a.text.strip()
                url = div.a.get('href', '')
                
                # Fix relative URLs
                if url and not url.startswith(('http://', 'https://')):
                    base_url = 'https://oga.site.nthu.edu.tw'
                    url = base_url + url if url.startswith('/') else base_url + '/' + url
                
                current_item = {
                    'title': title,
                    'url': url,
                    'scrape_date': datetime.now().strftime("%Y-%m-%d")
                }
                current_data.append(current_item)
        
        print(f"Scraped {len(current_data)} items")
        return current_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping website: {str(e)}")
        return []

def compare_data(current_data, previous_data):
    """Compare current and previous data and return list of changes"""
    if not previous_data:
        return current_data  # All items are new if no previous data

    updates = []
    for current_item in current_data:
        is_new = True
        for prev_item in previous_data:
            if current_item['title'] == prev_item['title'] and current_item['url'] == prev_item['url']:
                is_new = False
                break
        if is_new:
            updates.append(current_item)
    return updates

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            print(f"Created directory: {data_dir}")
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            raise

def save_json_safely(data, filename):
    """Safely save JSON data to file with error handling"""
    try:
        # First write to a temporary file
        temp_filename = filename + '.tmp'
        with open(temp_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Then rename it to the target file (atomic operation)
        os.replace(temp_filename, filename)
        print(f"Successfully saved: {filename}")
    except Exception as e:
        print(f"Error saving file {filename}: {str(e)}")
        # Try one more time with force write
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved with force write: {filename}")
        except Exception as e:
            print(f"Critical error saving file {filename}: {str(e)}")
            raise

def main():
    print("Starting main function...")
    try:
        ensure_data_directory()
        print("Data directory check completed")
        
        filename = 'data/nthu_oga_posts.json'
        print(f"Working directory: {os.getcwd()}")
        
        # List directory contents for debugging
        print(f"Directory contents: {os.listdir('.')}")
        
        current_data = scrape_nthu_oga()
        if not current_data:
            print("No data scraped, exiting")
            return
            
        previous_data = None
        if os.path.exists(filename):
            print(f"Found existing file: {filename}")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    previous_data = json.load(f)
                print(f"Loaded previous data from {filename}")
            except Exception as e:
                print(f"Error reading previous data from {filename}: {str(e)}")
        else:
            print(f"No existing file found at {filename}")
        
        updates = compare_data(current_data, previous_data)
        if updates:
            print(f"Found {len(updates)} updates")
            send_notification(updates)
            
            # Always save current data
            print(f"Attempting to save data")
            save_json_safely(current_data, filename)
            print(f"Saved data")
            
            # After sending notification, commit changes if not running in debug mode
            if 'CI' in os.environ:
                os.system('git config --global user.name "GitHub Action"')
                os.system('git config --global user.email "action@github.com"')
                os.system('git add data/*.json')
                os.system('git commit -m "Update NTHU OGA posts data"')
                os.system('git push')
                print("Changes committed and pushed")
        else:
            print("No updates found")
            # Still save the current data to update the scrape date
            save_json_safely(current_data, filename)
                
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback = sys.exc_info()[2]
        print(f"Error occurred at line {traceback.tb_lineno}")
        sys.exit(1)  # Exit with error code

if __name__ == '__main__':
    main()
