# app/utils/covert_csv_to_json.py

import pandas as pd
import numpy as np
import json

def convert_csv_to_json(csv_file_path, json_output_path, max_entries=None):
    """
    Converts a CSV file to JSON format using pandas DataFrame for efficient data manipulation.

    Args:
        csv_file_path (str): The path to the input CSV file containing company data.
        json_output_path (str): The path to the output JSON file where the processed data will be stored.
        max_entries (int, optional): The maximum number of entries to process from the CSV file. If None, process all entries.

    Returns:
        None: Writes the JSON output to the specified file.
    """

    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path)

        # If max_entries is set, limit the DataFrame to that number of entries
        if max_entries:
            df = df.head(max_entries)

        # Replace NaN values with None
        df = df.replace({np.nan: None})

        # Convert the DataFrame to a list of dictionaries
        records = df.to_dict(orient='records')

        # Ensure all NaN values are converted to None
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        # Write the list of dictionaries to a JSON file
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(records, json_file, ensure_ascii=False, indent=4)

        print(f"JSON file saved to {json_output_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
csv_file_path = "C:\\Users\\DevX\\specialProjects\\mAIndScout\\crunchbase_companies_data\\crunchbase_0-100k.csv"
json_output_path = "C:\\Users\\DevX\\specialProjects\\mAIndScout\\crunchbase_converted_to_json\\output.json"
convert_csv_to_json(csv_file_path, json_output_path, max_entries=10)
