import base64

def file_to_base64(file_path):
    """Convert a file (image or font) to a base64 string."""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def main():
    # List of file paths (images and font) and their intended variable names
    files = {
        'images/delta_local_record_bg.png': 'delta_local_record_bg_img_base64',
        'images/delta_world_record_bg.png': 'delta_world_record_bg_img_base64',
        'images/bestlap_bg.png': 'bestlap_bg_img_base64',
        'images/wheel_bg.png': 'wheel_bg_img_base64',
        'images/pedal_bg.png': 'pedal_bg_img_base64',
        'images/pedal_raw_bg.png': 'pedal_raw_bg_img_base64',
        'images/lap_bg.png': 'lap_bg_img_base64',
        'images/pos_bg.png': 'pos_bg_img_base64',
        'images/laptime_bg.png': 'laptime_bg_img_base64',
        'images/speedometer_bg.png': 'speedometer_bg_img_base64',
        'images/tachometer_bg.png': 'tachometer_bg_img_base64',
        'images/needle_bg.png': 'needle_bg_img_base64',
        'images/Race_results_Background.png': 'Race_results_Background_img_base64',
        'images/Race_scores_Background.png': 'Race_scores_Background_img_base64',
        'images/LiveRace_LiveView.jpg': 'liverace_liveview_img_base64',
        'images/High_scores_Background.png': 'High_scores_Background_img_base64',
        'images/LiveRace_Status.jpg': 'liverace_status_img_base64',
        'images/Driver_Statistics_Background.png': 'Driver_Statistics_Background_img_base64',
        'RockyTM.ico': 'icon_base64',
        'fonts/sui generis rg.ttf': 'sui_generis_rg_font_base64',
        'fonts/DS-DIGIB.TTF': 'ds_digib_font_base64',
           # Added font file
    }

    # Base path to your file directory
    base_path = 'C:/Users/DrmRacing/Documents/GitHub/AMS2_RaceScore/'

    # File to save the base64 strings
    output_file = 'file_base64_strings.py'

    with open(output_file, 'w') as f:
        for file_name, var_name in files.items():
            file_path = base_path + file_name
            base64_string = file_to_base64(file_path)
            f.write(f"{var_name} = \"{base64_string}\"\n\n")

    print(f"Base64 strings saved to {output_file}")

if __name__ == "__main__":
    main()
