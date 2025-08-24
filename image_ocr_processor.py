import os
import base64
from PIL import Image
import pytesseract
import requests
import argparse
from tqdm import tqdm
import time

def post_with_retry(url, json_payload, retries=3, timeout=180):
    """
    Sends a POST request with a timeout and retry mechanism.
    
    Args:
        url (str): The URL to send the request to.
        json_payload (dict): The JSON payload for the request.
        retries (int): The total number of attempts to make.
        timeout (int): The timeout in seconds for each request.
        
    Returns:
        requests.Response or None: The response object on success, or None on failure.
    """
    for attempt in range(retries):
        try:
            response = requests.post(url, json=json_payload, timeout=timeout)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response  # Success
        except requests.exceptions.Timeout:
            tqdm.write(f"Request timed out (attempt {attempt + 1}/{retries}). Retrying in 5 seconds...")
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            tqdm.write(f"Request failed: {e} (attempt {attempt + 1}/{retries}). Retrying in 5 seconds...")
            time.sleep(5)
            
    tqdm.write("All retry attempts failed.")
    return None

def process_image_with_tesseract(image_path):
    """Perform OCR using Tesseract"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, 'fas')  # Language set to Farsi ('fas')
        return text
    except Exception as e:
        return f"Error processing with Tesseract: {str(e)}"

def encode_image(image_path):
    """Encode image to a base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_with_ollama(image_path, tesseract_text, use_two_step=False):
    """
    Process an image using the native Ollama API.
    
    Returns:
        tuple: A tuple containing (initial_response, final_response).
    """
    encoded_image = encode_image(image_path)
    
    ollama_endpoint = 'http://localhost:11434/api/chat'
    model_name = "gemma3:27b-it-q8_0"  # Ensure this multimodal model is available

    initial_messages = [
        {
            "role": "user",
            "content": "OCR text in this image. dont translate. dont add any extra text.",
            "images": [encoded_image]
        }
    ]

    initial_payload = { "model": model_name, "messages": initial_messages, "stream": False }

    try:
        # Initial request with retry
        response = post_with_retry(ollama_endpoint, json_payload=initial_payload)
        if response is None:
            raise requests.exceptions.RequestException("Initial request failed after multiple retries.")
        
        result = response.json()
        initial_response_content = result['message']['content']

        if not use_two_step:
            return initial_response_content, None

        # Two-Step Refinement Process
        follow_up_messages = [
            *initial_messages,
            { "role": "assistant", "content": initial_response_content },
            { "role": "user", "content": f"Combine your OCR results with this Tesseract output and refine your response: {tesseract_text}" }
        ]
        
        follow_up_payload = { "model": model_name, "messages": follow_up_messages, "stream": False }
        
        # Follow-up request with retry
        follow_up_response = post_with_retry(ollama_endpoint, json_payload=follow_up_payload)
        if follow_up_response is None:
            raise requests.exceptions.RequestException("Follow-up request failed after multiple retries.")

        final_response_content = follow_up_response.json()['message']['content']
        return initial_response_content, final_response_content

    except requests.exceptions.RequestException as e:
        error_message = f"Error communicating with Ollama: {str(e)}"
        return error_message, None
    except KeyError as e:
        error_message = f"Error parsing Ollama response: {str(e)}."
        return error_message, None

def main(folder_path, output_folder, use_two_step):
    """Main function to process all images in a folder with resume capability."""
    os.makedirs(output_folder, exist_ok=True)

    image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    for image_file in tqdm(image_files, desc="Processing images") as pbar:
        base_name = os.path.splitext(image_file)[0]
        image_path = os.path.join(folder_path, image_file)
        
        # Resume Capability
        final_ollama_output_path = os.path.join(output_folder, f"{base_name}_ollama.txt")
        if os.path.exists(final_ollama_output_path):
            tqdm.write(f"Skipping '{image_file}' as it has already been processed.")
            continue

        # Processing
        tesseract_text = process_image_with_tesseract(image_path)
        ollama_initial, ollama_final = process_image_with_ollama(image_path, tesseract_text, use_two_step)
        
        final_ollama_text = ollama_final if use_two_step and ollama_final is not None else ollama_initial
        
        # Saving Individual Files
        tesseract_output_file = os.path.join(output_folder, f"{base_name}_tesseract.txt")
        with open(tesseract_output_file, 'w', encoding='utf-8') as tes_file:
            tes_file.write(tesseract_text)
        
        # If in two-step mode, save the intermediate AI response
        if use_two_step:
            intermediate_output_file = os.path.join(output_folder, f"{base_name}_ollama_intermediate.txt")
            with open(intermediate_output_file, 'w', encoding='utf-8') as inter_file:
                inter_file.write(ollama_initial or "")

        with open(final_ollama_output_path, 'w', encoding='utf-8') as ollama_file:
            ollama_file.write(final_ollama_text or "")
        
    # Aggregation Step
    tqdm.write("\nJob complete. Aggregating all results...")
    all_ollama_content = []
    all_tesseract_content = []

    # Re-read all individual files to create a complete aggregation.
    for image_file in tqdm(image_files, desc="Aggregating files"):
        base_name = os.path.splitext(image_file)[0]
        header = f"--- {image_file} ---\n"
        
        ollama_file_path = os.path.join(output_folder, f"{base_name}_ollama.txt")
        if os.path.exists(ollama_file_path):
            with open(ollama_file_path, 'r', encoding='utf-8') as f:
                all_ollama_content.append(header + f.read() + "\n")
        
        tesseract_file_path = os.path.join(output_folder, f"{base_name}_tesseract.txt")
        if os.path.exists(tesseract_file_path):
            with open(tesseract_file_path, 'r', encoding='utf-8') as f:
                all_tesseract_content.append(header + f.read() + "\n")

    with open(os.path.join(output_folder, "all_ollama_results.txt"), 'w', encoding='utf-8') as agg_file:
        agg_file.write('\n'.join(all_ollama_content))

    with open(os.path.join(output_folder, "all_tesseract_results.txt"), 'w', encoding='uf-8') as agg_file:
        agg_file.write('\n'.join(all_tesseract_content))
    
    tqdm.write("Aggregation complete. All files are up-to-date.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a folder of images with Tesseract and Ollama for OCR with resume capability.')
    parser.add_argument('-i', '--input', required=True, help='Path to the folder containing images.')
    parser.add_argument('-o', '--output', required=True, help='Path to the folder where text files will be saved.')
    parser.add_argument('--two-step', action='store_true', help='Enable two-step AI refinement using Tesseract output. This will also save the intermediate AI response.')

    args = parser.parse_args()
    main(args.input, args.output, args.two_step)