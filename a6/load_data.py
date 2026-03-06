import os
import sys
import json
from HashTableClient import HashTableClient

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 load_data.py <project_name> <data_directory>")
        sys.exit(1)

    project_name = sys.argv[1]
    data_dir = sys.argv[2]
    
    # Connect via project name (ensures we find the server even if port changed)
    client = HashTableClient.from_project_name(project_name)
    
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} not found.")
        return

    print(f"Loading files from {data_dir} into {project_name}...")

    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'r') as f:
            content = json.load(f)
        
        client.insert(str(filename), str(content))
        print(f"Inserted: {filename}")

if __name__ == "__main__":
    main()
