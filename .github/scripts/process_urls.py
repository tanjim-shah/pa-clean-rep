# # #!/usr/bin/env python3
# # # .github/scripts/process_urls.py

# # import os
# # import csv
# # import time
# # import json
# # import smtplib
# # import requests
# # import pandas as pd
# # import mimetypes
# # import re
# # import zipfile
# # import shutil
# # from io import BytesIO, StringIO
# # from email.mime.text import MIMEText
# # from email.mime.multipart import MIMEMultipart
# # from email.mime.application import MIMEApplication
# # from pathlib import Path
# # from PIL import Image
# # from datetime import datetime
# # from google import genai
# # from google.genai import types

# # # Constants
# # BATCH_SIZE = 5
# # URLS_FILE = "urls.txt"
# # PINS_DIR = "pins"
# # DATA_DIR = "data"
# # PINS_PER_URL = 25  # Reduce number of pins per URL for GitHub Actions

# # # Email configuration
# # TO_EMAIL = "beacleaner0@gmail.com"
# # FROM_EMAIL = "limon.working@gmail.com"
# # APP_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# # # Initialize API clients
# # genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# # def ensure_directory_exists(directory):
# #     """Ensure a directory exists, creating it if needed"""
# #     os.makedirs(directory, exist_ok=True)
# #     return directory

# # def ensure_file_exists(file_path, default_content=""):
# #     """Ensure a file exists, creating it with default content if needed"""
# #     directory = os.path.dirname(file_path)
# #     if directory and not os.path.exists(directory):
# #         os.makedirs(directory, exist_ok=True)
        
# #     if not os.path.exists(file_path):
# #         with open(file_path, "w") as f:
# #             f.write(default_content)
# #     return file_path

# # def read_urls(file_path):
# #     """Read URLs from a text file"""
# #     if not os.path.exists(file_path):
# #         return []
        
# #     with open(file_path, "r") as f:
# #         return [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]

# # def write_urls(file_path, urls):
# #     """Write URLs to a file"""
# #     with open(file_path, "w") as f:
# #         for url in urls:
# #             f.write(f"{url}\n")

# # def save_binary_file(file_name, data):
# #     """Save binary data to a file"""
# #     with open(file_name, "wb") as f:
# #         f.write(data)
# #     return file_name

# # def compress_image(image_path, quality=85):
# #     """Compress image and convert to WebP format"""
# #     try:
# #         with Image.open(image_path) as img:
# #             webp_path = f"{os.path.splitext(image_path)[0]}.webp"
# #             img.save(webp_path, 'WEBP', quality=quality)
# #             if os.path.exists(image_path):
# #                 os.remove(image_path)  # Remove original file
# #             return webp_path
# #     except Exception as e:
# #         print(f"Image compression error: {e}")
# #         return image_path

# # def upload_to_cloudinary(file_path, resource_type="image"):
# #     """Upload file to Cloudinary using direct API call"""
# #     url = f"https://api.cloudinary.com/v1_1/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/{resource_type}/upload"
# #     payload = {
# #         'upload_preset': 'ml_default',
# #         'api_key': os.environ.get('CLOUDINARY_API_KEY')
# #     }
# #     try:
# #         with open(file_path, 'rb') as f:
# #             files = {'file': f}
# #             response = requests.post(url, data=payload, files=files)
# #         if response.status_code == 200:
# #             return response.json()['secure_url']
# #         print(f"Upload failed: {response.text}")
# #         return None
# #     except Exception as e:
# #         print(f"Upload error: {e}")
# #         return None

# # def generate_image_with_gemini(prompt, file_name):
# #     """Generate an image using Gemini 2.0 Flash image generation model"""
# #     try:
# #         model = "gemini-2.0-flash-exp-image-generation"
# #         contents = [types.Content(
# #             role="user",
# #             parts=[types.Part.from_text(text=prompt)]
# #         )]

# #         response = genai_client.models.generate_content(
# #             model=model,
# #             contents=contents,
# #             config=types.GenerateContentConfig(response_modalities=["image", "text"])
# #         )

# #         # Process response to extract image
# #         if response.candidates and response.candidates[0].content.parts:
# #             for part in response.candidates[0].content.parts:
# #                 if hasattr(part, 'inline_data') and part.inline_data:
# #                     inline_data = part.inline_data
# #                     file_ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
# #                     file_path = f"{file_name}{file_ext}"

# #                     # Save the file
# #                     save_binary_file(file_path, inline_data.data)

# #                     # Compress and convert to WebP
# #                     final_path = compress_image(file_path)

# #                     print(f"Image generated and saved to: {final_path}")
# #                     return inline_data.data, inline_data.mime_type, final_path

# #         raise Exception("No image data found in response")
# #     except Exception as e:
# #         print(f"Error generating image: {str(e)}")
# #         return None, None, None

# # def generate_pin_content(url, pins_per_url=5):
# #     """Generate Pinterest pin content using Gemma model"""
# #     try:
# #         model = "gemma-3-27b-it"  # Using Gemma model
# #         contents = [types.Content(
# #             role="user",
# #             parts=[types.Part.from_text(text=f"""
# #             Create {pins_per_url} unique Pinterest pin ideas for the blog post at {url}.
# #             For each pin, provide:
# #             1. An engaging title (under 70 characters)
# #             2. A compelling description (must be 350-400 characters) that includes hashtags at the end
# #             3. 3-4 relevant keywords separated by commas
            
# #             The description MUST end with relevant hashtags like #Keyword1 #Keyword2.
            
# #             Format your response as CSV data with these exact columns:
# #             Title,Description,Keywords
            
# #             Make each pin unique with different angles or highlights from the blog post.
# #             Include calls to action and emotional appeals in descriptions.
# #             Do NOT include quotation marks around the title or description.
# #             """)]
# #         )]

# #         generate_content_config = types.GenerateContentConfig(
# #             temperature=1,
# #             top_p=0.95,
# #             top_k=64,
# #             max_output_tokens=8192,
# #             response_mime_type="text/plain",
# #         )

# #         print(f"Generating pin content with Gemma model for URL: {url}")
# #         response = genai_client.models.generate_content(
# #             model=model,
# #             contents=contents,
# #             config=generate_content_config
# #         )

# #         return response.text if response.text else "No content generated"
# #     except Exception as e:
# #         print(f"Error generating pin content: {str(e)}")
# #         return f"Error: {str(e)}"

# # def generate_board_category(title, keywords):
# #     """Generate Pinterest board category using Gemma model"""
# #     try:
# #         model = "gemma-3-27b-it"
# #         contents = [types.Content(
# #             role="user",
# #             parts=[types.Part.from_text(text=f"""
# #             Analyze this Pinterest pin title and keywords, then suggest ONE specific board name
# #             that would be most appropriate for this content on Pinterest.

# #             Title: {title}
# #             Keywords: {keywords}

# #             Return ONLY the board name, nothing else. The board name should be:
# #             - 2-3 words maximum
# #             - Descriptive of the content category
# #             - End with "ideas" or "inspiration"
# #             - Lowercase with hyphens between words (e.g., "home-decor-ideas")
# #             - Common Pinterest board category that would have wide appeal
# #             - NOT include the brand name or website name

# #             JUST RETURN THE BOARD NAME ONLY.
# #             """)]
# #         )]

# #         generate_content_config = types.GenerateContentConfig(
# #             temperature=0.2,  # Lower temperature for more consistent results
# #             top_p=0.95,
# #             top_k=40,
# #             max_output_tokens=20,  # Short response
# #             response_mime_type="text/plain",
# #         )

# #         response = genai_client.models.generate_content(
# #             model=model,
# #             contents=contents,
# #             config=generate_content_config
# #         )

# #         board_name = response.text.strip().lower()

# #         # Clean up the board name
# #         board_name = re.sub(r'[^a-z0-9\s-]', '', board_name)
# #         board_name = re.sub(r'[\s]+', '-', board_name)
# #         board_name = board_name.strip('-')

# #         # Fallback if the model returns something invalid
# #         if not board_name or len(board_name) < 3:
# #             return "home-inspiration"

# #         return board_name
# #     except Exception as e:
# #         print(f"Error generating board category: {str(e)}")
# #         return "home-inspiration"  # Default fallback

# # def parse_csv_content(csv_content):
# #     """Parse CSV content from API response"""
# #     pins = []
# #     lines = csv_content.strip().split('\n')

# #     # Skip header if present
# #     start_idx = 0
# #     if 'Title' in lines[0] and 'Description' in lines[0]:
# #         start_idx = 1

# #     # Process each line
# #     for i in range(start_idx, len(lines)):
# #         line = lines[i]
# #         if not line.strip():
# #             continue

# #         try:
# #             # Handle potential CSV formatting issues
# #             if ',' in line:
# #                 parts = line.split(',')
# #                 if len(parts) >= 3:
# #                     title = parts[0].strip()
# #                     description = ','.join(parts[1:-1]).strip()  # Join all middle parts in case descriptions have commas
# #                     keywords = parts[-1].strip()

# #                     # Remove quotation marks from title and description
# #                     title = title.strip('"\'')
# #                     description = description.strip('"\'')

# #                     pins.append({
# #                         'Title': title,
# #                         'Description': description,
# #                         'Keywords': keywords
# #                     })
# #         except Exception as e:
# #             print(f"Error parsing line: {line}, Error: {str(e)}")

# #     return pins

# # def send_email_notification(to_email, from_email, app_password, csv_data, subject="Pinterest Pin Generation Complete"):
# #     """Send email with CSV attachment"""
# #     if not app_password:
# #         print("No email password provided. Skipping email notification.")
# #         return False
        
# #     msg = MIMEMultipart()
# #     msg['From'] = from_email
# #     msg['To'] = to_email
# #     msg['Subject'] = f"{subject} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# #     # Email body
# #     body = f"""
# #     Hello,

# #     Your Pinterest pin generation process has completed successfully.
# #     The CSV file with the generated pins is attached.

# #     Time of completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# #     """

# #     msg.attach(MIMEText(body, 'plain'))

# #     # Attach CSV - ensure it's bytes
# #     if isinstance(csv_data, StringIO):
# #         attachment_data = csv_data.getvalue().encode('utf-8')
# #     else:
# #         attachment_data = csv_data.getvalue()

# #     csv_attachment = MIMEApplication(attachment_data)
# #     csv_attachment['Content-Disposition'] = 'attachment; filename="pinterest_pins.csv"'
# #     msg.attach(csv_attachment)

# #     # Send email
# #     try:
# #         server = smtplib.SMTP('smtp.gmail.com', 587)
# #         server.starttls()
# #         server.login(from_email, app_password)
# #         server.send_message(msg)
# #         server.quit()
# #         print("Email sent successfully!")
# #         return True
# #     except Exception as e:
# #         print(f"Failed to send email: {str(e)}")
# #         return False

# # def create_slug(text):
# #     """Generate SEO-friendly slug from text"""
# #     slug = text.lower()
# #     # Remove special characters and replace spaces with hyphens
# #     slug = re.sub(r'[^a-z0-9\s-]', '', slug)
# #     slug = re.sub(r'[\s-]+', '-', slug)
# #     slug = slug.strip('-')  # Remove leading/trailing hyphens
# #     slug = slug[:100]  # Limit length
# #     return slug

# # def extract_topic_from_url(url):
# #     """Extract topic from URL for image generation prompt"""
# #     # Extract path from URL
# #     path = url.split('/')

# #     # Find the part that's likely the article title
# #     article_segment = None
# #     for segment in path:
# #         if segment and segment not in ['http:', 'https:', '', 'www', 'com', 'org', 'net']:
# #             if '.' not in segment and segment not in ['utm_source', 'utm_campaign', 'utm_medium', 'utm_term']:
# #                 article_segment = segment
# #                 break

# #     if article_segment:
# #         # Convert hyphens to spaces and clean up
# #         topic = article_segment.replace('-', ' ').replace('_', ' ').title()
# #         return topic

# #     # Fallback
# #     return "Home Decor"

# # def get_domain_from_url(url):
# #     """Extract domain from URL for organization"""
# #     try:
# #         from urllib.parse import urlparse
# #         domain = urlparse(url).netloc
# #         # Remove www. prefix if present
# #         if domain.startswith('www.'):
# #             domain = domain[4:]
# #         return domain
# #     except:
# #         return "unknown-domain"

# # def create_run_id():
# #     """Create a unique ID for this run based on timestamp"""
# #     return datetime.now().strftime('%Y%m%d_%H%M%S')

# # def copy_image_to_repo(source_path, url, board_name, title):
# #     """Copy generated image to repository directory structure"""
# #     domain = get_domain_from_url(url)
# #     slug = create_slug(title)[:40]  # Limit length
    
# #     # Create directory structure: pins/domain/board_name/
# #     target_dir = os.path.join(PINS_DIR, domain, board_name)
# #     ensure_directory_exists(target_dir)
    
# #     # Define target path
# #     file_ext = os.path.splitext(source_path)[1]
# #     target_path = os.path.join(target_dir, f"{slug}{file_ext}")
    
# #     # Copy the file
# #     shutil.copy2(source_path, target_path)
# #     return target_path

# # def extract_keywords_for_extra_field(keywords_str):
# #     """Extract keywords for the extra 'Keywords' column"""
# #     # Split the keywords by commas
# #     keywords_list = [k.strip() for k in keywords_str.split(',')]
    
# #     # Join with commas and return
# #     return ', '.join(keywords_list)

# # def main():
# #     print("Pinterest Pin Maker - GitHub Actions Version")
# #     print("------------------------------------------")
    
# #     # Create run ID for this batch
# #     run_id = create_run_id()
    
# #     # Ensure required directories exist
# #     ensure_directory_exists(PINS_DIR)
# #     ensure_directory_exists(DATA_DIR)
    
# #     # Ensure required files exist
# #     ensure_file_exists(URLS_FILE)
    
# #     # Read URLs 
# #     all_urls = read_urls(URLS_FILE)
    
# #     if not all_urls:
# #         print("No URLs found to process.")
# #         return
    
# #     # Take the next batch of URLs
# #     batch_urls = all_urls[:BATCH_SIZE]
# #     remaining_urls = all_urls[BATCH_SIZE:]
# #     print(f"Processing batch of {len(batch_urls)} URLs")
    
# #     # Create CSV file for this batch
# #     batch_csv_path = os.path.join(DATA_DIR, f"pinterest_pins_{run_id}.csv")
    
# #     # Initialize CSV output with the exact column order requested
# #     csv_output = StringIO()
# #     csv_writer = csv.writer(csv_output)
# #     csv_writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Thumbnail', 'Link', 'Publish date', 'Description', 'Keywords', ''])

# #     # Storage for generated images
# #     generated_images = []

# #     # Cache for board names to reduce API calls
# #     board_cache = {}

# #     # Process each URL in the batch
# #     for i, url in enumerate(batch_urls):
# #         print(f"\nProcessing URL {i+1}/{len(batch_urls)}: {url}")
# #         domain_name = get_domain_from_url(url)

# #         try:
# #             # Generate pin content
# #             print("Generating pin content with Gemma model...")
# #             csv_content = generate_pin_content(url, PINS_PER_URL)

# #             if csv_content.startswith("Error"):
# #                 print(f"Error generating pin content: {csv_content}")
# #                 continue

# #             # Parse the generated content
# #             pins = parse_csv_content(csv_content)
# #             print(f"Generated {len(pins)} pin ideas")

# #             # Extract topic from URL
# #             topic = extract_topic_from_url(url)
# #             print(f"Extracted topic: {topic}")

# #             # Create images and upload to Cloudinary for each pin
# #             for j, pin in enumerate(pins):
# #                 print(f"Creating image {j+1}/{len(pins)}...")

# #                 # Generate image prompt based on pin title and URL topic
# #                 image_prompt = f"""
# #                 Create a visually appealing Pinterest pin image for the title: "{pin['Title']}"

# #                 {topic}

# #                 The image should be:
# #                 - In portrait orientation (2:3 ratio) for Pinterest
# #                 - Visually striking with bold colors
# #                 - Include minimal text elements
# #                 - Professional, clean design that would appeal to Pinterest users
# #                 - Suitable for home decor/cleaning tips context
# #                 - Include visual elements related to {topic}
# #                 """

# #                 # Generate image with Gemini
# #                 file_name = f"pin_{i+1}_{j+1}"
# #                 image_url = None
# #                 repo_image_path = None

# #                 try:
# #                     image_data, image_mime_type, image_file_path = generate_image_with_gemini(image_prompt, file_name)

# #                     if image_file_path and os.path.exists(image_file_path):
# #                         # Generate board name first (needed for repository path)
# #                         cache_key = pin['Title'][:15].lower()  # Use first part of title as cache key
# #                         if cache_key in board_cache:
# #                             board_name = board_cache[cache_key]
# #                             print(f"Using cached board name: {board_name}")
# #                         else:
# #                             print("Generating board name with Gemma model...")
# #                             board_name = generate_board_category(pin['Title'], pin['Keywords'])
# #                             board_cache[cache_key] = board_name
# #                             print(f"Generated board name: {board_name}")
                        
# #                         # Copy image to repository structure
# #                         repo_image_path = copy_image_to_repo(image_file_path, url, board_name, pin['Title'])
# #                         print(f"Copied image to repository: {repo_image_path}")
                        
# #                         # Upload to Cloudinary
# #                         print("Uploading to Cloudinary...")
# #                         image_url = upload_to_cloudinary(image_file_path)

# #                         if image_url:
# #                             generated_images.append({
# #                                 'file_path': image_file_path,
# #                                 'repo_path': repo_image_path,
# #                                 'url': image_url,
# #                                 'title': pin['Title']
# #                             })
# #                     else:
# #                         raise Exception("Image file not created properly")

# #                 except Exception as e:
# #                     print(f"Error generating/uploading image: {str(e)}")
# #                     # Use a placeholder image URL if image generation fails
# #                     image_url = "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg"
# #                     board_name = "home-inspiration"  # Default fallback

# #                 # Generate a unique UTM campaign parameter based on pin title
# #                 utm_campaign = create_slug(pin['Title'])[:20]  # Limit length for URL compatibility

# #                 # Create the tracked URL with UTM parameters
# #                 tracked_url = url
# #                 if '?' in tracked_url:
# #                     tracked_url += f"&utm_source=pinterest&utm_campaign={utm_campaign}"
# #                 else:
# #                     tracked_url += f"?utm_source=pinterest&utm_campaign={utm_campaign}"

# #                 # Extract keywords for the extra field
# #                 extra_keywords = extract_keywords_for_extra_field(pin['Keywords'])
                
# #                 # Add to CSV with the exact column order requested
# #                 csv_writer.writerow([
# #                     pin['Title'],                        # Title
# #                     image_url if image_url else "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg", # Media URL
# #                     board_name,                          # Pinterest board
# #                     '',                                  # Thumbnail (empty)
# #                     tracked_url,                         # Link (with UTM parameters)
# #                     datetime.now().strftime('%Y-%m-%d'), # Publish date
# #                     pin['Description'],                  # Description
# #                     pin['Keywords'],                     # Keywords
# #                     extra_keywords                       # Extra column for additional keywords
# #                 ])

# #                 # Add a small delay to prevent rate limiting
# #                 time.sleep(2)

# #         except Exception as e:
# #             print(f"Error processing URL {url}: {str(e)}")
# #             # Keep the URL in the list if there was an error
# #             remaining_urls.append(url)

# #     # Save CSV file to repository
# #     with open(batch_csv_path, 'w', newline='', encoding='utf-8') as f:
# #         f.write(csv_output.getvalue())
    
# #     # Create CSV file for all pins (append to existing or create new)
# #     all_pins_csv_path = os.path.join(DATA_DIR, "all_pinterest_pins.csv")
# #     if os.path.exists(all_pins_csv_path):
# #         # Read existing data
# #         existing_df = pd.read_csv(all_pins_csv_path)
# #         # Read new data
# #         csv_output.seek(0)
# #         new_df = pd.read_csv(csv_output)
# #         # Combine and save
# #         combined_df = pd.concat([existing_df, new_df], ignore_index=True)
# #         combined_df.to_csv(all_pins_csv_path, index=False)
# #     else:
# #         # Just save current batch as all pins
# #         csv_output.seek(0)
# #         with open(all_pins_csv_path, 'w', newline='', encoding='utf-8') as f:
# #             f.write(csv_output.getvalue())
    
# #     # Create zip archive of all generated images
# #     if generated_images:
# #         timestamp = int(time.time())
# #         zip_filename = f"pinterest_images_{timestamp}.zip"

# #         with zipfile.ZipFile(zip_filename, 'w') as zipf:
# #             for image in generated_images:
# #                 if os.path.exists(image['file_path']):
# #                     zipf.write(image['file_path'])

# #         print(f"\nImages zipped to {zip_filename}")

# #     # Write remaining URLs back to file
# #     write_urls(URLS_FILE, remaining_urls)
    
# #     # Send email notification
# #     print("Sending email notification...")
# #     csv_output.seek(0)
# #     send_email_notification(
# #         TO_EMAIL,
# #         FROM_EMAIL,
# #         APP_PASSWORD,
# #         csv_output,
# #         f"Pinterest Pin Generation - Batch of {len(batch_urls)} URLs"
# #     )
    
# #     print("\nProcess completed successfully!")
# #     print(f"Processed {len(batch_urls)} URLs, {len(remaining_urls)} URLs remaining")
    
# #     # Set output for GitHub Actions
# #     with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
# #         f.write(f"processed_urls={len(batch_urls)}\n")
# #         f.write(f"remaining_urls={len(remaining_urls)}\n")

# # if __name__ == "__main__":
# #     main()

# #!/usr/bin/env python3
# # .github/scripts/process_urls.py

# import os
# import csv
# import time
# import json
# import smtplib
# import requests
# import pandas as pd
# import mimetypes
# import re
# import zipfile
# import shutil
# import random
# from io import BytesIO, StringIO
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.application import MIMEApplication
# from pathlib import Path
# from PIL import Image
# from datetime import datetime
# from google import genai
# from google.genai import types

# # Constants
# BATCH_SIZE = 5
# URLS_FILE = "urls.txt"
# PINS_DIR = "pins"
# DATA_DIR = "data"
# PINS_PER_URL = 25  # Reduce number of pins per URL for GitHub Actions

# # Email configuration
# TO_EMAIL = "beacleaner0@gmail.com"
# FROM_EMAIL = "limon.working@gmail.com"
# APP_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# # Initialize API clients with multiple API keys
# def get_api_keys():
#     """Get all available API keys from environment variables"""
#     keys = []
    
#     # Check for primary API key
#     primary_key = os.environ.get("GEMINI_API_KEY")
#     if primary_key:
#         keys.append(primary_key)
    
#     # Check for numbered API keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
#     i = 1
#     while True:
#         key = os.environ.get(f"GEMINI_API_KEY_{i}")
#         if key:
#             keys.append(key)
#             i += 1
#         else:
#             break
    
#     if not keys:
#         raise ValueError("No Gemini API keys found in environment variables")
    
#     print(f"Found {len(keys)} Gemini API keys")
#     return keys

# # Create API key manager class
# class APIKeyManager:
#     def __init__(self, api_keys):
#         self.api_keys = api_keys
#         self.current_index = 0
#         self.clients = {}
        
#         # Initialize clients for each API key
#         for key in self.api_keys:
#             self.clients[key] = genai.Client(api_key=key)
    
#     def get_client(self):
#         """Get the current client"""
#         return self.clients[self.api_keys[self.current_index]]
    
#     def rotate_key(self):
#         """Rotate to the next API key"""
#         self.current_index = (self.current_index + 1) % len(self.api_keys)
#         print(f"Rotated to API key {self.current_index + 1}/{len(self.api_keys)}")
#         return self.get_client()
    
#     def get_random_client(self):
#         """Get a random client to distribute load"""
#         self.current_index = random.randint(0, len(self.api_keys) - 1)
#         return self.get_client()

# # Initialize API key manager with all available keys
# api_keys = get_api_keys()
# key_manager = APIKeyManager(api_keys)

# def ensure_directory_exists(directory):
#     """Ensure a directory exists, creating it if needed"""
#     os.makedirs(directory, exist_ok=True)
#     return directory

# def ensure_file_exists(file_path, default_content=""):
#     """Ensure a file exists, creating it with default content if needed"""
#     directory = os.path.dirname(file_path)
#     if directory and not os.path.exists(directory):
#         os.makedirs(directory, exist_ok=True)
        
#     if not os.path.exists(file_path):
#         with open(file_path, "w") as f:
#             f.write(default_content)
#     return file_path

# def read_urls(file_path):
#     """Read URLs from a text file"""
#     if not os.path.exists(file_path):
#         return []
        
#     with open(file_path, "r") as f:
#         return [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]

# def write_urls(file_path, urls):
#     """Write URLs to a file"""
#     with open(file_path, "w") as f:
#         for url in urls:
#             f.write(f"{url}\n")

# def save_binary_file(file_name, data):
#     """Save binary data to a file"""
#     with open(file_name, "wb") as f:
#         f.write(data)
#     return file_name

# def compress_image(image_path, quality=85):
#     """Compress image and convert to WebP format"""
#     try:
#         with Image.open(image_path) as img:
#             webp_path = f"{os.path.splitext(image_path)[0]}.webp"
#             img.save(webp_path, 'WEBP', quality=quality)
#             if os.path.exists(image_path):
#                 os.remove(image_path)  # Remove original file
#             return webp_path
#     except Exception as e:
#         print(f"Image compression error: {e}")
#         return image_path

# def upload_to_cloudinary(file_path, resource_type="image"):
#     """Upload file to Cloudinary using direct API call"""
#     url = f"https://api.cloudinary.com/v1_1/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/{resource_type}/upload"
#     payload = {
#         'upload_preset': 'ml_default',
#         'api_key': os.environ.get('CLOUDINARY_API_KEY')
#     }
#     try:
#         with open(file_path, 'rb') as f:
#             files = {'file': f}
#             response = requests.post(url, data=payload, files=files)
#         if response.status_code == 200:
#             return response.json()['secure_url']
#         print(f"Upload failed: {response.text}")
#         return None
#     except Exception as e:
#         print(f"Upload error: {e}")
#         return None

# def generate_image_with_gemini(prompt, file_name, max_retries=3):
#     """Generate an image using Gemini 2.0 Flash image generation model with retry logic"""
#     for attempt in range(max_retries):
#         try:
#             # Get current client or rotate after a failure
#             if attempt > 0:
#                 client = key_manager.rotate_key()
#             else:
#                 client = key_manager.get_client()
                
#             model = "gemini-2.0-flash-exp-image-generation"
#             contents = [types.Content(
#                 role="user",
#                 parts=[types.Part.from_text(text=prompt)]
#             )]

#             response = client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 config=types.GenerateContentConfig(response_modalities=["image", "text"])
#             )

#             # Process response to extract image
#             if response.candidates and response.candidates[0].content.parts:
#                 for part in response.candidates[0].content.parts:
#                     if hasattr(part, 'inline_data') and part.inline_data:
#                         inline_data = part.inline_data
#                         file_ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
#                         file_path = f"{file_name}{file_ext}"

#                         # Save the file
#                         save_binary_file(file_path, inline_data.data)

#                         # Compress and convert to WebP
#                         final_path = compress_image(file_path)

#                         print(f"Image generated and saved to: {final_path}")
#                         return inline_data.data, inline_data.mime_type, final_path

#             raise Exception("No image data found in response")
            
#         except Exception as e:
#             print(f"Error generating image (attempt {attempt+1}/{max_retries}): {str(e)}")
#             if attempt < max_retries - 1:
#                 print(f"Retrying with different API key...")
#                 time.sleep(2)  # Add a small delay before retry
#             else:
#                 print("All retries failed")
#                 return None, None, None

# def call_gemini_with_retry(model, contents, config, max_retries=3):
#     """Call Gemini API with retry logic for rate limits"""
#     for attempt in range(max_retries):
#         try:
#             # Get current client or rotate after a failure
#             if attempt > 0:
#                 client = key_manager.rotate_key()
#             else:
#                 client = key_manager.get_client()
                
#             response = client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 config=config
#             )
#             return response
            
#         except Exception as e:
#             error_str = str(e).lower()
#             print(f"API error (attempt {attempt+1}/{max_retries}): {error_str}")
            
#             # Check for rate limit errors
#             if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
#                 if attempt < max_retries - 1:
#                     print(f"Rate limit hit. Rotating API key and retrying...")
#                     time.sleep(2)  # Add a small delay before retry
#                 else:
#                     print("All API keys are rate limited. Giving up.")
#                     raise
#             else:
#                 # For non-rate-limit errors, don't retry
#                 raise

# def generate_pin_content(url, pins_per_url=5, max_retries=3):
#     """Generate Pinterest pin content using Gemma model with retry logic"""
#     try:
#         model = "gemma-3-27b-it"  # Using Gemma model
#         contents = [types.Content(
#             role="user",
#             parts=[types.Part.from_text(text=f"""
#             Create {pins_per_url} unique Pinterest pin ideas for the blog post at {url}.
#             For each pin, provide:
#             1. An engaging title (under 70 characters)
#             2. A compelling description (must be 350-400 characters) that includes hashtags at the end
#             3. 3-4 relevant keywords separated by commas
            
#             The description MUST end with relevant hashtags like #Keyword1 #Keyword2.
            
#             Format your response as CSV data with these exact columns:
#             Title,Description,Keywords
            
#             Make each pin unique with different angles or highlights from the blog post.
#             Include calls to action and emotional appeals in descriptions.
#             Do NOT include quotation marks around the title or description.
#             """)]
#         )]

#         generate_content_config = types.GenerateContentConfig(
#             temperature=1,
#             top_p=0.95,
#             top_k=64,
#             max_output_tokens=8192,
#             response_mime_type="text/plain",
#         )

#         print(f"Generating pin content with Gemma model for URL: {url}")
        
#         # Call with retry logic
#         response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)
        
#         return response.text if response.text else "No content generated"
#     except Exception as e:
#         print(f"Error generating pin content: {str(e)}")
#         return f"Error: {str(e)}"

# def generate_board_category(title, keywords, max_retries=3):
#     """Generate Pinterest board category using Gemma model with retry logic"""
#     try:
#         model = "gemma-3-27b-it"
#         contents = [types.Content(
#             role="user",
#             parts=[types.Part.from_text(text=f"""
#             Analyze this Pinterest pin title and keywords, then suggest ONE specific board name
#             that would be most appropriate for this content on Pinterest.

#             Title: {title}
#             Keywords: {keywords}

#             Return ONLY the board name, nothing else. The board name should be:
#             - 2-3 words maximum
#             - Descriptive of the content category
#             - End with "ideas" or "inspiration"
#             - Lowercase with hyphens between words (e.g., "home-decor-ideas")
#             - Common Pinterest board category that would have wide appeal
#             - NOT include the brand name or website name

#             JUST RETURN THE BOARD NAME ONLY.
#             """)]
#         )]

#         generate_content_config = types.GenerateContentConfig(
#             temperature=0.2,  # Lower temperature for more consistent results
#             top_p=0.95,
#             top_k=40,
#             max_output_tokens=20,  # Short response
#             response_mime_type="text/plain",
#         )

#         # Call with retry logic
#         response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)

#         board_name = response.text.strip().lower()

#         # Clean up the board name
#         board_name = re.sub(r'[^a-z0-9\s-]', '', board_name)
#         board_name = re.sub(r'[\s]+', '-', board_name)
#         board_name = board_name.strip('-')

#         # Fallback if the model returns something invalid
#         if not board_name or len(board_name) < 3:
#             return "home-inspiration"

#         return board_name
#     except Exception as e:
#         print(f"Error generating board category: {str(e)}")
#         return "home-inspiration"  # Default fallback

# def parse_csv_content(csv_content):
#     """Parse CSV content from API response"""
#     pins = []
#     lines = csv_content.strip().split('\n')

#     # Skip header if present
#     start_idx = 0
#     if 'Title' in lines[0] and 'Description' in lines[0]:
#         start_idx = 1

#     # Process each line
#     for i in range(start_idx, len(lines)):
#         line = lines[i]
#         if not line.strip():
#             continue

#         try:
#             # Handle potential CSV formatting issues
#             if ',' in line:
#                 parts = line.split(',')
#                 if len(parts) >= 3:
#                     title = parts[0].strip()
#                     description = ','.join(parts[1:-1]).strip()  # Join all middle parts in case descriptions have commas
#                     keywords = parts[-1].strip()

#                     # Remove quotation marks from title and description
#                     title = title.strip('"\'')
#                     description = description.strip('"\'')

#                     pins.append({
#                         'Title': title,
#                         'Description': description,
#                         'Keywords': keywords
#                     })
#         except Exception as e:
#             print(f"Error parsing line: {line}, Error: {str(e)}")

#     return pins

# def send_email_notification(to_email, from_email, app_password, csv_data, subject="Pinterest Pin Generation Complete"):
#     """Send email with CSV attachment"""
#     if not app_password:
#         print("No email password provided. Skipping email notification.")
#         return False
        
#     msg = MIMEMultipart()
#     msg['From'] = from_email
#     msg['To'] = to_email
#     msg['Subject'] = f"{subject} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

#     # Email body
#     body = f"""
#     Hello,

#     Your Pinterest pin generation process has completed successfully.
#     The CSV file with the generated pins is attached.

#     Time of completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#     """

#     msg.attach(MIMEText(body, 'plain'))

#     # Attach CSV - ensure it's bytes
#     if isinstance(csv_data, StringIO):
#         attachment_data = csv_data.getvalue().encode('utf-8')
#     else:
#         attachment_data = csv_data.getvalue()

#     csv_attachment = MIMEApplication(attachment_data)
#     csv_attachment['Content-Disposition'] = 'attachment; filename="pinterest_pins.csv"'
#     msg.attach(csv_attachment)

#     # Send email
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(from_email, app_password)
#         server.send_message(msg)
#         server.quit()
#         print("Email sent successfully!")
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {str(e)}")
#         return False

# def create_slug(text):
#     """Generate SEO-friendly slug from text"""
#     slug = text.lower()
#     # Remove special characters and replace spaces with hyphens
#     slug = re.sub(r'[^a-z0-9\s-]', '', slug)
#     slug = re.sub(r'[\s-]+', '-', slug)
#     slug = slug.strip('-')  # Remove leading/trailing hyphens
#     slug = slug[:100]  # Limit length
#     return slug

# def extract_topic_from_url(url):
#     """Extract topic from URL for image generation prompt"""
#     # Extract path from URL
#     path = url.split('/')

#     # Find the part that's likely the article title
#     article_segment = None
#     for segment in path:
#         if segment and segment not in ['http:', 'https:', '', 'www', 'com', 'org', 'net']:
#             if '.' not in segment and segment not in ['utm_source', 'utm_campaign', 'utm_medium', 'utm_term']:
#                 article_segment = segment
#                 break

#     if article_segment:
#         # Convert hyphens to spaces and clean up
#         topic = article_segment.replace('-', ' ').replace('_', ' ').title()
#         return topic

#     # Fallback
#     return "Home Decor"

# def get_domain_from_url(url):
#     """Extract domain from URL for organization"""
#     try:
#         from urllib.parse import urlparse
#         domain = urlparse(url).netloc
#         # Remove www. prefix if present
#         if domain.startswith('www.'):
#             domain = domain[4:]
#         return domain
#     except:
#         return "unknown-domain"

# def create_run_id():
#     """Create a unique ID for this run based on timestamp"""
#     return datetime.now().strftime('%Y%m%d_%H%M%S')

# def copy_image_to_repo(source_path, url, board_name, title):
#     """Copy generated image to repository directory structure"""
#     domain = get_domain_from_url(url)
#     slug = create_slug(title)[:40]  # Limit length
    
#     # Create directory structure: pins/domain/board_name/
#     target_dir = os.path.join(PINS_DIR, domain, board_name)
#     ensure_directory_exists(target_dir)
    
#     # Define target path
#     file_ext = os.path.splitext(source_path)[1]
#     target_path = os.path.join(target_dir, f"{slug}{file_ext}")
    
#     # Copy the file
#     shutil.copy2(source_path, target_path)
#     return target_path

# def extract_keywords_for_extra_field(keywords_str):
#     """Extract keywords for the extra 'Keywords' column"""
#     # Split the keywords by commas
#     keywords_list = [k.strip() for k in keywords_str.split(',')]
    
#     # Join with commas and return
#     return ', '.join(keywords_list)

# def main():
#     print("Pinterest Pin Maker - GitHub Actions Version")
#     print("------------------------------------------")
    
#     # Create run ID for this batch
#     run_id = create_run_id()
    
#     # Ensure required directories exist
#     ensure_directory_exists(PINS_DIR)
#     ensure_directory_exists(DATA_DIR)
    
#     # Ensure required files exist
#     ensure_file_exists(URLS_FILE)
    
#     # Read URLs 
#     all_urls = read_urls(URLS_FILE)
    
#     if not all_urls:
#         print("No URLs found to process.")
#         return
    
#     # Take the next batch of URLs
#     batch_urls = all_urls[:BATCH_SIZE]
#     remaining_urls = all_urls[BATCH_SIZE:]
#     print(f"Processing batch of {len(batch_urls)} URLs")
#     print(f"Using {len(api_keys)} Gemini API keys for load balancing")
    
#     # Create CSV file for this batch
#     batch_csv_path = os.path.join(DATA_DIR, f"pinterest_pins_{run_id}.csv")
    
#     # Initialize CSV output with the exact column order requested
#     csv_output = StringIO()
#     csv_writer = csv.writer(csv_output)
#     csv_writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Thumbnail', 'Link', 'Publish date', 'Description', 'Keywords', ''])

#     # Storage for generated images
#     generated_images = []

#     # Cache for board names to reduce API calls
#     board_cache = {}
    
#     # Track API usage for load balancing
#     api_usage_count = {key: 0 for key in api_keys}

#     # Process each URL in the batch
#     for i, url in enumerate(batch_urls):
#         print(f"\nProcessing URL {i+1}/{len(batch_urls)}: {url}")
#         domain_name = get_domain_from_url(url)

#         try:
#             # Generate pin content
#             print("Generating pin content with Gemma model...")
#             csv_content = generate_pin_content(url, PINS_PER_URL)

#             if csv_content.startswith("Error"):
#                 print(f"Error generating pin content: {csv_content}")
#                 continue

#             # Parse the generated content
#             pins = parse_csv_content(csv_content)
#             print(f"Generated {len(pins)} pin ideas")

#             # Extract topic from URL
#             topic = extract_topic_from_url(url)
#             print(f"Extracted topic: {topic}")

#             # Create images and upload to Cloudinary for each pin
#             for j, pin in enumerate(pins):
#                 print(f"Creating image {j+1}/{len(pins)}...")

#                 # Generate image prompt based on pin title and URL topic
#                 image_prompt = f"""
#                 Create a visually appealing Pinterest pin image for the title: "{pin['Title']}"

#                 {topic}

#                 The image should be:
#                 - In portrait orientation (2:3 ratio) for Pinterest
#                 - Visually striking with bold colors
#                 - Include minimal text elements
#                 - Professional, clean design that would appeal to Pinterest users
#                 - Suitable for home decor/cleaning tips context
#                 - Include visual elements related to {topic}
#                 """

#                 # Generate image with Gemini - distribute among API keys
#                 file_name = f"pin_{i+1}_{j+1}"
#                 image_url = None
#                 repo_image_path = None

#                 try:
#                     # Use a different API key for each image to distribute load
#                     key_manager.get_random_client()
#                     image_data, image_mime_type, image_file_path = generate_image_with_gemini(image_prompt, file_name)

#                     if image_file_path and os.path.exists(image_file_path):
#                         # Generate board name first (needed for repository path)
#                         cache_key = pin['Title'][:15].lower()  # Use first part of title as cache key
#                         if cache_key in board_cache:
#                             board_name = board_cache[cache_key]
#                             print(f"Using cached board name: {board_name}")
#                         else:
#                             print("Generating board name with Gemma model...")
#                             board_name = generate_board_category(pin['Title'], pin['Keywords'])
#                             board_cache[cache_key] = board_name
#                             print(f"Generated board name: {board_name}")
                        
#                         # Copy image to repository structure
#                         repo_image_path = copy_image_to_repo(image_file_path, url, board_name, pin['Title'])
#                         print(f"Copied image to repository: {repo_image_path}")
                        
#                         # Upload to Cloudinary
#                         print("Uploading to Cloudinary...")
#                         image_url = upload_to_cloudinary(image_file_path)

#                         if image_url:
#                             generated_images.append({
#                                 'file_path': image_file_path,
#                                 'repo_path': repo_image_path,
#                                 'url': image_url,
#                                 'title': pin['Title']
#                             })
#                     else:
#                         raise Exception("Image file not created properly")

#                 except Exception as e:
#                     print(f"Error generating/uploading image: {str(e)}")
#                     # Use a placeholder image URL if image generation fails
#                     image_url = "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg"
#                     board_name = "home-inspiration"  # Default fallback

#                 # Generate a unique UTM campaign parameter based on pin title
#                 utm_campaign = create_slug(pin['Title'])[:20]  # Limit length for URL compatibility

#                 # Create the tracked URL with UTM parameters
#                 tracked_url = url
#                 if '?' in tracked_url:
#                     tracked_url += f"&utm_source=pinterest&utm_campaign={utm_campaign}"
#                 else:
#                     tracked_url += f"?utm_source=pinterest&utm_campaign={utm_campaign}"

#                 # Extract keywords for the extra field
#                 extra_keywords = extract_keywords_for_extra_field(pin['Keywords'])
                
#                 # Add to CSV with the exact column order requested
#                 csv_writer.writerow([
#                     pin['Title'],                        # Title
#                     image_url if image_url else "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg", # Media URL
#                     board_name,                          # Pinterest board
#                     '',                                  # Thumbnail (empty)
#                     tracked_url,                         # Link (with UTM parameters)
#                     datetime.now().strftime('%Y-%m-%d'), # Publish date
#                     pin['Description'],                  # Description
#                     pin['Keywords'],                     # Keywords
#                     extra_keywords                       # Extra column for additional keywords
#                 ])

#                 # Add a small delay to prevent rate limiting
#                 time.sleep(2)

#         except Exception as e:
#             print(f"Error processing URL {url}: {str(e)}")
#             # Keep the URL in the list if there was an error
#             remaining_urls.append(url)

#     # Save CSV file to repository
#     with open(batch_csv_path, 'w', newline='', encoding='utf-8') as f:
#         f.write(csv_output.getvalue())
    
#     # Create CSV file for all pins (append to existing or create new)
#     all_pins_csv_path = os.path.join(DATA_DIR, "all_pinterest_pins.csv")
#     if os.path.exists(all_pins_csv_path):
#         # Read existing data
#         existing_df = pd.read_csv(all_pins_csv_path)
#         # Read new data
#         csv_output.seek(0)
#         new_df = pd.read_csv(csv_output)
#         # Combine and save
#         combined_df = pd.concat([existing_df, new_df], ignore_index=True)
#         combined_df.to_csv(all_pins_csv_path, index=False)
#     else:
#         # Just save current batch as all pins
#         csv_output.seek(0)
#         with open(all_pins_csv_path, 'w', newline='', encoding='utf-8') as f:
#             f.write(csv_output.getvalue())
    
#     # Create zip archive of all generated images
#     if generated_images:
#         timestamp = int(time.time())
#         zip_filename = f"pinterest_images_{timestamp}.zip"

#         with zipfile.ZipFile(zip_filename, 'w') as zipf:
#             for image in generated_images:
#                 if os.path.exists(image['file_path']):
#                     zipf.write(image['file_path'])

#         print(f"\nImages zipped to {zip_filename}")

#     # Write remaining URLs back to file
#     write_urls(URLS_FILE, remaining_urls)
    
#     # Send email notification
#     print("Sending email notification...")
#     csv_output.seek(0)
#     send_email_notification(
#         TO_EMAIL,
#         FROM_EMAIL,
#         APP_PASSWORD,
#         csv_output,
#         f"Pinterest Pin Generation - Batch of {len(batch_urls)} URLs"
#     )
    
#     print("\nProcess completed successfully!")
#     print(f"Processed {len(batch_urls)} URLs, {len(remaining_urls)} URLs remaining")
    
#     # Set output for GitHub Actions
#     with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
#         f.write(f"processed_urls={len(batch_urls)}\n")
#         f.write(f"remaining_urls={len(remaining_urls)}\n")

# if __name__ == "__main__":
#     main()

# #!/usr/bin/env python3
# # .github/scripts/process_urls.py

# import os
# import csv
# import time
# import json
# import smtplib
# import requests
# import pandas as pd
# import mimetypes
# import re
# import zipfile
# import shutil
# import random
# from io import BytesIO, StringIO
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.application import MIMEApplication
# from pathlib import Path
# from PIL import Image
# from datetime import datetime
# from google import genai
# from google.genai import types

# # Constants
# BATCH_SIZE = 5
# URLS_FILE = "urls.txt"
# PINS_DIR = "pins"
# DATA_DIR = "data"
# PINS_PER_URL = 25  # Reduce number of pins per URL for GitHub Actions

# # Email configuration
# TO_EMAIL = "beacleaner0@gmail.com"
# FROM_EMAIL = "limon.working@gmail.com"
# APP_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# # Initialize API clients with multiple API keys
# def get_api_keys():
#     """Get all available API keys from environment variables"""
#     keys = []
    
#     # Check for primary API key
#     primary_key = os.environ.get("GEMINI_API_KEY")
#     if primary_key:
#         keys.append(primary_key)
    
#     # Check for numbered API keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
#     i = 1
#     while True:
#         key = os.environ.get(f"GEMINI_API_KEY_{i}")
#         if key:
#             keys.append(key)
#             i += 1
#         else:
#             break
    
#     if not keys:
#         raise ValueError("No Gemini API keys found in environment variables")
    
#     print(f"Found {len(keys)} Gemini API keys")
#     return keys

# # Create API key manager class
# class APIKeyManager:
#     def __init__(self, api_keys):
#         self.api_keys = api_keys
#         self.current_index = 0
#         self.clients = {}
        
#         # Initialize clients for each API key
#         for key in self.api_keys:
#             self.clients[key] = genai.Client(api_key=key)
    
#     def get_client(self):
#         """Get the current client"""
#         return self.clients[self.api_keys[self.current_index]]
    
#     def rotate_key(self):
#         """Rotate to the next API key"""
#         self.current_index = (self.current_index + 1) % len(self.api_keys)
#         print(f"Rotated to API key {self.current_index + 1}/{len(self.api_keys)}")
#         return self.get_client()
    
#     def get_random_client(self):
#         """Get a random client to distribute load"""
#         self.current_index = random.randint(0, len(self.api_keys) - 1)
#         return self.get_client()

# # Initialize API key manager with all available keys
# api_keys = get_api_keys()
# key_manager = APIKeyManager(api_keys)

# def ensure_directory_exists(directory):
#     """Ensure a directory exists, creating it if needed"""
#     os.makedirs(directory, exist_ok=True)
#     return directory

# def ensure_file_exists(file_path, default_content=""):
#     """Ensure a file exists, creating it with default content if needed"""
#     directory = os.path.dirname(file_path)
#     if directory and not os.path.exists(directory):
#         os.makedirs(directory, exist_ok=True)
        
#     if not os.path.exists(file_path):
#         with open(file_path, "w") as f:
#             f.write(default_content)
#     return file_path

# def read_urls(file_path):
#     """Read URLs from a text file"""
#     if not os.path.exists(file_path):
#         return []
        
#     with open(file_path, "r") as f:
#         return [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]

# def write_urls(file_path, urls):
#     """Write URLs to a file"""
#     with open(file_path, "w") as f:
#         for url in urls:
#             f.write(f"{url}\n")

# def save_binary_file(file_name, data):
#     """Save binary data to a file"""
#     with open(file_name, "wb") as f:
#         f.write(data)
#     return file_name

# def compress_image(image_path, quality=85):
#     """Compress image and convert to WebP format"""
#     try:
#         with Image.open(image_path) as img:
#             webp_path = f"{os.path.splitext(image_path)[0]}.webp"
#             img.save(webp_path, 'WEBP', quality=quality)
#             if os.path.exists(image_path):
#                 os.remove(image_path)  # Remove original file
#             return webp_path
#     except Exception as e:
#         print(f"Image compression error: {e}")
#         return image_path

# def upload_to_cloudinary(file_path, resource_type="image"):
#     """Upload file to Cloudinary using direct API call"""
#     url = f"https://api.cloudinary.com/v1_1/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/{resource_type}/upload"
#     payload = {
#         'upload_preset': 'ml_default',
#         'api_key': os.environ.get('CLOUDINARY_API_KEY')
#     }
#     try:
#         with open(file_path, 'rb') as f:
#             files = {'file': f}
#             response = requests.post(url, data=payload, files=files)
#         if response.status_code == 200:
#             return response.json()['secure_url']
#         print(f"Upload failed: {response.text}")
#         return None
#     except Exception as e:
#         print(f"Upload error: {e}")
#         return None

# def generate_image_with_gemini(prompt, file_name, max_retries=3):
#     """Generate an image using Gemini 2.0 Flash image generation model with retry logic"""
#     for attempt in range(max_retries):
#         try:
#             # Get current client or rotate after a failure
#             if attempt > 0:
#                 client = key_manager.rotate_key()
#             else:
#                 client = key_manager.get_client()
                
#             model = "gemini-2.0-flash-exp-image-generation"
#             contents = [types.Content(
#                 role="user",
#                 parts=[types.Part.from_text(text=prompt)]
#             )]

#             response = client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 config=types.GenerateContentConfig(response_modalities=["image", "text"])
#             )

#             # Process response to extract image
#             if response.candidates and response.candidates[0].content.parts:
#                 for part in response.candidates[0].content.parts:
#                     if hasattr(part, 'inline_data') and part.inline_data:
#                         inline_data = part.inline_data
#                         file_ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
#                         file_path = f"{file_name}{file_ext}"

#                         # Save the file
#                         save_binary_file(file_path, inline_data.data)

#                         # Compress and convert to WebP
#                         final_path = compress_image(file_path)

#                         print(f"Image generated and saved to: {final_path}")
#                         return inline_data.data, inline_data.mime_type, final_path

#             raise Exception("No image data found in response")
            
#         except Exception as e:
#             print(f"Error generating image (attempt {attempt+1}/{max_retries}): {str(e)}")
#             if attempt < max_retries - 1:
#                 print(f"Retrying with different API key...")
#                 time.sleep(2)  # Add a small delay before retry
#             else:
#                 print("All retries failed")
#                 return None, None, None

# def call_gemini_with_retry(model, contents, config, max_retries=3):
#     """Call Gemini API with retry logic for rate limits"""
#     for attempt in range(max_retries):
#         try:
#             # Get current client or rotate after a failure
#             if attempt > 0:
#                 client = key_manager.rotate_key()
#             else:
#                 client = key_manager.get_client()
                
#             response = client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 config=config
#             )
#             return response
            
#         except Exception as e:
#             error_str = str(e).lower()
#             print(f"API error (attempt {attempt+1}/{max_retries}): {error_str}")
            
#             # Check for rate limit errors
#             if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
#                 if attempt < max_retries - 1:
#                     print(f"Rate limit hit. Rotating API key and retrying...")
#                     time.sleep(2)  # Add a small delay before retry
#                 else:
#                     print("All API keys are rate limited. Giving up.")
#                     raise
#             else:
#                 # For non-rate-limit errors, don't retry
#                 raise

# def generate_pin_content(url, pins_per_url=5, max_retries=3):
#     """Generate Pinterest pin content using Gemma model with retry logic"""
#     try:
#         model = "gemma-3-27b-it"  # Using Gemma model
#         contents = [types.Content(
#             role="user",
#             parts=[types.Part.from_text(text=f"""
#             Create {pins_per_url} unique Pinterest pin ideas for the blog post at {url}.
#             For each pin, provide:
#             1. An engaging title (under 70 characters)
#             2. A compelling description (must be 350-400 characters) that includes hashtags at the end
#             3. 3-4 relevant keywords separated by commas
            
#             The description MUST end with relevant hashtags like #Keyword1 #Keyword2.
            
#             Format your response as CSV data with these exact columns:
#             Title,Description,Keywords
            
#             Make each pin unique with different angles or highlights from the blog post.
#             Include calls to action and emotional appeals in descriptions.
#             Do NOT include quotation marks around the title or description.
#             """)]
#         )]

#         generate_content_config = types.GenerateContentConfig(
#             temperature=1,
#             top_p=0.95,
#             top_k=64,
#             max_output_tokens=8192,
#             response_mime_type="text/plain",
#         )

#         print(f"Generating pin content with Gemma model for URL: {url}")
        
#         # Call with retry logic
#         response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)
        
#         return response.text if response.text else "No content generated"
#     except Exception as e:
#         print(f"Error generating pin content: {str(e)}")
#         return f"Error: {str(e)}"

# def generate_board_category(title, keywords, max_retries=3):
#     """Generate Pinterest board category using Gemma model with retry logic"""
#     try:
#         model = "gemma-3-27b-it"
#         contents = [types.Content(
#             role="user",
#             parts=[types.Part.from_text(text=f"""
#             Analyze this Pinterest pin title and keywords, then suggest ONE specific board name
#             that would be most appropriate for this content on Pinterest.

#             Title: {title}
#             Keywords: {keywords}

#             Return ONLY the board name, nothing else. The board name should be:
#             - 2-3 words maximum
#             - Descriptive of the content category
#             - End with "ideas" or "inspiration" or "tips"
#             - Lowercase with hyphens between words (e.g., "home-decor-ideas")
#             - Common Pinterest board category that would have wide appeal
#             - NOT include the brand name or website name

#             JUST RETURN THE BOARD NAME ONLY.
#             """)]
#         )]

#         generate_content_config = types.GenerateContentConfig(
#             temperature=0.2,  # Lower temperature for more consistent results
#             top_p=0.95,
#             top_k=40,
#             max_output_tokens=20,  # Short response
#             response_mime_type="text/plain",
#         )

#         # Call with retry logic
#         response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)

#         board_name = response.text.strip().lower()

#         # Clean up the board name
#         board_name = re.sub(r'[^a-z0-9\s-]', '', board_name)
#         board_name = re.sub(r'[\s]+', '-', board_name)
#         board_name = board_name.strip('-')

#         # Fallback if the model returns something invalid
#         if not board_name or len(board_name) < 3:
#             return "home-inspiration"

#         return board_name
#     except Exception as e:
#         print(f"Error generating board category: {str(e)}")
#         return "home-inspiration"  # Default fallback

# def parse_csv_content(csv_content):
#     """Parse CSV content from API response using a more robust approach"""
#     pins = []
    
#     try:
#         # First attempt to use StringIO and csv reader for proper CSV parsing
#         csv_file = StringIO(csv_content.strip())
#         reader = csv.reader(csv_file)
        
#         rows = list(reader)
        
#         # Skip header if present
#         start_idx = 0
#         if rows and len(rows) > 0:
#             if 'Title' in rows[0][0] and 'Description' in ''.join(rows[0]):
#                 start_idx = 1
                
#         # Process each row
#         for i in range(start_idx, len(rows)):
#             row = rows[i]
#             if not row or not ''.join(row).strip():
#                 continue
                
#             # Ensure we have at least 3 columns
#             if len(row) >= 3:
#                 title = row[0].strip()
#                 description = row[1].strip()
#                 keywords = row[2].strip()
                
#                 # Remove quotation marks from title and description
#                 title = title.strip('"\'')
#                 description = description.strip('"\'')
                
#                 # Validate data
#                 if title and description and keywords:
#                     pins.append({
#                         'Title': title,
#                         'Description': description,
#                         'Keywords': keywords
#                     })
                    
#     except Exception as e:
#         print(f"Error parsing CSV with reader: {str(e)}")
#         # Fallback to manual parsing if CSV reader fails
#         try:
#             lines = csv_content.strip().split('\n')
            
#             # Skip header if present
#             start_idx = 0
#             if 'Title' in lines[0] and 'Description' in lines[0]:
#                 start_idx = 1
            
#             # Process each line
#             for i in range(start_idx, len(lines)):
#                 line = lines[i]
#                 if not line.strip():
#                     continue
                
#                 try:
#                     # Handle potential CSV formatting issues
#                     if ',' in line:
#                         parts = line.split(',')
#                         if len(parts) >= 3:
#                             title = parts[0].strip()
#                             description = ','.join(parts[1:-1]).strip()  # Join all middle parts in case descriptions have commas
#                             keywords = parts[-1].strip()
                            
#                             # Remove quotation marks from title and description
#                             title = title.strip('"\'')
#                             description = description.strip('"\'')
                            
#                             if title and description and keywords:
#                                 pins.append({
#                                     'Title': title,
#                                     'Description': description,
#                                     'Keywords': keywords
#                                 })
#                 except Exception as e:
#                     print(f"Error parsing line: {line}, Error: {str(e)}")
#         except Exception as e:
#             print(f"Error in fallback parsing: {str(e)}")

#     return pins

# def send_email_notification(to_email, from_email, app_password, csv_data, subject="Pinterest Pin Generation Complete"):
#     """Send email with CSV attachment"""
#     if not app_password:
#         print("No email password provided. Skipping email notification.")
#         return False
        
#     msg = MIMEMultipart()
#     msg['From'] = from_email
#     msg['To'] = to_email
#     msg['Subject'] = f"{subject} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

#     # Email body
#     body = f"""
#     Hello,

#     Your Pinterest pin generation process has completed successfully.
#     The CSV file with the generated pins is attached.

#     Time of completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#     """

#     msg.attach(MIMEText(body, 'plain'))

#     # Attach CSV - ensure it's bytes
#     if isinstance(csv_data, StringIO):
#         attachment_data = csv_data.getvalue().encode('utf-8')
#     else:
#         attachment_data = csv_data.getvalue()

#     csv_attachment = MIMEApplication(attachment_data)
#     csv_attachment['Content-Disposition'] = 'attachment; filename="pinterest_pins.csv"'
#     msg.attach(csv_attachment)

#     # Send email
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(from_email, app_password)
#         server.send_message(msg)
#         server.quit()
#         print("Email sent successfully!")
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {str(e)}")
#         return False

# def create_slug(text):
#     """Generate SEO-friendly slug from text"""
#     slug = text.lower()
#     # Remove special characters and replace spaces with hyphens
#     slug = re.sub(r'[^a-z0-9\s-]', '', slug)
#     slug = re.sub(r'[\s-]+', '-', slug)
#     slug = slug.strip('-')  # Remove leading/trailing hyphens
#     slug = slug[:100]  # Limit length
#     return slug

# def extract_topic_from_url(url):
#     """Extract topic from URL for image generation prompt"""
#     # Extract path from URL
#     path = url.split('/')

#     # Find the part that's likely the article title
#     article_segment = None
#     for segment in path:
#         if segment and segment not in ['http:', 'https:', '', 'www', 'com', 'org', 'net']:
#             if '.' not in segment and segment not in ['utm_source', 'utm_campaign', 'utm_medium', 'utm_term']:
#                 article_segment = segment
#                 break

#     if article_segment:
#         # Convert hyphens to spaces and clean up
#         topic = article_segment.replace('-', ' ').replace('_', ' ').title()
#         return topic

#     # Fallback
#     return "Home Decor"

# def get_domain_from_url(url):
#     """Extract domain from URL for organization"""
#     try:
#         from urllib.parse import urlparse
#         domain = urlparse(url).netloc
#         # Remove www. prefix if present
#         if domain.startswith('www.'):
#             domain = domain[4:]
#         return domain
#     except:
#         return "unknown-domain"

# def create_run_id():
#     """Create a unique ID for this run based on timestamp"""
#     return datetime.now().strftime('%Y%m%d_%H%M%S')

# def copy_image_to_repo(source_path, url, board_name, title):
#     """Copy generated image to repository directory structure"""
#     domain = get_domain_from_url(url)
#     slug = create_slug(title)[:40]  # Limit length
    
#     # Create directory structure: pins/domain/board_name/
#     target_dir = os.path.join(PINS_DIR, domain, board_name)
#     ensure_directory_exists(target_dir)
    
#     # Define target path
#     file_ext = os.path.splitext(source_path)[1]
#     target_path = os.path.join(target_dir, f"{slug}{file_ext}")
    
#     # Copy the file
#     shutil.copy2(source_path, target_path)
#     return target_path

# def extract_keywords_for_extra_field(keywords_str):
#     """Extract keywords for the extra 'Keywords' column"""
#     # Split the keywords by commas
#     keywords_list = [k.strip() for k in keywords_str.split(',')]
    
#     # Join with commas and return
#     return ', '.join(keywords_list)

# def main():
#     print("Pinterest Pin Maker - GitHub Actions Version")
#     print("------------------------------------------")
    
#     # Create run ID for this batch
#     run_id = create_run_id()
    
#     # Ensure required directories exist
#     ensure_directory_exists(PINS_DIR)
#     ensure_directory_exists(DATA_DIR)
    
#     # Ensure required files exist
#     ensure_file_exists(URLS_FILE)
    
#     # Read URLs 
#     all_urls = read_urls(URLS_FILE)
    
#     if not all_urls:
#         print("No URLs found to process.")
#         return
    
#     # Take the next batch of URLs
#     batch_urls = all_urls[:BATCH_SIZE]
#     remaining_urls = all_urls[BATCH_SIZE:]
#     print(f"Processing batch of {len(batch_urls)} URLs")
#     print(f"Using {len(api_keys)} Gemini API keys for load balancing")
    
#     # Create CSV file for this batch
#     batch_csv_path = os.path.join(DATA_DIR, f"pinterest_pins_{run_id}.csv")
    
#     # Initialize CSV output with the exact column order requested
#     csv_output = StringIO()
#     csv_writer = csv.writer(csv_output, quoting=csv.QUOTE_MINIMAL)
#     csv_writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Thumbnail', 'Link', 'Publish date', 'Description', 'Keywords'])

#     # Storage for generated images
#     generated_images = []

#     # Cache for board names to reduce API calls
#     board_cache = {}
    
#     # Track API usage for load balancing
#     api_usage_count = {key: 0 for key in api_keys}

#     # Process each URL in the batch
#     for i, url in enumerate(batch_urls):
#         print(f"\nProcessing URL {i+1}/{len(batch_urls)}: {url}")
#         domain_name = get_domain_from_url(url)

#         try:
#             # Generate pin content
#             print("Generating pin content with Gemma model...")
#             csv_content = generate_pin_content(url, PINS_PER_URL)

#             if csv_content.startswith("Error"):
#                 print(f"Error generating pin content: {csv_content}")
#                 continue

#             # Parse the generated content
#             pins = parse_csv_content(csv_content)
#             print(f"Generated {len(pins)} pin ideas")

#             # Extract topic from URL
#             topic = extract_topic_from_url(url)
#             print(f"Extracted topic: {topic}")

#             # Create images and upload to Cloudinary for each pin
#             for j, pin in enumerate(pins):
#                 print(f"Creating image {j+1}/{len(pins)}...")

#                 # Validate pin data
#                 if not pin.get('Title') or not pin.get('Description') or not pin.get('Keywords'):
#                     print(f"Skipping pin with incomplete data: {pin}")
#                     continue

#                 # Generate image prompt based on pin title and URL topic
#                 image_prompt = f"""
#                 Create a visually appealing Pinterest pin image for the title: "{pin['Title']}"

#                 {topic}

#                 The image should be:
#                 - In portrait orientation (2:3 ratio) for Pinterest
#                 - Visually striking with bold colors
#                 - Include minimal text elements
#                 - Professional, clean design that would appeal to Pinterest users
#                 - Suitable for home decor/cleaning tips context
#                 - Include visual elements related to {topic}
#                 """

#                 # Generate image with Gemini - distribute among API keys
#                 file_name = f"pin_{i+1}_{j+1}"
#                 image_url = None
#                 repo_image_path = None

#                 try:
#                     # Use a different API key for each image to distribute load
#                     key_manager.get_random_client()
#                     image_data, image_mime_type, image_file_path = generate_image_with_gemini(image_prompt, file_name)

#                     if image_file_path and os.path.exists(image_file_path):
#                         # Generate board name first (needed for repository path)
#                         cache_key = pin['Title'][:15].lower()  # Use first part of title as cache key
#                         if cache_key in board_cache:
#                             board_name = board_cache[cache_key]
#                             print(f"Using cached board name: {board_name}")
#                         else:
#                             print("Generating board name with Gemma model...")
#                             board_name = generate_board_category(pin['Title'], pin['Keywords'])
#                             board_cache[cache_key] = board_name
#                             print(f"Generated board name: {board_name}")
                        
#                         # Copy image to repository structure
#                         repo_image_path = copy_image_to_repo(image_file_path, url, board_name, pin['Title'])
#                         print(f"Copied image to repository: {repo_image_path}")
                        
#                         # Upload to Cloudinary
#                         print("Uploading to Cloudinary...")
#                         image_url = upload_to_cloudinary(image_file_path)

#                         if image_url:
#                             generated_images.append({
#                                 'file_path': image_file_path,
#                                 'repo_path': repo_image_path,
#                                 'url': image_url,
#                                 'title': pin['Title']
#                             })
#                     else:
#                         raise Exception("Image file not created properly")

#                 except Exception as e:
#                     print(f"Error generating/uploading image: {str(e)}")
#                     # Use a placeholder image URL if image generation fails
#                     image_url = "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg"
#                     board_name = "home-inspiration"  # Default fallback

#                 # Generate a unique UTM campaign parameter based on pin title
#                 utm_campaign = create_slug(pin['Title'])[:20]  # Limit length for URL compatibility

#                 # Create the tracked URL with UTM parameters
#                 tracked_url = url
#                 if '?' in tracked_url:
#                     tracked_url += f"&utm_source=pinterest&utm_campaign={utm_campaign}"
#                 else:
#                     tracked_url += f"?utm_source=pinterest&utm_campaign={utm_campaign}"

#                 # Extract keywords for the extra field
#                 extra_keywords = extract_keywords_for_extra_field(pin['Keywords'])
                
#                 # Format the current date
#                 current_date = datetime.now().strftime('%Y-%m-%d')
                
#                 # Add to CSV with proper quoting to avoid field delimiter issues
#                 csv_writer.writerow([
#                     pin['Title'],                        # Title
#                     image_url if image_url else "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg", # Media URL
#                     board_name,                          # Pinterest board
#                     '',                                  # Thumbnail (empty)
#                     tracked_url,                         # Link (with UTM parameters)
#                     current_date,                        # Publish date
#                     pin['Description'],                  # Description
#                     pin['Keywords']                      # Keywords
#                 ])

#                 # Add a small delay to prevent rate limiting
#                 time.sleep(2)

#         except Exception as e:
#             print(f"Error processing URL {url}: {str(e)}")
#             # Keep the URL in the list if there was an error
#             remaining_urls.append(url)

#     # Save CSV file to repository
#     with open(batch_csv_path, 'w', newline='', encoding='utf-8') as f:
#         f.write(csv_output.getvalue())
    
#     # Create CSV file for all pins (append to existing or create new)
#     all_pins_csv_path = os.path.join(DATA_DIR, "all_pinterest_pins.csv")
#     if os.path.exists(all_pins_csv_path):
#         # Read existing data
#         existing_df = pd.read_csv(all_pins_csv_path)
#         # Read new data
#         csv_output.seek(0)
#         new_df = pd.read_csv(csv_output)
#         # Combine and save
#         combined_df = pd.concat([existing_df, new_df], ignore_index=True)
#         combined_df.to_csv(all_pins_csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
#     else:
#         # Just save current batch as all pins
#         csv_output.seek(0)
#         with open(all_pins_csv_path, 'w', newline='', encoding='utf-8') as f:
#             f.write(csv_output.getvalue())
    
#     # Create zip archive of all generated images
#     if generated_images:
#         timestamp = int(time.time())
#         zip_filename = f"pinterest_images_{timestamp}.zip"

#         with zipfile.ZipFile(zip_filename, 'w') as zipf:
#             for image in generated_images:
#                 if os.path.exists(image['file_path']):
#                     zipf.write(image['file_path'])

#         print(f"\nImages zipped to {zip_filename}")

#     # Write remaining URLs back to file
#     write_urls(URLS_FILE, remaining_urls)
    
#     # Send email notification
#     print("Sending email notification...")
#     csv_output.seek(0)
#     send_email_notification(
#         TO_EMAIL,
#         FROM_EMAIL,
#         APP_PASSWORD,
#         csv_output,
#         f"Pinterest Pin Generation - Batch of {len(batch_urls)} URLs"
#     )
    
#     print("\nProcess completed successfully!")
#     print(f"Processed {len(batch_urls)} URLs, {len(remaining_urls)} URLs remaining")
    
#     # Set output for GitHub Actions
#     with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
#         f.write(f"processed_urls={len(batch_urls)}\n")
#         f.write(f"remaining_urls={len(remaining_urls)}\n")

# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
# .github/scripts/process_urls.py

import os
import csv
import time
import json
import smtplib
import requests
import pandas as pd
import mimetypes
import re
import zipfile
import shutil
import random
from io import BytesIO, StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from PIL import Image
from datetime import datetime
from google import genai
from google.genai import types

# Constants
BATCH_SIZE = 5
URLS_FILE = "urls.txt"
PINS_DIR = "pins"
DATA_DIR = "data"
PINS_PER_URL = 25  # Reduce number of pins per URL for GitHub Actions

# Email configuration
TO_EMAIL = "beacleaner0@gmail.com"
FROM_EMAIL = "limon.working@gmail.com"
APP_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# Initialize API clients with multiple API keys
def get_api_keys():
    """Get all available API keys from environment variables"""
    keys = []
    
    # Check for primary API key
    primary_key = os.environ.get("GEMINI_API_KEY")
    if primary_key:
        keys.append(primary_key)
    
    # Check for numbered API keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    i = 1
    while True:
        key = os.environ.get(f"GEMINI_API_KEY_{i}")
        if key:
            keys.append(key)
            i += 1
        else:
            break
    
    if not keys:
        raise ValueError("No Gemini API keys found in environment variables")
    
    print(f"Found {len(keys)} Gemini API keys")
    return keys

# Create API key manager class
class APIKeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.key_ids = [f"Key {i+1}" for i in range(len(api_keys))]
        self.current_index = 0
        self.clients = {self.key_ids[i]: genai.Client(api_key=key) for i, key in enumerate(self.api_keys)}
    
    def get_client(self):
        """Get the current client and its key ID"""
        key_id = self.key_ids[self.current_index]
        return self.clients[key_id], key_id
    
    def get_current_key_id(self):
        """Get the current key identifier"""
        return self.key_ids[self.current_index]
    
    def rotate_key(self):
        """Rotate to the next API key"""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        key_id = self.key_ids[self.current_index]
        print(f"Rotated to {key_id}")
        return self.get_client()
    
    def get_random_client(self):
        """Get a random client to distribute load"""
        self.current_index = random.randint(0, len(self.api_keys) - 1)
        key_id = self.key_ids[self.current_index]
        return self.clients[key_id], key_id

# Initialize API key manager with all available keys
api_keys = get_api_keys()
key_manager = APIKeyManager(api_keys)

def ensure_directory_exists(directory):
    """Ensure a directory exists, creating it if needed"""
    os.makedirs(directory, exist_ok=True)
    return directory

def ensure_file_exists(file_path, default_content=""):
    """Ensure a file exists, creating it with default content if needed"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(default_content)
    return file_path

def read_urls(file_path):
    """Read URLs from a text file"""
    if not os.path.exists(file_path):
        return []
        
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip() and line.strip().startswith('http')]

def write_urls(file_path, urls):
    """Write URLs to a file"""
    with open(file_path, "w") as f:
        for url in urls:
            f.write(f"{url}\n")

def save_binary_file(file_name, data):
    """Save binary data to a file"""
    with open(file_name, "wb") as f:
        f.write(data)
    return file_name

def compress_image(image_path, quality=85):
    """Compress image and convert to WebP format"""
    try:
        with Image.open(image_path) as img:
            webp_path = f"{os.path.splitext(image_path)[0]}.webp"
            img.save(webp_path, 'WEBP', quality=quality)
            if os.path.exists(image_path):
                os.remove(image_path)  # Remove original file
            return webp_path
    except Exception as e:
        print(f"Image compression error: {e}")
        return image_path

def upload_to_cloudinary(file_path, resource_type="image"):
    """Upload file to Cloudinary using direct API call"""
    url = f"https://api.cloudinary.com/v1_1/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/{resource_type}/upload"
    payload = {
        'upload_preset': 'ml_default',
        'api_key': os.environ.get('CLOUDINARY_API_KEY')
    }
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            return response.json()['secure_url']
        print(f"Upload failed: {response.text}")
        return None
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def generate_image_with_gemini(prompt, file_name, max_retries=3):
    """Generate an image using Gemini 2.0 Flash image generation model with retry logic"""
    for attempt in range(max_retries):
        client, key_id = key_manager.get_client()
        print(f"Attempt {attempt+1}/{max_retries} with {key_id} for image generation")
        try:
            model = "gemini-2.0-flash-exp-image-generation"
            contents = [types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )]

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=["image", "text"])
            )

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        inline_data = part.inline_data
                        file_ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                        file_path = f"{file_name}{file_ext}"

                        save_binary_file(file_path, inline_data.data)
                        final_path = compress_image(file_path)
                        print(f"Successfully generated image with {key_id} and saved to: {final_path}")
                        return inline_data.data, inline_data.mime_type, final_path

            raise Exception("No image data found in response")
            
        except Exception as e:
            print(f"Failed with {key_id}: {str(e)}")
            if attempt < max_retries - 1:
                key_manager.rotate_key()
                time.sleep(2)
            else:
                print("All retries failed")
                return None, None, None

def call_gemini_with_retry(model, contents, config, max_retries=3):
    """Call Gemini API with retry logic for rate limits"""
    for attempt in range(max_retries):
        client, key_id = key_manager.get_client()
        print(f"Attempt {attempt+1}/{max_retries} with {key_id} for content generation")
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            print(f"Successfully generated content with {key_id}")
            return response
        except Exception as e:
            error_str = str(e).lower()
            print(f"Failed with {key_id}: {error_str}")
            if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    key_manager.rotate_key()
                    time.sleep(2)
                else:
                    print("All API keys are rate limited. Giving up.")
                    raise
            else:
                raise

def generate_pin_content(url, pins_per_url=5, max_retries=3):
    """Generate Pinterest pin content using Gemma model with retry logic"""
    try:
        model = "gemma-3-27b-it"
        contents = [types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"""
            Create {pins_per_url} unique Pinterest pin ideas for the blog post at {url}.
            For each pin, provide:
            1. An engaging title (under 70 characters)
            2. A compelling description (must be 350-400 characters) that includes hashtags at the end
            3. 3-4 relevant keywords separated by commas
            
            The description MUST end with relevant hashtags like #Keyword1 #Keyword2.
            
            Format your response as CSV data with these exact columns:
            Title,Description,Keywords
            
            Make each pin unique with different angles or highlights from the blog post.
            Include calls to action and emotional appeals in descriptions.
            Do NOT include quotation marks around the title or description.
            """)]
        )]

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192,
            response_mime_type="text/plain",
        )

        print(f"Generating pin content with Gemma model for URL: {url}")
        response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)
        
        return response.text if response.text else "No content generated"
    except Exception as e:
        print(f"Error generating pin content: {str(e)}")
        return f"Error: {str(e)}"

def generate_board_category(title, keywords, max_retries=3):
    """Generate Pinterest board category using Gemma model with retry logic"""
    try:
        model = "gemma-3-27b-it"
        contents = [types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"""
            Analyze this Pinterest pin title and keywords, then suggest ONE specific board name
            that would be most appropriate for this content on Pinterest.

            Title: {title}
            Keywords: {keywords}

            Return ONLY the board name, nothing else. The board name should be:
            - 2-3 words maximum
            - Descriptive of the content category
            - End with "ideas" or "inspiration" or "tips"
            - Lowercase with hyphens between words (e.g., "home-decor-ideas")
            - Common Pinterest board category that would have wide appeal
            - NOT include the brand name or website name

            JUST RETURN THE BOARD NAME ONLY.
            """)]
        )]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            top_k=40,
            max_output_tokens=20,
            response_mime_type="text/plain",
        )

        response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)

        board_name = response.text.strip().lower()
        board_name = re.sub(r'[^a-z0-9\s-]', '', board_name)
        board_name = re.sub(r'[\s]+', '-', board_name)
        board_name = board_name.strip('-')

        if not board_name or len(board_name) < 3:
            return "home-inspiration"
        return board_name
    except Exception as e:
        print(f"Error generating board category: {str(e)}")
        return "home-inspiration"

def parse_csv_content(csv_content):
    """Parse CSV content from API response using a more robust approach"""
    pins = []
    
    try:
        csv_file = StringIO(csv_content.strip())
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        start_idx = 0
        if rows and len(rows) > 0:
            if 'Title' in rows[0][0] and 'Description' in ''.join(rows[0]):
                start_idx = 1
                
        for i in range(start_idx, len(rows)):
            row = rows[i]
            if not row or not ''.join(row).strip():
                continue
                
            if len(row) >= 3:
                title = row[0].strip()
                description = row[1].strip()
                keywords = row[2].strip()
                
                title = title.strip('"\'')
                description = description.strip('"\'')
                
                if title and description and keywords:
                    pins.append({
                        'Title': title,
                        'Description': description,
                        'Keywords': keywords
                    })
                    
    except Exception as e:
        print(f"Error parsing CSV with reader: {str(e)}")
        try:
            lines = csv_content.strip().split('\n')
            start_idx = 0
            if 'Title' in lines[0] and 'Description' in lines[0]:
                start_idx = 1
            
            for i in range(start_idx, len(lines)):
                line = lines[i]
                if not line.strip():
                    continue
                
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        title = parts[0].strip()
                        description = ','.join(parts[1:-1]).strip()
                        keywords = parts[-1].strip()
                        
                        title = title.strip('"\'')
                        description = description.strip('"\'')
                        
                        if title and description and keywords:
                            pins.append({
                                'Title': title,
                                'Description': description,
                                'Keywords': keywords
                            })
        except Exception as e:
            print(f"Error in fallback parsing: {str(e)}")

    return pins

def send_email_notification(to_email, from_email, app_password, csv_data, subject="Pinterest Pin Generation Complete"):
    """Send email with CSV attachment"""
    if not app_password:
        print("No email password provided. Skipping email notification.")
        return False
        
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = f"{subject} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    body = f"""
    Hello,

    Your Pinterest pin generation process has completed successfully.
    The CSV file with the generated pins is attached.

    Time of completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    msg.attach(MIMEText(body, 'plain'))

    if isinstance(csv_data, StringIO):
        attachment_data = csv_data.getvalue().encode('utf-8')
    else:
        attachment_data = csv_data.getvalue()

    csv_attachment = MIMEApplication(attachment_data)
    csv_attachment['Content-Disposition'] = 'attachment; filename="pinterest_pins.csv"'
    msg.attach(csv_attachment)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, app_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def create_slug(text):
    """Generate SEO-friendly slug from text"""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    slug = slug[:100]
    return slug

def extract_topic_from_url(url):
    """Extract topic from URL for image generation prompt"""
    path = url.split('/')
    article_segment = None
    for segment in path:
        if segment and segment not in ['http:', 'https:', '', 'www', 'com', 'org', 'net']:
            if '.' not in segment and segment not in ['utm_source', 'utm_campaign', 'utm_medium', 'utm_term']:
                article_segment = segment
                break

    if article_segment:
        topic = article_segment.replace('-', ' ').replace('_', ' ').title()
        return topic
    return "Home Decor"

def get_domain_from_url(url):
    """Extract domain from URL for organization"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return "unknown-domain"

def create_run_id():
    """Create a unique ID for this run based on timestamp"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def copy_image_to_repo(source_path, url, board_name, title):
    """Copy generated image to repository directory structure"""
    domain = get_domain_from_url(url)
    slug = create_slug(title)[:40]
    
    target_dir = os.path.join(PINS_DIR, domain, board_name)
    ensure_directory_exists(target_dir)
    
    file_ext = os.path.splitext(source_path)[1]
    target_path = os.path.join(target_dir, f"{slug}{file_ext}")
    
    shutil.copy2(source_path, target_path)
    return target_path

def extract_keywords_for_extra_field(keywords_str):
    """Extract keywords for the extra 'Keywords' column"""
    keywords_list = [k.strip() for k in keywords_str.split(',')]
    return ', '.join(keywords_list)

def main():
    print("Pinterest Pin Maker - GitHub Actions Version")
    print("------------------------------------------")
    
    run_id = create_run_id()
    
    ensure_directory_exists(PINS_DIR)
    ensure_directory_exists(DATA_DIR)
    ensure_file_exists(URLS_FILE)
    
    all_urls = read_urls(URLS_FILE)
    
    if not all_urls:
        print("No URLs found to process.")
        return
    
    batch_urls = all_urls[:BATCH_SIZE]
    remaining_urls = all_urls[BATCH_SIZE:]
    print(f"Processing batch of {len(batch_urls)} URLs")
    print(f"Using {len(api_keys)} Gemini API keys for load balancing")
    
    batch_csv_path = os.path.join(DATA_DIR, f"pinterest_pins_{run_id}.csv")
    
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output, quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Thumbnail', 'Link', 'Publish date', 'Description', 'Keywords'])

    generated_images = []
    board_cache = {}
    api_usage_count = {key: 0 for key in api_keys}

    for i, url in enumerate(batch_urls):
        print(f"\nProcessing URL {i+1}/{len(batch_urls)}: {url}")
        domain_name = get_domain_from_url(url)

        try:
            print("Generating pin content with Gemma model...")
            csv_content = generate_pin_content(url, PINS_PER_URL)

            if csv_content.startswith("Error"):
                print(f"Error generating pin content: {csv_content}")
                continue

            pins = parse_csv_content(csv_content)
            print(f"Generated {len(pins)} pin ideas")

            topic = extract_topic_from_url(url)
            print(f"Extracted topic: {topic}")

            for j, pin in enumerate(pins):
                print(f"Creating image {j+1}/{len(pins)}...")

                if not pin.get('Title') or not pin.get('Description') or not pin.get('Keywords'):
                    print(f"Skipping pin with incomplete data: {pin}")
                    continue

                image_prompt = f"""
                Create a visually appealing Pinterest pin image for the title: "{pin['Title']}"

                {topic}

                The image should be:
                - In portrait orientation (2:3 ratio) for Pinterest
                - Visually striking with bold colors
                - Include minimal text elements
                - Professional, clean design that would appeal to Pinterest users
                - Suitable for home decor/cleaning tips context
                - Include visual elements related to {topic}
                """

                file_name = f"pin_{i+1}_{j+1}"
                image_url = None
                repo_image_path = None

                try:
                    key_manager.get_random_client()
                    current_key_id = key_manager.get_current_key_id()
                    print(f"Starting image generation for pin {j+1} with {current_key_id}")
                    image_data, image_mime_type, image_file_path = generate_image_with_gemini(image_prompt, file_name)

                    if image_file_path and os.path.exists(image_file_path):
                        cache_key = pin['Title'][:15].lower()
                        if cache_key in board_cache:
                            board_name = board_cache[cache_key]
                            print(f"Using cached board name: {board_name}")
                        else:
                            print("Generating board name with Gemma model...")
                            board_name = generate_board_category(pin['Title'], pin['Keywords'])
                            board_cache[cache_key] = board_name
                            print(f"Generated board name: {board_name}")
                        
                        repo_image_path = copy_image_to_repo(image_file_path, url, board_name, pin['Title'])
                        print(f"Copied image to repository: {repo_image_path}")
                        
                        print("Uploading to Cloudinary...")
                        image_url = upload_to_cloudinary(image_file_path)

                        if image_url:
                            generated_images.append({
                                'file_path': image_file_path,
                                'repo_path': repo_image_path,
                                'url': image_url,
                                'title': pin['Title']
                            })
                    else:
                        raise Exception("Image file not created properly")

                except Exception as e:
                    print(f"Error generating/uploading image: {str(e)}")
                    image_url = "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg"
                    board_name = "home-inspiration"

                utm_campaign = create_slug(pin['Title'])[:20]
                tracked_url = url
                if '?' in tracked_url:
                    tracked_url += f"&utm_source=pinterest&utm_campaign={utm_campaign}"
                else:
                    tracked_url += f"?utm_source=pinterest&utm_campaign={utm_campaign}"

                extra_keywords = extract_keywords_for_extra_field(pin['Keywords'])
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                csv_writer.writerow([
                    pin['Title'],
                    image_url if image_url else "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg",
                    board_name,
                    '',
                    tracked_url,
                    current_date,
                    pin['Description'],
                    pin['Keywords']
                ])

                time.sleep(2)

        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            remaining_urls.append(url)

    with open(batch_csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(csv_output.getvalue())
    
    all_pins_csv_path = os.path.join(DATA_DIR, "all_pinterest_pins.csv")
    if os.path.exists(all_pins_csv_path):
        existing_df = pd.read_csv(all_pins_csv_path)
        csv_output.seek(0)
        new_df = pd.read_csv(csv_output)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(all_pins_csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    else:
        csv_output.seek(0)
        with open(all_pins_csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_output.getvalue())
    
    if generated_images:
        timestamp = int(time.time())
        zip_filename = f"pinterest_images_{timestamp}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for image in generated_images:
                if os.path.exists(image['file_path']):
                    zipf.write(image['file_path'])
        print(f"\nImages zipped to {zip_filename}")

    write_urls(URLS_FILE, remaining_urls)
    
    print("Sending email notification...")
    csv_output.seek(0)
    send_email_notification(
        TO_EMAIL,
        FROM_EMAIL,
        APP_PASSWORD,
        csv_output,
        f"Pinterest Pin Generation - Batch of {len(batch_urls)} URLs"
    )
    
    print("\nProcess completed successfully!")
    print(f"Processed {len(batch_urls)} URLs, {len(remaining_urls)} URLs remaining")
    
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f"processed_urls={len(batch_urls)}\n")
        f.write(f"remaining_urls={len(remaining_urls)}\n")

if __name__ == "__main__":
    main()