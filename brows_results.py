
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

smartschoolSession = Smartschool(creds= creds)

# Example: List courses
print("Fetching results...")
    
results = list(Results(smartschool=smartschoolSession))
for result in results:
    for key, value in vars(result).items():
        print(f"{key}: {value}")


# ... add calls to other features as needed ...

print("\nDone.")