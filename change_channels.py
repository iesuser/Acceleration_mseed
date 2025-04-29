import os
from obspy import read

# Get the folder where the script is running
folder_path = os.path.dirname(os.path.abspath(__file__))

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Only process files (ignore folders)
    if os.path.isfile(file_path):
        try:
            # Try reading the file
            st = read(file_path)
            
            # Change 'HHE' channel to 'HNE'
            for tr in st:
                if tr.stats.channel == "HHE":
                    tr.stats.channel = "HNE"
            
            # Overwrite the file with the updated stream
            st.write(file_path, format="MSEED")
            print(f"Modified: {filename}")
        
        except Exception as e:
            print(f"Skipped: {filename} ({e})")

print("Done!")
