import json

# File paths
original_file = "physiology_A.json"
update_file = "physiology_A_update.json"

# Load the original JSON file (list of dicts)
with open(original_file, "r", encoding="utf-8") as f:
    original_data = json.load(f)

# Load the update JSON file (list of dicts)
with open(update_file, "r", encoding="utf-8") as f:
    update_data = json.load(f)

# Convert update_data to a dict for fast lookup by AnswerNO
update_dict = {item["AnswerNO"]: item["file_name"] for item in update_data}

# Merge file_name into original_data where AnswerNO matches
for item in original_data:
    answer_no = item.get("AnswerNO")
    if answer_no in update_dict:
        item["file_name"] = update_dict[answer_no]

# Save the updated data back to the original file
with open(original_file, "w", encoding="utf-8") as f:
    json.dump(original_data, f, indent=4, ensure_ascii=False)

print(f"Updated {original_file} successfully.")
