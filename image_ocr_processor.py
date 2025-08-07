import os
import base64
from PIL import Image
import pytesseract
import requests
import argparse
from tqdm import tqdm

def process_image_with_tesseract(image_path):
    # Load the image
    image = Image.open(image_path)
    # Perform OCR using Tesseract
    text = pytesseract.image_to_string(image, 'fas2')
    return text

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_with_ollama(image_path, prim_ocr_txt):
    """Process image using Ollama chat API with LLaVA model"""
    # Encode the image to base64
    encoded_image = encode_image(image_path)
    
    # Prepare the request payload
    payload = {
        "model": "Gemma3-27b-q5-vision:latest",
        "role": "user",
        "prompt": f"OCR text in this image. dont translate. this is the OCR of the image created by tesseract (use it for improving the results):\n\n {prim_ocr_txt}",
        "images": [encoded_image],
        "stream": False
    }   
    try:
        # Send request to Ollama API
        response = requests.post('http://localhost:11434/api/generate', json=payload)
        response.raise_for_status()
        
        # Extract the response text from JSON
        result = response.json()
        return result.get('response', '')
    except requests.exceptions.RequestException as e:
        return f"Error processing image with Ollama: {str(e)}"
    except KeyError as e:
        return f"Error parsing Ollama response: {str(e)}"

def main(folder_path, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # List all image files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    # Collect all results for aggregation
    all_tesseract_results = []
    all_ollama_results = []
    
    # Process files with progress bar
    for image_file in tqdm(image_files, desc="Processing images"):
        image_path = os.path.join(folder_path, image_file)
        
        # Process with Tesseract
        tesseract_text = process_image_with_tesseract(image_path)
        
        # Process with Ollama
        ollama_text = process_image_with_ollama(image_path, tesseract_text)
        
        # Generate output file names (same as image name but .txt extension)
        base_name = os.path.splitext(image_file)[0]
        tesseract_output_file = os.path.join(output_folder, f"{base_name}_tesseract.txt")
        ollama_output_file = os.path.join(output_folder, f"{base_name}_ollama.txt")
        
        # Save results to individual text files
        with open(tesseract_output_file, 'w') as tes_file:
            tes_file.write(tesseract_text)
            
        with open(ollama_output_file, 'w') as ollama_file:
            ollama_file.write(ollama_text)
        
        # Collect results for aggregation
        all_tesseract_results.append(f"--- {image_file} ---\n{tesseract_text}\n")
        all_ollama_results.append(f"--- {image_file} ---\n{ollama_text}\n")
    
    # Save aggregated results
    with open(os.path.join(output_folder, "all_tesseract_results.txt"), 'w') as agg_file:
        agg_file.write('\n'.join(all_tesseract_results))
        
    with open(os.path.join(output_folder, "all_ollama_results.txt"), 'w') as agg_file:
        agg_file.write('\n'.join(all_ollama_results))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process images and save OCR results')
    parser.add_argument('-i', '--input',required=True, help='Path to the folder containing images')
    parser.add_argument('-o', '--output', required=True, help='Output folder path for text files')
    
    args = parser.parse_args()
    
    main(args.input, args.output)