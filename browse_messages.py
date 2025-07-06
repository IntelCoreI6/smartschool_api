
import sys
import os
import logging
from datetime import date # Added for lesson example
from datetime import date, timedelta

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if (src_path not in sys.path):
    sys.path.insert(0, src_path)

from smartschool import (
    Smartschool,
    PathCredentials,
    Courses,
    TopNavCourses,
    Results,
    Periods,
    FutureTasks,
    SmartschoolLessons,
    SmartschoolHours,
    MessageHeaders,
    BoxType,
    StudentSupportLinks,
    # ... import other needed classes
)
from smartschool.logger import setup_logger

# Optional: Enable detailed logging
setup_logger(logging.DEBUG)

# Load credentials from credentials.yml (or specified path)
creds = PathCredentials()
# creds = PathCredentials("path/to/your/credentials.yml")

# Start the session (handles login)
# session = Smartschool.start(creds)
smartschoolSession = Smartschool(creds=creds)

# Example: List courses
print("Fetching messages...")
# date of last week

# timestamp_to_use=date.today() - timedelta(weeks=1)
# timestamp_to_use=date.today()
# timestamp_to_use=date.today() + timedelta(days=1)
# timestamp_to_use=date(2025, 6, 11)
timestamp_to_use=None
messages = list(MessageHeaders(smartschool=smartschoolSession))
for message in messages[0:10]:
# agendalesson = agenda[0]
# if agendalesson:
    for key, value in vars(message).items():
        print(f"{key}: {value}")
    print("----")

# ... add calls to other features as needed ...

print("\nDone.")