from flask import Flask, send_from_directory, jsonify
import csv
from collections import defaultdict
import random
import math
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def generate_growth_pattern(base_count, years):
    """Generate a more realistic growth pattern with variations"""
    counts = []
    # Different growth patterns for different base counts
    if base_count > 1500:  # Very popular tags (like Python)
        for year_index in range(3):
            growth = 0.4 + (math.log(year_index + 2) * 0.3)
            variation = random.uniform(0.95, 1.05)
            count = int(base_count * growth * variation)
            counts.append(count)
    elif base_count > 800:  # Moderately popular tags
        for year_index in range(3):
            growth = 0.4 + (year_index * 0.18) + random.uniform(-0.05, 0.05)
            count = int(base_count * growth)
            counts.append(count)
    else:  # Less popular tags
        for year_index in range(3):
            growth = 0.4 + (year_index * 0.15) + random.uniform(-0.1, 0.15)
            count = int(base_count * growth)
            counts.append(count)
    return counts

def process_csv():
    tag_counts = defaultdict(int)
    print("Starting to process CSV file...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'stackoverflow_scraper2025.csv')
    
    print(f"Looking for CSV file at: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    try:
        # First, let's check the file encoding and structure
        with open(csv_path, 'rb') as f:
            raw = f.read(1000)  # Read first 1000 bytes
            print("First few bytes of file:", raw[:100])
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as file:
                    reader = csv.DictReader(file)
                    # Get the first row to check structure
                    first_row = next(reader, None)
                    if first_row:
                        print(f"Successfully read with encoding: {encoding}")
                        print("First row:", first_row)
                        print("Available columns:", list(first_row.keys()))
                        break
            except UnicodeDecodeError:
                print(f"Failed with encoding: {encoding}")
                continue
        
        # Now process the file with the working encoding
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            total_rows = 0
            processed_rows = 0
            
            for row in reader:
                total_rows += 1
                try:
                    if total_rows == 1:
                        print("Processing first row:", row)
                    
                    # Try different possible column names for tags
                    tag = None
                    for possible_column in ['Tag', 'tag', 'Tags', 'tags', 'TAG']:
                        if possible_column in row:
                            tag = row[possible_column]
                            break
                    
                    if tag is None:
                        print(f"Warning: No tag column found in row {total_rows}")
                        continue
                    
                    tag_counts[tag] += 1
                    processed_rows += 1
                    
                except Exception as e:
                    print(f"Error processing row {total_rows}: {e}")
                    continue
            
            print(f"Total rows processed: {total_rows}")
            print(f"Successfully processed rows: {processed_rows}")
            
            if total_rows == 0:
                raise ValueError("CSV file is empty")
            
            if processed_rows == 0:
                raise ValueError("No valid rows found in CSV file")
            
            # Get top 10 tags
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            print("Top 10 tags:", top_tags)
            
            # Create yearly data (2023-2025)
            years = list(range(2023, 2026))
            yearly_data = {year: {} for year in years}
            
            # Generate growth patterns for each tag
            for tag, base_count in top_tags:
                counts = generate_growth_pattern(base_count, years)
                for year_index, year in enumerate(years):
                    yearly_data[year][tag] = counts[year_index]
            
            # Calculate yearly totals and percentages
            yearly_totals = {}
            yearly_percentages = {year: {} for year in years}
            
            for year in years:
                total_questions = sum(yearly_data[year].values())
                yearly_totals[year] = total_questions
                
                for tag in yearly_data[year]:
                    percentage = (yearly_data[year][tag] / total_questions) * 100
                    yearly_percentages[year][tag] = round(percentage, 2)
            
            # Prepare data for visualization
            tags_data = []
            for tag, _ in top_tags:
                percentages = [yearly_percentages[year][tag] for year in years]
                average = sum(percentages) / len(percentages)
                tags_data.append({
                    'name': tag,
                    'data': percentages,
                    'average': round(average, 2)
                })
            
            tags_data.sort(key=lambda x: x['average'], reverse=True)
            
            result = {
                'years': years,
                'tags': tags_data,
                'total_questions': yearly_totals
            }
            
            print("Final data structure:", result)
            return result
            
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        raise

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/data')
def get_data():
    try:
        print("Starting to process data...")
        data = process_csv()
        print("Data processed successfully")
        return jsonify(data)
    except Exception as e:
        print(f"Error in get_data: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=3000)