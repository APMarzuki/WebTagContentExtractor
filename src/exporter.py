"""
Simplified Data export functionality without pandas
"""

import csv
import os
from datetime import datetime

class DataExporter:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def export(self, data, filename, format_type='csv'):
        """
        Export data to CSV file (Excel support removed for simplicity)
        """
        # Force CSV format for now
        if not filename.endswith('.csv'):
            filename = filename.replace('.xlsx', '.csv') + '.csv'

        # Full output path
        output_path = os.path.join(self.output_dir, filename)

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Extracted_Content', 'Extraction_Date'])

                # Write data
                for item in data:
                    writer.writerow([item, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

            return output_path

        except Exception as e:
            raise Exception(f"Export failed: {e}")