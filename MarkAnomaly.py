import os
import json
import shutil
import time
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any, Optional

class PostDataProcessor:
    def __init__(self, base_dir: str = "results", backup_dir: str = "results_backup"):
        """
        Initialize the post-data processor.
        
        Args:
            base_dir: Directory containing the results
            backup_dir: Directory for backups
        """
        self.base_dir = base_dir
        self.backup_dir = backup_dir
        self.log_file = "logs/post_process_log.txt"
        
        # Create necessary directories
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Initialize statistics
        self.stats = {
            "total_files": 0,
            "modified_files": 0,
            "errors": 0,
            "out_of_budget": 0,
            "out_of_wholesale": 0,
            "irrational_refuse": 0,
            "overpayment": 0,
            "anomalies": 0
        }

    def backup_file(self, file_path: str) -> str:
        """Create a backup of the file."""
        backup_path = os.path.join(self.backup_dir, os.path.relpath(file_path, self.base_dir))
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def calculate_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate various anomalies in the negotiation data.
        
        Args:
            data: The negotiation data dictionary
            
        Returns:
            Dictionary containing anomaly flags and metrics
        """
        anomalies = {}
        
        if "seller_price_offers" in data and isinstance(data["seller_price_offers"], list):
            price_offers = data["seller_price_offers"]
            
            if len(price_offers) > 0 and price_offers[0] > 0:
                first_price = price_offers[0]
                last_price = price_offers[-1]
                
                # Calculate bargaining rate
                anomalies["bargaining_rate"] = (first_price - last_price) / first_price
                
                # Check for overpayment
                anomalies["overpayment"] = last_price > first_price
                
                # Check budget constraints
                if "budget" in data:
                    anomalies["out_of_budget"] = last_price > data["budget"]
                    if data.get("negotiation_result") == "rejected":
                        anomalies["irrational_refuse"] = last_price < data["budget"]
                
                # Check wholesale price constraints
                if "product_data" in data and "Wholesale Price" in data["product_data"]:
                    wholesale_price_str = data["product_data"]["Wholesale Price"]
                    wholesale_price = float(wholesale_price_str.replace("$", "").replace(",", ""))
                    anomalies["out_of_wholesale"] = last_price < wholesale_price
                
                # Calculate price volatility
                if len(price_offers) > 1:
                    price_changes = np.diff(price_offers)
                    anomalies["price_volatility"] = np.std(price_changes) if len(price_changes) > 0 else 0
                    anomalies["max_price_change"] = np.max(np.abs(price_changes)) if len(price_changes) > 0 else 0
        
        return anomalies

    def process_file(self, file_path: str) -> bool:
        """
        Process a single JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            True if file was modified, False otherwise
        """
        try:
            # Backup file
            self.backup_file(file_path)
            
            # Read JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Calculate anomalies
            anomalies = self.calculate_anomalies(data)
            
            # Update data with anomalies
            modified = False
            for key, value in anomalies.items():
                if key not in data or data[key] != value:
                    data[key] = value
                    modified = True
            
            # Update statistics
            if modified:
                self.stats["modified_files"] += 1
                if anomalies.get("out_of_budget"):
                    self.stats["out_of_budget"] += 1
                if anomalies.get("out_of_wholesale"):
                    self.stats["out_of_wholesale"] += 1
                if anomalies.get("irrational_refuse"):
                    self.stats["irrational_refuse"] += 1
                if anomalies.get("overpayment"):
                    self.stats["overpayment"] += 1
                
                # Save modified data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            return modified
            
        except Exception as e:
            self.stats["errors"] += 1
            with open(self.log_file, 'a', encoding='utf-8') as log:
                log.write(f"Error processing {file_path}: {str(e)}\n\n")
            return False

    def process_all_files(self):
        """Process all JSON files in the results directory."""
        with open(self.log_file, 'w', encoding='utf-8') as log:
            log.write("Processing JSON files for anomalies and statistics\n")
            log.write("=" * 80 + "\n\n")
            
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    if file.endswith('.json'):
                        self.stats["total_files"] += 1
                        file_path = os.path.join(root, file)
                        self.process_file(file_path)
            
            # Write summary
            log.write("\nSummary:\n")
            for key, value in self.stats.items():
                log.write(f"{key}: {value}\n")
            log.write(f"\nBackup created at: {self.backup_dir}\n")
        
        print(f"Process completed. {self.stats['total_files']} files processed, {self.stats['modified_files']} files modified.")
        print(f"Full backup created at: {self.backup_dir}")
        print(f"See {self.log_file} for details of changes made.")

    def generate_summary_report(self, output_file: str = "analysis/summary_report.csv"):
        """
        Generate a summary report of all processed negotiations.
        
        Args:
            output_file: Path to save the summary report
        """
        summary_data = []
        
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # Extract relevant information
                        summary = {
                            "file_path": file_path,
                            "model_combination": f"{data.get('seller_model_name', '')}_vs_{data.get('buyer_model_name', '')}",
                            "budget_scenario": data.get("budget_scenario", ""),
                            "negotiation_result": data.get("negotiation_result", ""),
                            "bargaining_rate": data.get("bargaining_rate", None),
                            "out_of_budget": data.get("out_of_budget", False),
                            "out_of_wholesale": data.get("out_of_wholesale", False),
                            "irrational_refuse": data.get("irrational_refuse", False),
                            "overpayment": data.get("overpayment", False),
                            "price_volatility": data.get("price_volatility", None),
                            "max_price_change": data.get("max_price_change", None)
                        }
                        summary_data.append(summary)
                    except Exception as e:
                        print(f"Error processing {file_path} for summary: {str(e)}")
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(summary_data)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"Summary report saved to {output_file}")

def main():
    processor = PostDataProcessor()
    processor.process_all_files()
    processor.generate_summary_report()

if __name__ == "__main__":
    main() 