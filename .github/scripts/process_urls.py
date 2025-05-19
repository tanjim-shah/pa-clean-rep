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

#!/usr/bin/env python3
# .github/scripts/process_urls.py

import logging
from tqdm import tqdm

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

# Set up logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = os.path.join(DATA_DIR, "logs")
    ensure_directory_exists(log_dir)
    
    log_file = os.path.join(log_dir, f"pinterest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Create a logger
    logger = logging.getLogger("pinterest_maker")
    logger.info(f"Starting Pinterest Pin Maker - Log file: {log_file}")
    
    return logger

class ProgressTracker:
    """Track and report progress of the pin generation process"""
    def __init__(self, total_urls, total_pins):
        self.total_urls = total_urls
        self.total_pins = total_pins
        self.processed_urls = 0
        self.processed_pins = 0
        self.successful_pins = 0
        self.failed_pins = 0
        self.start_time = datetime.now()
        self.url_progress_bar = tqdm(total=total_urls, desc="URLs processed")
        self.pin_progress_bar = tqdm(total=total_pins, desc="Pins created  ")
        
    def update_url_progress(self, increment=1):
        """Update URL processing progress"""
        self.processed_urls += increment
        self.url_progress_bar.update(increment)
        
    def update_pin_progress(self, successful=0, failed=0):
        """Update pin creation progress"""
        self.processed_pins += (successful + failed)
        self.successful_pins += successful
        self.failed_pins += failed
        self.pin_progress_bar.update(successful + failed)
        
    def get_summary(self):
        """Get summary statistics of the progress"""
        elapsed_time = datetime.now() - self.start_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        # Calculate rates
        urls_per_hour = (self.processed_urls / elapsed_seconds) * 3600 if elapsed_seconds > 0 else 0
        pins_per_hour = (self.processed_pins / elapsed_seconds) * 3600 if elapsed_seconds > 0 else 0
        
        # Calculate success rate
        success_rate = (self.successful_pins / max(1, self.processed_pins)) * 100
        
        # Estimate time remaining
        remaining_urls = self.total_urls - self.processed_urls
        estimated_seconds_remaining = (remaining_urls / max(0.1, urls_per_hour)) * 3600 if urls_per_hour > 0 else 0
        
        # Format time remaining
        hours, remainder = divmod(int(estimated_seconds_remaining), 3600)
        minutes, seconds = divmod(remainder, 60)
        estimated_time_remaining = f"{hours}h {minutes}m {seconds}s"
        
        summary = {
            "processed_urls": self.processed_urls,
            "total_urls": self.total_urls,
            "processed_pins": self.processed_pins,
            "successful_pins": self.successful_pins,
            "failed_pins": self.failed_pins,
            "success_rate": success_rate,
            "elapsed_time": str(elapsed_time).split('.')[0],
            "urls_per_hour": urls_per_hour,
            "pins_per_hour": pins_per_hour,
            "estimated_time_remaining": estimated_time_remaining
        }
        
        return summary
    
    def close(self):
        """Close progress bars"""
        self.url_progress_bar.close()
        self.pin_progress_bar.close()
    
    def print_summary(self):
        """Print progress summary"""
        summary = self.get_summary()
        
        print("\n\n=== Pinterest Pin Generation Summary ===")
        print(f"URLs processed: {summary['processed_urls']}/{summary['total_urls']} ({summary['processed_urls']/max(1, summary['total_urls'])*100:.1f}%)")
        print(f"Pins created: {summary['processed_pins']} (Success: {summary['successful_pins']}, Failed: {summary['failed_pins']})")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Elapsed time: {summary['elapsed_time']}")
        print(f"Processing rate: {summary['urls_per_hour']:.1f} URLs/hour, {summary['pins_per_hour']:.1f} pins/hour")
        print(f"Estimated time remaining: {summary['estimated_time_remaining']}")
        print("=========================================")

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

# Enhanced API Key Manager with metrics
class APIKeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_index = 0
        self.clients = {}
        
        # Initialize clients for each API key
        for key in self.api_keys:
            self.clients[key] = genai.Client(api_key=key)
        
        # Add metrics tracking
        self.usage = {key: {"calls": 0, "rate_limits": 0, "errors": 0, "last_used": None} for key in api_keys}
        self.metrics_file = os.path.join(DATA_DIR, "api_metrics.json")
        self.load_metrics()
    
    def load_metrics(self):
        """Load existing metrics if available"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    # Merge saved metrics with current keys
                    for key in self.api_keys:
                        if key in saved_metrics:
                            self.usage[key] = saved_metrics[key]
            except Exception as e:
                print(f"Error loading metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics: {e}")
    
    def get_client(self):
        """Get the current client"""
        key = self.api_keys[self.current_index]
        self.usage[key]["last_used"] = datetime.now().isoformat()
        return self.clients[key]
    
    def rotate_key(self):
        """Rotate to the next API key"""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        key = self.api_keys[self.current_index]
        self.usage[key]["last_used"] = datetime.now().isoformat()
        print(f"Rotated to API key {self.current_index + 1}/{len(self.api_keys)}")
        return self.get_client()
    
    def get_random_client(self):
        """Get a random client to distribute load"""
        self.current_index = random.randint(0, len(self.api_keys) - 1)
        key = self.api_keys[self.current_index]
        self.usage[key]["last_used"] = datetime.now().isoformat()
        return self.get_client()
    
    def log_success(self):
        """Log successful API call"""
        key = self.api_keys[self.current_index]
        self.usage[key]["calls"] += 1
        self.save_metrics()
    
    def log_rate_limit(self):
        """Log rate limit error"""
        key = self.api_keys[self.current_index]
        self.usage[key]["rate_limits"] += 1
        self.save_metrics()
    
    def log_error(self):
        """Log general error"""
        key = self.api_keys[self.current_index]
        self.usage[key]["errors"] += 1
        self.save_metrics()
    
    def get_healthiest_key(self):
        """Get the key with the lowest rate limit count"""
        # Find key with lowest rate limit and error ratio
        best_key_index = 0
        best_score = float('inf')
        
        for i, key in enumerate(self.api_keys):
            # Calculate a health score based on rate limits and total calls
            total_calls = max(1, self.usage[key]["calls"]) 
            rate_limit_ratio = self.usage[key]["rate_limits"] / total_calls
            error_ratio = self.usage[key]["errors"] / total_calls
            score = (rate_limit_ratio * 10) + (error_ratio * 5)  # Weighted score
            
            if score < best_score:
                best_score = score
                best_key_index = i
        
        self.current_index = best_key_index
        return self.get_client()
    
    def print_usage_stats(self):
        """Print API key usage statistics"""
        print("\nAPI Key Usage Statistics:")
        print("-------------------------")
        for i, key in enumerate(self.api_keys):
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
            total_calls = self.usage[key]["calls"]
            rate_limits = self.usage[key]["rate_limits"]
            errors = self.usage[key]["errors"]
            last_used = self.usage[key]["last_used"]
            
            success_rate = ((total_calls - rate_limits - errors) / max(1, total_calls)) * 100
            
            print(f"Key {i+1}: {masked_key}")
            print(f"  Total calls: {total_calls}")
            print(f"  Rate limits: {rate_limits}")
            print(f"  Other errors: {errors}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Last used: {last_used}")
        print("-------------------------")

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

def read_urls_with_metadata(file_path):
    """Read URLs from a text file with optional metadata"""
    if not os.path.exists(file_path):
        return []
    
    urls_with_metadata = []
    
    with open(file_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or not line.startswith('http'):
                continue
            
            # Check if the line has metadata in JSON format after the URL
            parts = line.split('::')
            url = parts[0].strip()
            
            metadata = {}
            if len(parts) > 1:
                try:
                    metadata = json.loads(parts[1])
                except json.JSONDecodeError:
                    metadata = {"notes": parts[1]}
            
            # Add default priority if not present
            if "priority" not in metadata:
                metadata["priority"] = 5  # Default priority (1-10 scale)
            
            urls_with_metadata.append({
                "url": url,
                "metadata": metadata
            })
    
    return urls_with_metadata

def write_urls_with_metadata(file_path, urls_with_metadata):
    """Write URLs with metadata back to file"""
    with open(file_path, "w") as f:
        for item in urls_with_metadata:
            url = item["url"]
            metadata = item["metadata"]
            
            # Convert metadata to JSON string
            metadata_str = json.dumps(metadata)
            
            # Write URL and metadata to file
            f.write(f"{url}::{metadata_str}\n")

def get_next_batch(urls_with_metadata, batch_size):
    """Get the next batch of URLs based on priority"""
    # Sort by priority (higher number = higher priority)
    sorted_urls = sorted(urls_with_metadata, key=lambda x: x["metadata"].get("priority", 5), reverse=True)
    
    # Take the top batch_size URLs
    batch = sorted_urls[:batch_size]
    remaining = sorted_urls[batch_size:]
    
    return batch, remaining

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
        try:
            # Get current client or rotate after a failure
            if attempt > 0:
                client = key_manager.rotate_key()
            else:
                client = key_manager.get_client()
                
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

            # Process response to extract image
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        inline_data = part.inline_data
                        file_ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                        file_path = f"{file_name}{file_ext}"

                        # Save the file
                        save_binary_file(file_path, inline_data.data)

                        # Compress and convert to WebP
                        final_path = compress_image(file_path)

                        print(f"Image generated and saved to: {final_path}")
                        return inline_data.data, inline_data.mime_type, final_path

            raise Exception("No image data found in response")
            
        except Exception as e:
            print(f"Error generating image (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying with different API key...")
                time.sleep(2)  # Add a small delay before retry
            else:
                print("All retries failed")
                return None, None, None

def call_gemini_with_retry(model, contents, config, max_retries=3):
    """Call Gemini API with retry logic for rate limits"""
    for attempt in range(max_retries):
        try:
            # Get current client or rotate after a failure
            if attempt > 0:
                client = key_manager.rotate_key()
            else:
                client = key_manager.get_client()
                
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            print(f"API error (attempt {attempt+1}/{max_retries}): {error_str}")
            
            # Check for rate limit errors
            if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Rotating API key and retrying...")
                    time.sleep(2)  # Add a small delay before retry
                else:
                    print("All API keys are rate limited. Giving up.")
                    raise
            else:
                # For non-rate-limit errors, don't retry
                raise

def assess_content_quality(content, content_type="pin"):
    """Assess the quality of generated content and determine if retry is needed"""
    if not content or content.startswith("Error"):
        return False, "Empty or error response"
    
    if content_type == "pin":
        # Check for CSV structure
        if "Title,Description,Keywords" not in content and "," not in content:
            return False, "Missing CSV structure"
        
        # Check number of pins (at least 3)
        lines = content.strip().split('\n')
        data_lines = [line for line in lines if line.strip() and ',' in line]
        if len(data_lines) < 3:
            return False, f"Too few pins generated ({len(data_lines)})"
        
        # Check for common error patterns
        error_patterns = ["I apologize", "I cannot", "unable to", "sorry", "error"]
        for pattern in error_patterns:
            if pattern.lower() in content.lower():
                return False, f"Error pattern detected: '{pattern}'"
    
    elif content_type == "board":
        # Check board name quality
        if not content or len(content) < 3:
            return False, "Board name too short"
        
        if len(content.split()) > 3:
            return False, "Board name too verbose"
    
    return True, "Content passed quality check"

def generate_pin_content(url, pins_per_url=5, max_retries=3, quality_retries=2):
    """Generate Pinterest pin content using Gemma model with quality assessment"""
    best_content = None
    best_quality_score = 0
    
    for quality_attempt in range(quality_retries):
        try:
            model = "gemma-3-27b-it"  # Using Gemma model
            
            # Adjust the prompt slightly each retry for variety
            if quality_attempt > 0:
                temperature = 0.9 + (quality_attempt * 0.1)  # Increase temperature for more variety
                print(f"Quality retry attempt {quality_attempt+1}/{quality_retries} with temperature {temperature}")
            else:
                temperature = 1.0
            
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
                temperature=temperature,
                top_p=0.95,
                top_k=64,
                max_output_tokens=8192,
                response_mime_type="text/plain",
            )

            print(f"Generating pin content with Gemma model for URL: {url}")
            
            # Call with retry logic
            response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)
            
            if not response.text:
                print("Empty response received")
                continue
                
            # Assess content quality
            is_good, quality_message = assess_content_quality(response.text, "pin")
            
            # Parse content to count valid pins
            pins = parse_csv_content(response.text)
            quality_score = len(pins)
            
            print(f"Generated {len(pins)} pins, quality check: {is_good}, {quality_message}")
            
            # Keep track of best content so far
            if is_good and quality_score > best_quality_score:
                best_content = response.text
                best_quality_score = quality_score
                
                # If we got a good result with enough pins, don't need more retries
                if quality_score >= pins_per_url * 0.8:  # At least 80% of requested pins
                    break
                    
        except Exception as e:
            print(f"Error generating pin content (quality attempt {quality_attempt+1}): {str(e)}")
    
    # Return best content or error message
    if best_content:
        return best_content
    else:
        return f"Error: Failed to generate quality content after {quality_retries} attempts"

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
            - End with "ideas" or "inspiration"
            - Lowercase with hyphens between words (e.g., "home-decor-ideas")
            - Common Pinterest board category that would have wide appeal
            - NOT include the brand name or website name

            JUST RETURN THE BOARD NAME ONLY.
            """)]
        )]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,  # Lower temperature for more consistent results
            top_p=0.95,
            top_k=40,
            max_output_tokens=20,  # Short response
            response_mime_type="text/plain",
        )

        # Call with retry logic
        response = call_gemini_with_retry(model, contents, generate_content_config, max_retries)

        board_name = response.text.strip().lower()

        # Clean up the board name
        board_name = re.sub(r'[^a-z0-9\s-]', '', board_name)
        board_name = re.sub(r'[\s]+', '-', board_name)
        board_name = board_name.strip('-')

        # Fallback if the model returns something invalid
        if not board_name or len(board_name) < 3:
            return "home-inspiration"

        return board_name
    except Exception as e:
        print(f"Error generating board category: {str(e)}")
        return "home-inspiration"  # Default fallback

def parse_csv_content(csv_content):
    """Parse CSV content from API response"""
    pins = []
    lines = csv_content.strip().split('\n')

    # Skip header if present
    start_idx = 0
    if 'Title' in lines[0] and 'Description' in lines[0]:
        start_idx = 1

    # Process each line
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not line.strip():
            continue

        try:
            # Handle potential CSV formatting issues
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    title = parts[0].strip()
                    description = ','.join(parts[1:-1]).strip()  # Join all middle parts in case descriptions have commas
                    keywords = parts[-1].strip()

                    # Remove quotation marks from title and description
                    title = title.strip('"\'')
                    description = description.strip('"\'')

                    pins.append({
                        'Title': title,
                        'Description': description,
                        'Keywords': keywords
                    })
        except Exception as e:
            print(f"Error parsing line: {line}, Error: {str(e)}")

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

    # Email body
    body = f"""
    Hello,

    Your Pinterest pin generation process has completed successfully.
    The CSV file with the generated pins is attached.

    Time of completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    msg.attach(MIMEText(body, 'plain'))

    # Attach CSV - ensure it's bytes
    if isinstance(csv_data, StringIO):
        attachment_data = csv_data.getvalue().encode('utf-8')
    else:
        attachment_data = csv_data.getvalue()

    csv_attachment = MIMEApplication(attachment_data)
    csv_attachment['Content-Disposition'] = 'attachment; filename="pinterest_pins.csv"'
    msg.attach(csv_attachment)

    # Send email
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
    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')  # Remove leading/trailing hyphens
    slug = slug[:100]  # Limit length
    return slug

def extract_topic_from_url(url):
    """Extract topic from URL for image generation prompt"""
    # Extract path from URL
    path = url.split('/')

    # Find the part that's likely the article title
    article_segment = None
    for segment in path:
        if segment and segment not in ['http:', 'https:', '', 'www', 'com', 'org', 'net']:
            if '.' not in segment and segment not in ['utm_source', 'utm_campaign', 'utm_medium', 'utm_term']:
                article_segment = segment
                break

    if article_segment:
        # Convert hyphens to spaces and clean up
        topic = article_segment.replace('-', ' ').replace('_', ' ').title()
        return topic

    # Fallback
    return "Home Decor"

def get_domain_from_url(url):
    """Extract domain from URL for organization"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. prefix if present
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
    slug = create_slug(title)[:40]  # Limit length
    
    # Create directory structure: pins/domain/board_name/
    target_dir = os.path.join(PINS_DIR, domain, board_name)
    ensure_directory_exists(target_dir)
    
    # Define target path
    file_ext = os.path.splitext(source_path)[1]
    target_path = os.path.join(target_dir, f"{slug}{file_ext}")
    
    # Copy the file
    shutil.copy2(source_path, target_path)
    return target_path

def extract_keywords_for_extra_field(keywords_str):
    """Extract keywords for the extra 'Keywords' column"""
    # Split the keywords by commas
    keywords_list = [k.strip() for k in keywords_str.split(',')]
    
    # Join with commas and return
    return ', '.join(keywords_list)

def save_progress(run_id, processed_urls, remaining_urls, csv_output):
    """Save processing progress to allow resuming after interruptions"""
    progress_file = os.path.join(DATA_DIR, f"progress_{run_id}.json")
    
    # Seek to start of CSV output to get full content
    if csv_output:
        csv_output.seek(0)
        csv_content = csv_output.getvalue()
    else:
        csv_content = ""
    
    progress_data = {
        "run_id": run_id,
        "processed_urls": processed_urls,
        "remaining_urls": remaining_urls,
        "timestamp": datetime.now().isoformat(),
        "csv_content": csv_content
    }
    
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)
    
    print(f"Progress saved to {progress_file}")
    return progress_file

def check_for_saved_progress():
    """Check for any saved progress files from interrupted runs"""
    progress_files = [f for f in os.listdir(DATA_DIR) if f.startswith("progress_") and f.endswith(".json")]
    
    if not progress_files:
        return None
    
    # Find the newest progress file
    newest_file = max(progress_files, key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)))
    progress_path = os.path.join(DATA_DIR, newest_file)
    
    # Load the progress data
    with open(progress_path, 'r') as f:
        progress_data = json.load(f)
    
    # Check if the progress file is recent (within the last 24 hours)
    progress_time = datetime.fromisoformat(progress_data["timestamp"])
    time_diff = datetime.now() - progress_time
    if time_diff.total_seconds() > 86400:  # 24 hours in seconds
        print(f"Found progress file {newest_file} but it's too old ({time_diff.total_seconds()/3600:.1f} hours)")
        return None
    
    print(f"Found recent progress file {newest_file} from {progress_time}")
    return progress_data

def main():
    print("Pinterest Pin Maker - GitHub Actions Version")
    print("------------------------------------------")
    
    # Create run ID for this batch
    run_id = create_run_id()
    
    # Ensure required directories exist
    ensure_directory_exists(PINS_DIR)
    ensure_directory_exists(DATA_DIR)
    
    # Ensure required files exist
    ensure_file_exists(URLS_FILE)
    
    # Check for saved progress from interrupted runs
    progress_data = check_for_saved_progress()
    csv_output = None
    
    if progress_data and os.environ.get("ENABLE_RESUME", "true").lower() == "true":
        print("Resuming from previous run...")
        # Restore state from saved progress
        run_id = progress_data["run_id"]
        batch_urls = progress_data["processed_urls"]  # URLs that were being processed
        remaining_urls = progress_data["remaining_urls"]
        
        # Restore CSV output
        csv_output = StringIO(progress_data["csv_content"])
        
        print(f"Resumed run ID: {run_id}")
        print(f"Resuming processing of {len(batch_urls)} URLs")
    else:
        # Normal startup without resuming
        # Read URLs 
        all_urls = read_urls(URLS_FILE)
        
        if not all_urls:
            print("No URLs found to process.")
            return
        
        # Take the next batch of URLs
        batch_urls = all_urls[:BATCH_SIZE]
        remaining_urls = all_urls[BATCH_SIZE:]
    
    print(f"Processing batch of {len(batch_urls)} URLs")
    print(f"Using {len(api_keys)} Gemini API keys for load balancing")
    
    # Create CSV file for this batch
    batch_csv_path = os.path.join(DATA_DIR, f"pinterest_pins_{run_id}.csv")
    
    # Initialize CSV output with the exact column order requested
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Thumbnail', 'Link', 'Publish date', 'Description', 'Keywords', ''])

    # Storage for generated images
    generated_images = []

    # Cache for board names to reduce API calls
    board_cache = {}
    
    # Track API usage for load balancing
    api_usage_count = {key: 0 for key in api_keys}

    # Process each URL in the batch
    for i, url in enumerate(batch_urls):
        print(f"\nProcessing URL {i+1}/{len(batch_urls)}: {url}")
        domain_name = get_domain_from_url(url)

        try:
            # Generate pin content
            print("Generating pin content with Gemma model...")
            csv_content = generate_pin_content(url, PINS_PER_URL)

            if csv_content.startswith("Error"):
                print(f"Error generating pin content: {csv_content}")
                continue

            # Parse the generated content
            pins = parse_csv_content(csv_content)
            print(f"Generated {len(pins)} pin ideas")

            # Extract topic from URL
            topic = extract_topic_from_url(url)
            print(f"Extracted topic: {topic}")

            # Create images and upload to Cloudinary for each pin
            for j, pin in enumerate(pins):
                print(f"Creating image {j+1}/{len(pins)}...")

                # Generate image prompt based on pin title and URL topic
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

                # Generate image with Gemini - distribute among API keys
                file_name = f"pin_{i+1}_{j+1}"
                image_url = None
                repo_image_path = None

                try:
                    # Use a different API key for each image to distribute load
                    key_manager.get_random_client()
                    image_data, image_mime_type, image_file_path = generate_image_with_gemini(image_prompt, file_name)

                    if image_file_path and os.path.exists(image_file_path):
                        # Generate board name first (needed for repository path)
                        cache_key = pin['Title'][:15].lower()  # Use first part of title as cache key
                        if cache_key in board_cache:
                            board_name = board_cache[cache_key]
                            print(f"Using cached board name: {board_name}")
                        else:
                            print("Generating board name with Gemma model...")
                            board_name = generate_board_category(pin['Title'], pin['Keywords'])
                            board_cache[cache_key] = board_name
                            print(f"Generated board name: {board_name}")
                        
                        # Copy image to repository structure
                        repo_image_path = copy_image_to_repo(image_file_path, url, board_name, pin['Title'])
                        print(f"Copied image to repository: {repo_image_path}")
                        
                        # Upload to Cloudinary
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
                    # Use a placeholder image URL if image generation fails
                    image_url = "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg"
                    board_name = "home-inspiration"  # Default fallback

                # Generate a unique UTM campaign parameter based on pin title
                utm_campaign = create_slug(pin['Title'])[:20]  # Limit length for URL compatibility

                # Create the tracked URL with UTM parameters
                tracked_url = url
                if '?' in tracked_url:
                    tracked_url += f"&utm_source=pinterest&utm_campaign={utm_campaign}"
                else:
                    tracked_url += f"?utm_source=pinterest&utm_campaign={utm_campaign}"

                # Extract keywords for the extra field
                extra_keywords = extract_keywords_for_extra_field(pin['Keywords'])
                
                # Add to CSV with the exact column order requested
                csv_writer.writerow([
                    pin['Title'],                        # Title
                    image_url if image_url else "https://res.cloudinary.com/dbcpfy04c/image/upload/v1618237451/placeholder.jpg", # Media URL
                    board_name,                          # Pinterest board
                    '',                                  # Thumbnail (empty)
                    tracked_url,                         # Link (with UTM parameters)
                    datetime.now().strftime('%Y-%m-%d'), # Publish date
                    pin['Description'],                  # Description
                    pin['Keywords'],                     # Keywords
                    extra_keywords                       # Extra column for additional keywords
                ])

                # Add a small delay to prevent rate limiting
                time.sleep(2)

        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            # Keep the URL in the list if there was an error
            remaining_urls.append(url)

    # Save CSV file to repository
    with open(batch_csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(csv_output.getvalue())
    
    # Create CSV file for all pins (append to existing or create new)
    all_pins_csv_path = os.path.join(DATA_DIR, "all_pinterest_pins.csv")
    if os.path.exists(all_pins_csv_path):
        # Read existing data
        existing_df = pd.read_csv(all_pins_csv_path)
        # Read new data
        csv_output.seek(0)
        new_df = pd.read_csv(csv_output)
        # Combine and save
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(all_pins_csv_path, index=False)
    else:
        # Just save current batch as all pins
        csv_output.seek(0)
        with open(all_pins_csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_output.getvalue())
    
    # Create zip archive of all generated images
    if generated_images:
        timestamp = int(time.time())
        zip_filename = f"pinterest_images_{timestamp}.zip"

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for image in generated_images:
                if os.path.exists(image['file_path']):
                    zipf.write(image['file_path'])

        print(f"\nImages zipped to {zip_filename}")

    # Write remaining URLs back to file
    write_urls(URLS_FILE, remaining_urls)
    
    # Send email notification
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
    
    # Set output for GitHub Actions
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f"processed_urls={len(batch_urls)}\n")
        f.write(f"remaining_urls={len(remaining_urls)}\n")

if __name__ == "__main__":
    main()