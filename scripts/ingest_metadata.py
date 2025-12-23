"""Script to ingest CSV metadata into SQLite for faster lookups."""

import os
import csv
import sys
from fccs_agent.config import load_config
from fccs_agent.services.cache_service import init_cache_service, get_cache_service

def get_reader_and_file(file_path):
    """Try to get a CSV reader and its file handle with the correct encoding."""
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'utf-16']
    
    for encoding in encodings:
        f = None
        try:
            f = open(file_path, mode='r', encoding=encoding)
            sample = f.read(1024)
            if not sample:
                f.close()
                continue
            
            # Try to detect delimiter
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            return csv.DictReader(f, dialect=dialect), encoding, f
        except Exception:
            if f:
                f.close()
            continue
            
    # Fallback to comma and utf-8 if sniffer fails
    f = open(file_path, mode='r', encoding='utf-8-sig')
    return csv.DictReader(f), 'utf-8-sig (fallback)', f

def ingest_csv_metadata(data_dir: str):
    """Load metadata from data directory into SQLite."""
    config = load_config()
    db_url = config.database_url
    
    print(f"Initializing CacheService with {db_url}...")
    cache = init_cache_service(db_url)
    
    # Files to process
    metadata_files = {
        "Account": "Ravi_ExportedMetadata_Account.csv",
        "Entity": "Ravi_ExportedMetadata_Entity.csv",
        "Movement": "Ravi_ExportedMetadata_Movement.csv",
        "Data Source": "Ravi_ExportedMetadata_Data Source.csv"
    }
    
    total_count = 0
    
    for dimension, filename in metadata_files.items():
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Skipping {dimension}: File not found at {file_path}")
            continue
            
        print(f"Processing {dimension} from {filename}...")
        count = 0
        f_handle = None
        
        try:
            reader, used_encoding, f_handle = get_reader_and_file(file_path)
            print(f"  Detected encoding: {used_encoding}")
            
            for row in reader:
                # Clean up keys (sometimes sniffer leaves whitespace)
                row = {k.strip() if k else k: v for k, v in row.items()}
                
                # Member identification
                member_name = (
                    row.get('Member') or 
                    row.get(dimension) or 
                    row.get('Account') or 
                    row.get('Entity') or
                    row.get('Movement') or
                    row.get('Data Source')
                )
                
                if not member_name:
                    # Try the first column value
                    keys = list(row.keys())
                    if keys:
                        member_name = row.get(keys[0])
                
                if member_name:
                    member_name = member_name.strip()
                    cache.update_member(dimension, member_name, row)
                    count += 1
            
            print(f"  Loaded {count} members for {dimension}.")
            total_count += count
        except Exception as e:
            print(f"  Error processing {dimension}: {e}")
        finally:
            if f_handle:
                f_handle.close()
            
    print(f"\nTotal metadata entries loaded: {total_count}")

if __name__ == "__main__":
    # Path to data directory relative to project root
    data_dir = os.path.join(os.getcwd(), "data")
    ingest_csv_metadata(data_dir)

