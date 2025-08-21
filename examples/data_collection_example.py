#!/usr/bin/env python3
"""
Example usage of FPL Data Collection

This script demonstrates how to use the data collection module
to fetch and validate FPL data.
"""

import sys
from pathlib import Path

# Add src to path to import modules
sys.path.append(str(Path(__file__).parent.parent / "src"))

from data_collection import FPLDataCollector
from data_validation import FPLDataValidator


def main():
    """Example of data collection and validation workflow."""
    
    print("🚀 FPL Data Collection Example")
    print("=" * 40)
    
    # Initialize data collector
    collector = FPLDataCollector(output_dir="data/raw")
    
    try:
        # Collect all data
        print("Step 1: Collecting data from FPL API...")
        collector.collect_all_data()
        
        # Validate collected data
        print("\nStep 2: Validating collected data...")
        validator = FPLDataValidator(data_dir="data/raw")
        validation_success = validator.run_validation()
        
        if validation_success:
            print("\n🎉 Data collection and validation completed successfully!")
            print("\nNext steps:")
            print("1. Run feature engineering: make features")
            print("2. Train forecasting model: make forecast") 
            print("3. Optimize squad: make optimise_gw N=1")
        else:
            print("\n❌ Data validation failed. Please check the issues above.")
            
    except Exception as e:
        print(f"\n❌ Error during data collection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()