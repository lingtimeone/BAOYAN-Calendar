# --- START OF FILE load_calendar.py ---

import yaml
from ics import Calendar, Event
import time
import os
import sqlite3 # import sqlite3 library - Removed fullwidth comma here

# --- Configuration ---
DB_FILE = 'baoyan_calendar.db' # Database file name
ICS_FILE = 'calendar.ics'     # ICS file name
# ---------------------

print("--- Baoyan Calendar Generator Script ---")

# --- 1. Read and merge all YAML files ---
print("Reading and merging YAML files...")
calendar_data = None
all_info_path = 'all_info'

# Check if all_info directory exists and is a directory
if not os.path.exists(all_info_path) or not os.path.isdir(all_info_path):
    print(f"Warning: Directory '{all_info_path}' not found or is not a directory. Cannot read YAML files.")
else:
    for dirpath, dirnames, filenames in os.walk(all_info_path):
        # Iterate through files in the current directory of walk
        for filename in filenames:
            if filename.endswith('.yaml'):
                filepath = os.path.join(dirpath, filename)
                # print(f"  Reading file: {filepath}") # Uncomment for detailed file processing
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Skip empty files
                        if not content.strip():
                            print(f"  Warning: Skipping empty YAML file: {filepath}")
                            continue

                        yaml_content = yaml.safe_load(content)

                        # Check if YAML content is a dictionary and contains an 'events' list
                        if not isinstance(yaml_content, dict) or 'events' not in yaml_content or not isinstance(yaml_content['events'], list):
                             print(f"  Warning: Skipping invalid YAML file format (missing 'events' list or incorrect format): {filepath}")
                             continue

                        if calendar_data is None:
                            # First file loaded
                            calendar_data = yaml_content
                        else:
                            # Subsequent files, extend the 'events' list
                            # Ensure calendar_data already has an 'events' list before extending
                            if 'events' in calendar_data and isinstance(calendar_data['events'], list):
                                 calendar_data['events'].extend(yaml_content['events'])
                            else:
                                 # Handle case where initial calendar_data did not have a valid 'events' list
                                 print(f"  Warning: Unexpected calendar_data structure encountered before processing {filepath}")
                                 # Optionally handle this, e.g., re-initialize calendar_data
                                 pass # Currently skips extending


                except yaml.YAMLError as exc:
                    print(f"  Error: Failed to parse YAML file {filepath}: {exc}")
                    continue
                except Exception as e:
                    print(f"  Error: Failed to process file {filepath}: {e}")
                    continue

# Ensure all_events list is correctly populated after reading all files
if calendar_data is None or 'events' not in calendar_data or not isinstance(calendar_data['events'], list):
     print("Warning: No valid YAML event data found. Using an empty event list.")
     all_events = [] # Initialize as empty list to prevent NameError
else:
     all_events = calendar_data['events'] # Get the events list from the merged data

print(f"Finished reading YAML files. Total {len(all_events)} events found.")
print("-" * 20)


# --- 2. Write events to ICS file ---
print(f"Generating ICS file: {ICS_FILE}...")
c = Calendar()
if all_events:
    for event in all_events:
        try:
            e = Event()
            # Use .get() with default values to avoid KeyError if key is missing
            e.name = event.get('school', 'Unknown School')
            e.begin = event.get('begin') # begin and end are required for valid ICS events
            e.end = event.get('end')
            description = event.get('description', '')
            url_info = event.get('url', '')
            e.description = f"{description}  {url_info}".strip() if description or url_info else ""

            # Check for required fields before adding to ICS
            if not e.begin or not e.end:
                 # print(f"  Warning: Skipping ICS event due to missing begin/end time: {e.name}") # Uncomment for detailed warning
                 continue # Skip adding this event to ICS if critical fields are missing

            c.events.add(e)

        except Exception as e:
            print(f"  Error: Failed to process event for ICS ({event.get('school', 'Unknown School')}): {e}")
            continue # Skip processing current event for ICS


    try:
        # Delete existing ICS file
        if os.path.exists(ICS_FILE):
            os.remove(ICS_FILE)
            # print(f"Deleted old file: {ICS_FILE}") # Uncomment for detailed file deletion

        # Write the new ICS file
        with open(ICS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(c.serialize())
        print(f"Successfully generated ICS file: {ICS_FILE}")

    except Exception as e:
        print(f"Error: Failed to write ICS file: {e}")

else:
    print("No event data to generate ICS file.")
print("-" * 20)


# --- 3. Write events to SQLite database (.db) file ---
print(f"Writing to database file: {DB_FILE}...")
conn = None
try:
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create events table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT,
            school TEXT,
            begin_time TEXT,
            end_time TEXT,
            description TEXT,
            url TEXT
        )
    ''')
    conn.commit() # Commit table creation

    # Optional: Clear old data before inserting new (if you want the DB to only contain current YAML events)
    cursor.execute('DELETE FROM events')
    conn.commit()
    # print("Cleared old event data from database.") # Uncomment for detailed clear

    if all_events:
        # Prepare data for insertion
        data_to_insert = []
        for event in all_events:
            # Prepare single row data, use .get() for potentially missing keys
            row_data = (
                event.get('year', ''),
                event.get('school', ''),
                event.get('begin', ''),
                event.get('end', ''),
                event.get('description', ''),
                event.get('url', '')
            )
            data_to_insert.append(row_data)

        # Execute batch insertion for efficiency
        if data_to_insert:
            try:
                cursor.executemany('''
                    INSERT INTO events (year, school, begin_time, end_time, description, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                conn.commit() # Commit the insertions
                print(f"Successfully inserted {len(data_to_insert)} event records into database.")
            except sqlite3.Error as e:
                print(f"Error: Failed to insert data into database: {e}")
                conn.rollback() # Rollback changes on error

    else:
        print("No event data to insert into database.")

except sqlite3.Error as e:
    print(f"Error: Database connection or operation failed: {e}")
except Exception as e:
    print(f"Error: An unknown error occurred during database writing: {e}")

finally:
    # Ensure database connection is closed
    if conn:
        conn.close()
        # print("Database connection closed.") # Uncomment for detailed close
print("-" * 20)


# --- 4. Update README.md (using fixed ICS filename) ---
print("Updating README.md file...")

# Ensure this is YOUR GitHub username and repo name
usr = 'lingtimeone'
repo = 'BAOYAN-Calendar'
branch = 'main'

# Online calendar viewer URL, using the fixed ICS_FILE name
online_calendar_url = f"https://open-web-calendar.hosted.quelltext.eu/calendar.html?url=https%3A%2F%2Fraw.githubusercontent.com%2F{usr}%2F{repo}%2F{branch}%2F{ICS_FILE}"

# Get current time for last update timestamp (+8 hours for Beijing time if needed)
last_update = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 8 * 60 * 60))

# Using string concatenation to build README content, avoiding triple-quote issues
readme_content = (
    f"# Last Updated: {last_update}\n\n" # Use English or remove non-ASCII
    f"[![🕊Next time for sure](img.png \"This is a pigeon\")]({online_calendar_url})\n\n" # Image alt/title English or remove non-ASCII
    "# Click Hard Above 👆\n\n" # Use English or remove non-ASCII. Retained emoji for visual similarity.
    "# Disclaimer: This repository is non-profit and does not assume any responsibility for specific content\n\n" # Use English
    "# pr:\n"
    "1. fork this repository\n" # Use English
    "2. clone to local, create school folder in `all_info` folder, and create college yaml file in it, format as follows:\n" # Use English
    "```yaml\n" # YAML code block start
    "events:\n"
    "  - year: \"2023\"\n"
    "    school: \"ShuShu University\"\n" # Use English or Pinyin
    "    begin: \"2023-01-01\"\n"
    "    end: \"2023-01-02\"\n"
    "    description: \"ShuShu College\"\n" # Use English or Pinyin
    "    url: \"https://www.shushu.edu.cn/\"\n"
    "```\n\n" # YAML code block end, two newlines after ```
    "3. push update your fork, and submit pr\n" # Use English
    "4. wait for merge\n" # Use English
    "5. wait for auto update to complete and click the pigeon\n\n" # Use English
    "**Finally, regarding the future, if there is any incorrect information, please verify it in time and raise an issue or pr**\n" # Use English
) # End of concatenation

try:
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content) # Write the combined string
    print("README.md file updated successfully.")

except Exception as e:
    print(f"Error: Failed to update README.md file: {e}")

print("-" * 20)
print("Script execution finished.")

# --- END OF FILE load_calendar.py ---