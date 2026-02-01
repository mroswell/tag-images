import os
import csv
import time
from google import genai
from PIL import Image

# Initialize
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def main():
    image_dir = "kapok_tree_images"
    output_file = "artwork_descriptions_gemini.csv"
    
    # Get files
    images = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['filename', 'description', 'tags'])
        writer.writeheader()
        
        for file in images:
            print(f"Working on {file}...")
            path = os.path.join(image_dir, file)
            
            try:
                # 10-second sleep is the 'Magic Number' for Free Tier stability
                time.sleep(10) 
                
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=["Describe this artwork in 3 sentences. List 5 tags.", Image.open(path)]
                )
                
                # Simple storage
                writer.writerow({
                    'filename': file,
                    'description': response.text.replace('\n', ' ').strip(),
                    'tags': 'check_description_text'
                })
                csvfile.flush()
                print("Success!")
                
            except Exception as e:
                print(f"Error on {file}: {e}")

    print("Done. Check your CSV.")

if __name__ == "__main__":
    main()
