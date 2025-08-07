import os
from PIL import Image

def split_image_horizontally(image_path, output_dir):
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Calculate the midpoint for horizontal split
        midpoint = width // 2
        
        # Define the bounding boxes for the two halves
        left_half_box = (0, 230, midpoint, height)
        right_half_box = (midpoint, 230, width, height)
        
        # Crop the image into two halves
        left_half = img.crop(left_half_box)
        right_half = img.crop(right_half_box)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get original filename and extension
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        
        # Save the two halves
        left_half_path = os.path.join(output_dir, f"{name}_part1{ext}")
        right_half_path = os.path.join(output_dir, f"{name}_part2{ext}")
        
        left_half.save(left_half_path)
        right_half.save(right_half_path)
        
        print(f"Successfully split '{base_name}' into '{os.path.basename(left_half_path)}' and '{os.path.basename(right_half_path)}'")
        return True
    except Exception as e:
        print(f"Error processing '{image_path}': {e}")
        return False

def process_images_in_directory(input_dir, output_dir):
    if not os.path.exists(input_dir):
        print(f"Input directory '{input_dir}' does not exist.")
        return

    print(f"Processing images from '{input_dir}'...")
    processed_count = 0
    failed_count = 0

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path):
            # Check if it's a common image file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                if split_image_horizontally(file_path, output_dir):
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

    parser = argparse.ArgumentParser(description="Horizontally split image files into two halves.")
    parser.add_argument("-i", "--input_directory", required=True, help="Path to the directory containing the original image files.")
    parser.add_argument("-o", "--output_directory", required=True, help="Path to the directory where the split image files will be saved.")
    
    args = parser.parse_args()
    
    process_images_in_directory(args.input_directory, args.output_directory)