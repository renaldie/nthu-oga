import json
import os
import sys
import traceback
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
        
        print(f"Sending request to {URL}")
        resp = requests.get(URL, headers=headers, timeout=30)
        status_code = resp.status_code
        print(f"Received response with status code: {status_code}")
        
        if status_code != 200:
            print(f"Unexpected status code: {status_code}")
            print(f"Response content: {resp.text[:500]}...")
            resp.raise_for_status()
        
        content_type = resp.headers.get('Content-Type', '')
        print(f"Content type: {content_type}")
        
        # Print first 200 characters of response for debugging
        print(f"Response preview: {resp.text[:200]}...")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Debug: print all found div elements
        all_divs = soup.find_all('div')
        print(f"Found {len(all_divs)} div elements total")
        
        # Look for mtitle class divs
        mtitle_divs = soup.find_all('div', class_='mtitle')
        print(f"Found {len(mtitle_divs)} div elements with class 'mtitle'")
        
        if len(mtitle_divs) == 0:
            print("No mtitle divs found. Checking for alternative selectors...")
            # Try to find some common elements to understand the structure
            headlines = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            print(f"Found {len(headlines)} headline elements")
            if headlines:
                print("Sample headlines:")
                for i, h in enumerate(headlines[:5]):
                    print(f"  {i+1}. {h.text.strip()}")
            
            links = soup.find_all('a')
            print(f"Found {len(links)} link elements")
            if links:
                print("Sample links:")
                for i, a in enumerate(links[:5]):
                    print(f"  {i+1}. Text: {a.text.strip()}, Href: {a.get('href', 'N/A')}")
        
        current_data = []
        for div in mtitle_divs:
            if div.a:
                title = div.a.text.strip()
                url = div.a.get('href', '')
                print(f"Found item: {title} - {url}")
                
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
        
        print(f"Successfully scraped {len(current_data)} items")
        
        # If no items found but page loaded, attempt a simpler approach
        if len(current_data) == 0 and status_code == 200:
            print("No items found with primary selector. Trying alternative approach...")
            # Try to find all links with news-like patterns
            news_links = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.text.strip()
                if text and href and ('news' in href.lower() or 'article' in href.lower() or 'post' in href.lower()):
                    news_links.append({
                        'title': text,
                        'url': href if href.startswith(('http://', 'https://')) else f"https://oga.site.nthu.edu.tw{href if href.startswith('/') else '/'+href}",
                        'scrape_date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if news_links:
                print(f"Found {len(news_links)} items with alternative approach")
                current_data = news_links
        
        if len(current_data) > 0:
            return current_data
        else:
            # Create a minimal fake data entry to avoid failure
            print("WARNING: No data could be scraped, creating fallback data")
            return [{
                'title': "Scraper Alert: No data found",
                'url': URL,
                'scrape_date': datetime.now().strftime("%Y-%m-%d")
            }]
        
    except requests.exceptions.RequestException as e:
        print(f"Error scraping website: {str(e)}")
        traceback.print_exc()
        # Return a minimal data item to prevent complete failure
        return [{
            'title': f"Scraper Error: {str(e)}",
            'url': URL,
            'scrape_date': datetime.now().strftime("%Y-%m-%d")
        }]
    except Exception as e:
        print(f"Unexpected error in scraper: {str(e)}")
        traceback.print_exc()
        # Return a minimal data item to prevent complete failure
        return [{
            'title': f"Scraper Unexpected Error: {str(e)}",
            'url': URL,
            'scrape_date': datetime.now().strftime("%Y-%m-%d")
        }]

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
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Debug environment variables
        print("Environment variables:")
        for key, value in os.environ.items():
            if not key.startswith(('PATH', 'PYTHONPATH')):  # Skip long path variables
                print(f"  {key}: {value}")
        
        # List directory contents for debugging
        print("Directory structure:")
        for root, dirs, files in os.walk('.'):
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{sub_indent}{f}")
        
        ensure_data_directory()
        print("Data directory check completed")
        
        filename = 'data/nthu_oga_posts.json'
        
        # Print system path for debugging
        print(f"System path: {sys.path}")
        
        # Test file access
        print("Testing file access:")
        try:
            with open('README.md', 'r') as f:
                print("  README.md is readable")
        except Exception as e:
            print(f"  README.md access error: {str(e)}")
        
        # Test data directory
        print("Testing data directory:")
        try:
            test_file = 'data/test.txt'
            with open(test_file, 'w') as f:
                f.write('test')
            print(f"  Successfully wrote to {test_file}")
            os.remove(test_file)
            print(f"  Successfully removed {test_file}")
        except Exception as e:
            print(f"  Data directory write test error: {str(e)}")
        
        print("Testing requests module:")
        try:
            test_url = "https://httpbin.org/get"
            response = requests.get(test_url)
            print(f"  Requests test successful, status code: {response.status_code}")
        except Exception as e:
            print(f"  Requests test error: {str(e)}")
        
        print("Starting web scraping...")
        current_data = scrape_nthu_oga()
        if not current_data:
            print("No data scraped, exiting with error")
            sys.exit(1)
        
        print(f"Successfully scraped {len(current_data)} items")
            
        previous_data = None
        if os.path.exists(filename):
            print(f"Found existing file: {filename}")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    previous_data = json.load(f)
                print(f"Loaded previous data from {filename}")
            except Exception as e:
                print(f"Error reading previous data from {filename}: {str(e)}")
                print("Continuing with empty previous data")
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
            if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ:
                print("Running in CI environment, attempting git operations")
                os.system('git config --global user.name "GitHub Action"')
                os.system('git config --global user.email "action@github.com"')
                os.system('git add data/*.json')
                commit_result = os.system('git commit -m "Update NTHU OGA posts data"')
                print(f"Git commit result: {commit_result}")
                push_result = os.system('git push')
                print(f"Git push result: {push_result}")
            else:
                print("Not running in CI environment, skipping git operations")
        else:
            print("No updates found")
            # Still save the current data to update the scrape date
            save_json_safely(current_data, filename)
        
        print("Script completed successfully")
                
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)  # Exit with error code

if __name__ == '__main__':
    main()
