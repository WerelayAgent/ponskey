import os
import re
import urllib.request
from urllib.parse import urljoin, unquote, urlparse, parse_qs

base_url = 'https://pumpkey.tech'
output_dir = r'C:\Tools\ponskey'
os.makedirs(output_dir, exist_ok=True)

pages_to_visit = {'/'}
visited_pages = set()
asset_urls = set()

rebrand_patterns = [
    (re.compile(r'PumpKey', re.IGNORECASE), 'PonsKey Market'),
    (re.compile(r'pumpkey\.tech', re.IGNORECASE), 'ponskeymarket.com'),
    (re.compile(r'Solana', re.IGNORECASE), 'Robinhood Chain'),
    (re.compile(r'\bSOL\b'), 'ETH'),
    (re.compile(r'x\.com/pumpkey_tech', re.IGNORECASE), 'x.com/PonskeyMarket'),
    (re.compile(r'twitter\.com/pumpkey_tech', re.IGNORECASE), 'x.com/PonskeyMarket'),
    (re.compile(r'x\.com/pumpkey', re.IGNORECASE), 'x.com/PonskeyMarket'),
    (re.compile(r'twitter\.com/pumpkey', re.IGNORECASE), 'x.com/PonskeyMarket'),
    (re.compile(r'pumpkey-icon', re.IGNORECASE), 'ponskey-icon')
]

def get_content(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as res:
            return res.read()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def download_asset(url, save_path):
    if os.path.exists(save_path): return
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    content = get_content(url)
    if content:
        with open(save_path, 'wb') as f:
            f.write(content)

while pages_to_visit:
    page = pages_to_visit.pop()
    if page in visited_pages: continue
    visited_pages.add(page)
    
    page_url = base_url + page
    print(f"Fetching {page_url}")
    html_bytes = get_content(page_url)
    if not html_bytes: continue
    
    html = html_bytes.decode('utf-8')
    
    # Generic extraction for src="/..." and href="/..."
    srcs = re.findall(r'src=[\"\'](/[^\"\']+)[\"\']', html)
    hrefs = re.findall(r'href=[\"\'](/[^\"\']+)[\"\']', html)
    for p in srcs + hrefs:
        if not p.startswith('//'):
            asset_urls.add(p.split('?')[0])

    for pattern, replacement in rebrand_patterns:
        html = pattern.sub(replacement, html)
        
    save_path = os.path.join(output_dir, 'index.html') if page == '/' else os.path.join(output_dir, page.strip('/') + '.html')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html)

print(f"Found {len(asset_urls)} assets to process.")

# Process assets
for path in asset_urls:
    if not path.startswith('/'): path = '/' + path
    # If the file path changed due to rebranding (like pumpkey-icon-500.png -> ponskey-icon-500.png), download from the original name
    original_path = path
    for pattern, replacement in rebrand_patterns:
        pass # Wait, if we use the unbranded original_path to download, we need the original URL.
    
    # We found `original_path` before rebranding HTML, so it is the correct URL
    dl_url = base_url + original_path
    
    # Now rebrand the local filename
    local_path = original_path
    for pattern, replacement in rebrand_patterns:
        local_path = pattern.sub(replacement, local_path)
    
    local_path_full = os.path.join(output_dir, unquote(local_path).lstrip('/').replace('/', '\\'))
    download_asset(dl_url, local_path_full)
    
    if local_path_full.endswith('.js') or local_path_full.endswith('.css'):
        if os.path.exists(local_path_full):
            try:
                with open(local_path_full, 'r', encoding='utf-8') as f:
                    content = f.read()
                original_content = content
                
                # Also apply rebranding inside assets! Wait, if there are asset URLs inside JS/CSS, we need them too.
                # Just string replacement for now.
                for pattern, replacement in rebrand_patterns:
                    content = pattern.sub(replacement, content)
                    
                if content != original_content:
                    with open(local_path_full, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception as e:
                pass
                
# Find assets inside JS/CSS that were just downloaded
new_assets = set()
for root, dirs, files in os.walk(output_dir):
    for file in files:
        if file.endswith('.js') or file.endswith('.css'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Find /assets/... or other paths inside CSS/JS
                paths = re.findall(r'[\"\'](/assets/[^\"\']+)[\"\']', content)
                for p in paths:
                    new_assets.add(p)
            except:
                pass

for path in new_assets:
    dl_url = base_url + path
    # Rebrand path if needed
    local_path = path
    for pattern, replacement in rebrand_patterns:
        local_path = pattern.sub(replacement, local_path)
    local_path_full = os.path.join(output_dir, unquote(local_path).lstrip('/').replace('/', '\\'))
    download_asset(dl_url, local_path_full)
    
print("Full scrape and rebrand complete.")
