import json
import os
import pandas as pd
from collections import Counter

# Directory containing JSON files
json_dir = "metadata-plugin-modernizer"

# Collect data from all JSON files in modernization-metadata directories
data_list = []
for root, dirs, files in os.walk(json_dir):
    if os.path.basename(root) == "modernization-metadata":
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), "r") as f:
                    data = json.load(f)
                    data_list.append(data)

# Create a DataFrame for analysis
df = pd.DataFrame(data_list)

# Create overall reports directory if it doesn't exist
os.makedirs("reports", exist_ok=True)

# Report 1: Per-plugin Failed Migrations (CSV)
grouped = df.groupby("pluginName")
for plugin_name, group_df in grouped:
    failed_migrations = group_df[group_df["migrationStatus"] == "fail"]
    if not failed_migrations.empty:
        # Define the report directory for this plugin
        report_dir = os.path.join(json_dir, plugin_name, "reports")
        os.makedirs(report_dir, exist_ok=True)
        # Save the failure report
        report_path = os.path.join(report_dir, "failed_migrations.csv")
        report_columns = ["migrationId", "migrationStatus", "pullRequestUrl", "checkRunsSummary"]
        failed_migrations[report_columns].to_csv(report_path, index=False)

# Report 2: Overall Summary Report (Markdown)
total_migrations = len(df)
failed_migrations_count = len(df[df["migrationStatus"] == "fail"])
success_rate = ((total_migrations - failed_migrations_count) / total_migrations * 100) if total_migrations > 0 else 0

# Breakdown of failures by migrationId across all plugins
failure_by_recipe = Counter(df[df["migrationStatus"] == "fail"]["migrationId"]).most_common()
failure_table = "\n".join([f"- {recipe}: {count} failures" for recipe, count in failure_by_recipe])

summary = f"""
# Jenkins Plugin Modernizer Report
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- **Total Migrations**: {total_migrations}
- **Failed Migrations**: {failed_migrations_count}
- **Success Rate**: {success_rate:.2f}%

## Failures by Recipe
{failure_table if failure_by_recipe else "No failures recorded."}
"""
summary_path = os.path.join(json_dir, "reports", "summary.md")
os.makedirs(os.path.dirname(summary_path), exist_ok=True)  
with open(summary_path, "w") as f:
    f.write(summary)