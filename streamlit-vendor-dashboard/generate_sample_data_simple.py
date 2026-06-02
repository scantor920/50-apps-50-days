"""
Alternative data generator using openpyxl directly (no pandas required for generation).
Run: python generate_sample_data_simple.py
"""

from openpyxl import Workbook
import random
from datetime import datetime

# Sample vendor names
VENDORS = [
    "Acme Corp",
    "Blue Sky Industries",
    "CloudTech Solutions",
    "Delta Logistics",
    "Evergreen Supply",
    "Falcon Services",
    "Global Partners",
    "Horizon Distribution",
    "InnovateLabs",
    "JetStream Technologies",
    "Quantum Ventures",
    "Stellar Systems",
]

# Generate quarters from Q1 FY19 to Q4 FY26
quarters = []
for year in range(19, 27):
    for q in range(1, 5):
        quarters.append(f"Q{q}-FY{year}")

# Create workbook
wb = Workbook()
ws = wb.active
ws.title = "Vendor Spend"

# Write header row
ws.append(["Vendor"] + quarters)

# Write vendor data rows
random.seed(42)
for vendor in VENDORS:
    row_data = [vendor]
    
    for i, quarter in enumerate(quarters):
        fy_year = int(quarter.split("-FY")[-1])
        year = 2000 + fy_year
        q_num = int(quarter[1])
        
        # Base spend (100k - 2M)
        base_spend = random.uniform(100_000, 2_000_000)
        
        # Growth factor (8% per year)
        growth_factor = 1.0 + ((year - 2019) * 0.08)
        
        # Seasonality (Q4 is higher)
        seasonality = 1.0 + (q_num - 2.5) * 0.1
        
        # Random noise
        noise = random.uniform(0.9, 1.1)
        
        # Final spend
        spend = base_spend * growth_factor * seasonality * noise
        row_data.append(round(spend, 2))
    
    ws.append(row_data)

# Save
wb.save("vendor_spend.xlsx")
print("✅ Sample data generated: vendor_spend.xlsx")
print(f"   - {len(VENDORS)} vendors")
print(f"   - {len(quarters)} quarters ({quarters[0]} to {quarters[-1]})")
