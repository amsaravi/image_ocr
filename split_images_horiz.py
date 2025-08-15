import os
from PIL import Image

def split_image_vertically_with_overlap(image_path, output_dir, overlap=20):
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate midpoint for vertical (top/bottom) split
        midpoint = height // 2
        
        # Add overlap
        top_half_box = (0, 0, width, midpoint + overlap)
        bottom_half_box = (0, midpoint - overlap, width, height)
        
        # Crop the image into two halves
        top_half = img.crop(top_half_box)
        bottom_half = img.crop(bottom_half_box)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get original filename and extension
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        
        # Save the two halves
        top_half_path = os.path.join(output_dir, f"{name}_part1{ext}")
        bottom_half_path = os.path.join(output_dir, f"{name}_part2{ext}")
        
        top_half.save(top_half_path)
        bottom_half.save(bottom_half_path)
        
        print(f"Successfully split '{base_name}' into '{os.path.basename(top_half_path)}' and '{os.path.basename(bottom_half_path)}'")
        return True
    except Exception as e:
        print(f"Error processing '{image_path}': {e}")
        return False

def process_images_in_directory(input_dir, output_dir, overlap=20):
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist.")
        return

    print(f"Processing images from '{input_dir}'...")
    processed_count = 0
    failed_count = 0

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                if split_image_vertically_with_overlap(file_path, output_dir, overlap):
                    processed_count += 1
                else:
                    failed_count += 1
            else:
                print(f"Skipping non-image file: '{filename}'")
        else:
            print(f"Skipping directory: '{filename}'")
    
    print(f"\nProcessing complete.")
    print(f"Total images processed: {processed_count}")
    print(f"Total images failed: {failed_count}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vertically split images (top/bottom) with overlap.")
    parser.add_argument("-i", "--input_directory", required=True, help="Path to the directory containing the original image files.")
    parser.add_argument("-o", "--output_directory", required=True, help="Path to the directory where the split image files will be saved.")
    parser.add_argument("--overlap", type=int, default=20, help="Pixel overlap between the two halves (default: 20).")
    
    args = parser.parse_args()
    
    process_images_in_directory(args.input_directory, args.output_directory, args.overlap)
