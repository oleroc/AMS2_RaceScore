import base64
import os

def file_to_base64(file_path):
    """Convert a file (image or font) to a base64 string."""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def main():
    base_path = 'C:/Users/DrmRacing/Documents/GitHub/AMS2_RaceScore/'
    image_dir = os.path.join(base_path, 'images')
    font_dir = os.path.join(base_path, 'fonts')

    output_file = 'file_base64_strings.py'
    files = {}

    # Hent bilder og ikoner fra images/
    for file_name in os.listdir(image_dir):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.ico')):
            key = os.path.splitext(file_name)[0].replace('-', '_').replace(' ', '_').lower()
            suffix = "icon_base64" if file_name.lower().endswith('.ico') else "img_base64"
            var_name = f"{key}_{suffix}"
            files[os.path.join('images', file_name)] = var_name

    # Hent fonter fra fonts/
    for file_name in os.listdir(font_dir):
        if file_name.lower().endswith(('.ttf', '.otf')):
            key = os.path.splitext(file_name)[0].replace('-', '_').replace(' ', '_').lower()
            var_name = f"{key}_font_base64"
            files[os.path.join('fonts', file_name)] = var_name

    # Lagre base64-strenger
    with open(output_file, 'w') as f:
        for relative_path, var_name in files.items():
            file_path = os.path.join(base_path, relative_path)
            base64_string = file_to_base64(file_path)
            f.write(f"{var_name} = \"{base64_string}\"\n\n")

    print(f"Base64 strings saved to {output_file}")

if __name__ == "__main__":
    main()
