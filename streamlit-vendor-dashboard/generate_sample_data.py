"""
Generate sample vendor spend data for testing the dashboard.
Run: python generate_sample_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
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

# Generate quarters from Q1 2019 to Q4 2026
quarters = []
for year in range(2019, 2027):
    for q in range(1, 5):
        quarters.append(f"Q{q} {year}")

# Create sample data
np.random.seed(42)
data = {
    "Vendor": VENDORS,
}

# Generate spend values for each quarter
for quarter in quarters:
    # Base spend varies by vendor (some larger, some smaller)
    base_spend = np.random.uniform(100_000, 2_000_000, len(VENDORS))
    
    # Add seasonality and growth trend
    year = int(quarter.split()[-1])
    q_num = int(quarter[1])
    
    # Growth from 2019 to 2026 (upward trend over time)
    growth_factor = 1.0 + ((year - 2019) * 0.08)
    
    # Seasonality (Q4 tends higher)
    seasonality = 1.0 + (q_num - 2.5) * 0.1
    
    # Random noise
    noise = np.random.uniform(0.9, 1.1, len(VENDORS))
    
    # Combine factors
    spend = base_spend * growth_factor * seasonality * noise
    
    # For projections (Q1 2026 onward), add a slight variance
    if (year == 2026 and q_num >= 1) or year > 2026:
        spend = spend * np.random.uniform(0.95, 1.05, len(VENDORS))
    
    data[quarter] = spend.round(2)

df = pd.DataFrame(data)

# Save to Excel
output_path = Path(__file__).parent / "vendor_spend.xlsx"
df.to_excel(output_path, index=False)

print(f"✅ Sample data generated: {output_path}")
print(f"   - {len(VENDORS)} vendors")
print(f"   - {len(quarters)} quarters ({quarters[0]} to {quarters[-1]})")
print(f"   - Projections: {quarters[-3:]} (and beyond)")
