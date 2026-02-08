import os
import csv
import requests
import json
from PIL import Image
import base64
from tqdm.notebook import tqdm

# Define the directory containing the PNG images
IMAGE_DIR = "kapok_tree_images"  # Change this to your directory path

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to get image orientation (portrait or landscape)
def get_orientation(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        if width > height:
            return "landscape"
        else:
            return "portrait"

# Function to analyze image using Claude API
def analyze_image_claude(image_path):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Add more detailed error handling
    print(f"Processing: {os.path.basename(image_path)}")
    
    base64_image = encode_image(image_path)
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Get the correct media type based on file extension
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext == '.png':
        media_type = "image/png"
    elif file_ext in ['.jpg', '.jpeg']:
        media_type = "image/jpeg"
    else:
        media_type = "image/jpeg"  # Default to JPEG
    
    payload = {
        "model": "claude-opus-4-20250514", 
        "max_tokens": 1000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a hand-drawn artwork. (Don't worry about spaces, they will be a place for text when it becomes a book.) Please provide: \n1. A short description (1-2 sentences)\n2. A detailed description (4-5 sentences)\n3. A comma-separated list of tags for this image"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract the content from response
        content = result['content'][0]['text']
        
        # Parse the response to extract descriptions and tags
        lines = content.strip().split('\n')
        short_desc = ""
        long_desc = ""
        tags = ""
        
        section = 0
        for line in lines:
            if "1." in line[:3] or "Short description:" in line:
                section = 1
                short_desc = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
            elif "2." in line[:3] or "Detailed description:" in line:
                section = 2
                long_desc = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
            elif "3." in line[:3] or "Tags:" in line:
                section = 3
                tags = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
            elif section == 1 and not short_desc:
                short_desc = line.strip()
            elif section == 2 and not long_desc:
                long_desc = line.strip()
            elif section == 2 and long_desc:
                long_desc += " " + line.strip()
            elif section == 3 and not tags:
                tags = line.strip()
        
        return {
            "short_description": short_desc,
            "long_description": long_desc,
            "tags": tags
        }
    
    except requests.exceptions.HTTPError as e:
        response_text = e.response.text if hasattr(e, 'response') and hasattr(e.response, 'text') else "No response text"
        print(f"Error analyzing image: {e}")
        print(f"Response details: {response_text}")
        return {
            "short_description": "Error analyzing image",
            "long_description": f"There was an error analyzing this image with the API: {e}",
            "tags": "error, failed_analysis"
        }
    except Exception as e:
        print(f"Unexpected error analyzing image: {e}")
        return {
            "short_description": "Error analyzing image",
            "long_description": "There was an error analyzing this image with the API.",
            "tags": "error, failed_analysis"
        }

# Main function to process all images and create CSV
def process_images():
    # Ensure the directory exists
    if not os.path.exists(IMAGE_DIR):
        print(f"Directory {IMAGE_DIR} does not exist!")
        return
    
    # Get all JPG files (changed from JPG)
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    
    if not image_files:
        print(f"No  images found in {IMAGE_DIR}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    # Create CSV file
    csv_filename = "scratch/artwork_descriptions_claude.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'short_description', 'long_description', 'tags', 'orientation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each image
        for img_file in tqdm(image_files, desc="Processing images"):
            img_path = os.path.join(IMAGE_DIR, img_file)
            
            # Get image orientation
            orientation = get_orientation(img_path)
            
            # Analyze image with Claude API
            analysis = analyze_image_claude(img_path)
            
            # Write to CSV
            writer.writerow({
                'filename': img_file,
                'short_description': analysis['short_description'],
                'long_description': analysis['long_description'],
                'tags': analysis['tags'],
                'orientation': orientation
            })
    
    print(f"Analysis complete! Results saved to {csv_filename}")

# Run the function - uncommented to execute
process_images()
