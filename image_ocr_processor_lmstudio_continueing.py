import os
import base64
from PIL import Image
import pytesseract
import requests
import argparse
from tqdm import tqdm
def read_initial_response_from_file(image_path):
    """Read initial LMStudio response from corresponding text file"""
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    lmstudio_output_file = f"{base_name}_lmstudio.txt"
    try:
        with open(lmstudio_output_file, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return None

def read_tesseract_response_from_file(image_path):
    """Read Tesseract response from corresponding text file"""
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    tesseract_output_file = f"{base_name}_tesseract.txt"
    try:
        with open(tesseract_output_file, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return None

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

def process_image_with_lmstudio(image_path, tesseract_text, initial_response):
    """Process image using LMStudio OpenAI-compatible API with LLaVA model.
    If initial responses are available in files, use them instead of making live API calls."""

    # tesseract_text = read_tesseract_response_from_file(image_path) or tesseract_text

    if initial_response is None:
        print(f"No initial response found for {image_path}. Processing with new text generation.")
        # If no file-based response, proceed with live API call
        # Encode the image to base64
        encoded_image = encode_image(image_path)

        # Prepare the initial request payload for OpenAI-compatible API
        payload = {
            "model": "gemma-3-27b-it-k-latest",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "OCR text in this image. dont translate. dont add any extra text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            "stream": False
        }

        try:
            # Send initial request to LMStudio API (OpenAI-compatible endpoint)
            response = requests.post('http://localhost:1234/v1/chat/completions', json=payload)
            response.raise_for_status()

            # Extract the initial response text from JSON
            result = response.json()
            initial_response = result['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            return f"Error processing image with LMStudio: {str(e)}"
        except KeyError as e:
            return f"Error parsing LMStudio response: {str(e)}"

    # Prepare follow-up message to refine results with Tesseract comparison
    encoded_image = encode_image(image_path)
    follow_up_payload = {
        "model": "gemma-3-27b-it-k-latest",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "OCR text in this image. dont translate. dont add any extra text."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            },
            {
                "role": "assistant",
                "content": initial_response
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Combine your OCR results with this Tesseract output and refine your response: {tesseract_text}"
                    }
                ]
            }
        ],
        "stream": False
    }

    try:
        # Send follow-up request to LMStudio API
        follow_up_response = requests.post('http://localhost:1234/v1/chat/completions', json=follow_up_payload)
        follow_up_response.raise_for_status()

        # Extract the refined response text from JSON
        follow_up_result = follow_up_response.json()
        return follow_up_result['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        return f"Error processing image with LMStudio: {str(e)}"
    except KeyError as e:
        return f"Error parsing LMStudio response: {str(e)}"

def main(folder_path, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # List all image files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]

    # Collect all results for aggregation
    all_tesseract_results = []
    all_lmstudio_results = []

    # Process files with progress bar
    for image_file in tqdm(image_files, desc="Processing images"):
        image_path = os.path.join(folder_path, image_file)

        # Generate output file names (same as image name but .txt extension)
        base_name = os.path.splitext(image_file)[0]
        tesseract_output_file = os.path.join(output_folder, f"{base_name}_tesseract.txt")
        lmstudio_output_file = os.path.join(output_folder, f"{base_name}_lmstudio.txt")
        lmstudio_new_output_file = os.path.join(output_folder, f"{base_name}_lmstudio_modified.txt")

        # Check if we already have saved responses
        has_saved_responses = (
            os.path.exists(tesseract_output_file) and
            os.path.exists(lmstudio_output_file)
        )

        if has_saved_responses:
            print("previous response found, continuing from ...")
            # Read existing results from files
            with open(tesseract_output_file, 'r') as tes_file:
                tesseract_text = tes_file.read()

            with open(lmstudio_output_file, 'r') as lmstudio_file:
                lmstudio_text = lmstudio_file.read()

            # Process with LMStudio (will use file-based responses if available)
            lmstudio_text = process_image_with_lmstudio(image_path, tesseract_text, lmstudio_text)


            with open(lmstudio_new_output_file, 'w') as lmstudio_new_file:
                lmstudio_new_file.write(lmstudio_text)
                all_lmstudio_results.append(f"--- {image_file} ---\n{lmstudio_text}\n")
        else:
            print("no saved responses for", image_file)


    with open(os.path.join(output_folder, "all_lmstudio_modified_results.txt"), 'w') as agg_file:
        agg_file.write('\n'.join(all_lmstudio_results))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process images and save OCR results')
    parser.add_argument('-i', '--input', required=True, help='Path to the folder containing images')
    parser.add_argument('-o', '--output', required=True, help='Output folder path for text files')

    args = parser.parse_args()

    main(args.input, args.output)
