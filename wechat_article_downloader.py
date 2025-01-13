import pandas as pd
import os
import subprocess
import time
from urllib.parse import quote
from datetime import datetime
import re
import logging
from pathlib import Path
import random
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)

def sanitize_filename(filename):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '_', filename.strip())

def create_year_directory(date_str):
    year = date_str.split('-')[0]
    year_path = Path(year)
    year_path.mkdir(exist_ok=True)
    return year

def get_downloaded_files():
    downloaded = set()
    # Scan all year directories
    for year_dir in [d for d in os.listdir('.') if os.path.isdir(d) and d.isdigit()]:
        for file in os.listdir(year_dir):
            if file.endswith('.mhtml'):
                downloaded.add(os.path.join(year_dir, file))
    return downloaded

def download_article(url, title, date_str, max_retries=2, retry_delay=5):
    year_dir = create_year_directory(date_str)
    safe_title = sanitize_filename(title)
    output_path = os.path.join(year_dir, f"{safe_title}.html")
    
    # Skip if already downloaded and has content
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        logging.info(f"Skipping {title} - already downloaded")
        return True
    
                # Add random delay between downloads to avoid rate limiting
    sleep_time = random.uniform(1, 30)
    logging.info(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)

    for attempt in range(max_retries):
        try:
            # Remove existing invalid file if any
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Use Chrome to dump DOM
            chrome_cmd = [
                'google-chrome',
                '--headless',
                '--window-size=1920,1080',
                '--disable-gpu',
                '--dump-dom',
                '--run-all-compositor-stages-before-draw',
                '--incognito',
                '--virtual-time-budget=15000',
                url
            ]
            
            logging.info(f"Downloading: {title} (Attempt {attempt + 1}/{max_retries})")
            process = subprocess.run(chrome_cmd, capture_output=True, text=True, timeout=30)
            
            # Log Chrome's stderr if any
            if process.stderr:
                logging.warning(f"Chrome stderr: {process.stderr[:500]}...")
            
            # Check Chrome's return code
            if process.returncode != 0:
                logging.error(f"Chrome process failed with return code {process.returncode}")
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                continue
            
            # Save the stdout content to file
            if process.stdout:
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(process.stdout)
                    
                    file_size = os.path.getsize(output_path)
                    if file_size > 0:
                        logging.info(f"Successfully downloaded: {title} (size: {file_size} bytes)")
                        return True
                    else:
                        logging.warning(f"Downloaded content is empty for {title}")
                except Exception as e:
                    logging.error(f"Error saving content for {title}: {str(e)}")
            else:
                logging.warning(f"No content received from Chrome for {title}")
            
            if os.path.exists(output_path):
                os.remove(output_path)
            
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                    
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout while downloading {title} on attempt {attempt + 1}")
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logging.error(f"Error downloading {title} on attempt {attempt + 1}: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    

    logging.error(f"Failed to download {title} after {max_retries} attempts")
    return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Download WeChat articles from CSV file')
    parser.add_argument('csv_file', help='Path to the input CSV file')
    parser.add_argument('--order', choices=['regular', 'reverse', 'random'], 
                      default='regular', help='Sorting order for processing articles')
    args = parser.parse_args()

    try:
        # Read CSV file
        df = pd.read_csv(args.csv_file)
        
        # Sort based on the specified order
        df['发布日期'] = pd.to_datetime(df['发布日期'])
        if args.order == 'regular':
            df = df.sort_values('发布日期', ascending=True)
        elif args.order == 'reverse':
            df = df.sort_values('发布日期', ascending=False)
        elif args.order == 'random':
            df = df.sample(frac=1).reset_index(drop=True)
        
        # Get already downloaded files
        downloaded = get_downloaded_files()
        
        total = len(df)
        success_count = 0
        fail_count = 0
        
        for index, row in df.iterrows():
            if pd.isna(row['原文链接']) or not isinstance(row['原文链接'], str):
                logging.warning(f"Skipping row {index}: Invalid URL")
                continue
                
            date_str = row['发布日期'].strftime('%Y-%m-%d')
            title = row['标题']
            url = row['原文链接']
            
            # Download the article
            success = download_article(url, title, date_str)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                
            # Log progress
            logging.info(f"Progress: {index + 1}/{total} - Success: {success_count}, Failed: {fail_count}")
            
    except Exception as e:
        logging.error(f"Main process error: {str(e)}")
    finally:
        logging.info(f"Download completed. Total: {total}, Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    main() 