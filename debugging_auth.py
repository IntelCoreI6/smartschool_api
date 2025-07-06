import sys
import os
import logging
import time
from pathlib import Path
import requests # Added import
from bs4 import BeautifulSoup # Added import
from urllib.parse import urljoin # Added import
import yaml # Added import
import datetime # Added import

# --- Configuration ---
LOG_LEVEL = logging.DEBUG
COOKIE_FILE = Path.cwd() / "cookies.txt" # Still useful for session persistence if needed
CREDENTIALS_FILE = Path.cwd() / "credentials.yml"

# --- Setup ---
print("Setting up logger...")
# Basic logging setup if smartschool.logger is not available
logging.basicConfig(level=LOG_LEVEL, format="[%(asctime)s] [%(levelname)s] %(name)s > %(message)s")
logger = logging.getLogger("standalone_auth_test")

# --- Credentials ---
# Load credentials from YAML file
try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = yaml.safe_load(f)
    SMARTSCHOOL_DOMAIN = creds['main_url']
    USERNAME = creds['username']
    PASSWORD = creds['password']
    BIRTH_DATE = creds.get('birth_date') # Use .get() as birth_date might be optional in some contexts
    if not BIRTH_DATE:
        logger.warning("Birth date not found in credentials.yml, verification might fail if required.")
except FileNotFoundError:
    logger.error(f"ERROR: Credentials file not found at {CREDENTIALS_FILE}")
    sys.exit(1)
except KeyError as e:
    logger.error(f"ERROR: Missing key {e} in {CREDENTIALS_FILE}")
    sys.exit(1)
except Exception as e:
    logger.error(f"ERROR: Failed to load or parse {CREDENTIALS_FILE}: {e}")
    sys.exit(1)

# --- Setup ---
print("Setting up logger...")
# Basic logging setup if smartschool.logger is not available
logging.basicConfig(level=LOG_LEVEL, format="[%(asctime)s] [%(levelname)s] %(name)s > %(message)s")
logger = logging.getLogger("standalone_auth_test")

# --- Helper Functions ---

def get_form_inputs(html_content, form_selector):
    """Parses HTML to extract input values from a form."""
    soup = BeautifulSoup(html_content, 'html.parser')
    form = soup.select_one(form_selector)
    if not form:
        logger.error(f"Could not find form with selector: {form_selector}")
        return None
    
    inputs = {}
    for input_tag in form.find_all(['input', 'select', 'textarea']):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            # Basic handling for multiple inputs with same name (e.g., checkboxes)
            # For this login form, it's likely not needed, but good practice
            if name in inputs:
                if isinstance(inputs[name], list):
                    inputs[name].append(value)
                else:
                    inputs[name] = [inputs[name], value]
            else:
                inputs[name] = value
    logger.debug(f"Extracted inputs from {form_selector}: {list(inputs.keys())}")
    return inputs

def check_authentication(session, base_url):
    """
    Attempts to fetch the main Smartschool page ('/').
    Prints the HTML if successful (status 200 and not redirected to login/verification).
    Returns True if authenticated, False otherwise.
    """
    logger.info("Attempting to fetch main page ('/') to verify authentication...")
    try:
        home_url = base_url + "/"
        home_resp = session.get(home_url, allow_redirects=True) # Allow redirects to see final URL

        logger.info(f"GET / response status: {home_resp.status_code}, Final URL: {home_resp.url}")

        if home_resp.status_code == 200 and not home_resp.url.endswith(("/login", "/account-verification")):
            logger.info("Authentication successful! Printing homepage HTML:")
            print("\n" + "="*20 + " HOMEPAGE HTML START " + "="*20 + "\n")
            print(home_resp.text)
            print("\n" + "="*20 + "  HOMEPAGE HTML END  " + "="*20 + "\n")
            return True
        elif home_resp.url.endswith("/login"):
            logger.error("Authentication check failed: Ended on /login")
            return False
        elif home_resp.url.endswith("/account-verification"):
            logger.error("Authentication check failed: Ended on /account-verification")
            return False
        else:
            logger.error(f"Authentication check failed: Unexpected status code {home_resp.status_code} or URL {home_resp.url}")
            return False
    except requests.exceptions.RequestException as e:
        logger.exception(f"Authentication check failed: RequestException during GET /: {e}")
        return False
    except Exception as e:
        logger.exception("Authentication check failed: Unexpected error during GET /")
        return False

# --- Standalone Authentication Logic ---

def attempt_standalone_login():
    """Performs the full login and verification flow directly."""
    logger.info("\n--- Running Standalone Authentication Attempt ---")
    base_url = f"https://{SMARTSCHOOL_DOMAIN}"
    login_url = base_url + "/login"
    verification_url = base_url + "/account-verification"

    # Use a requests session to handle cookies automatically
    session = requests.Session()
    session.headers.update({"User-Agent": "StandaloneAuthTester/1.0"})

    try:
        # 1. GET the login page
        logger.info(f"GET {login_url} to obtain login form and cookies")
        login_page_resp = session.get(login_url)
        login_page_resp.raise_for_status()

        if not login_page_resp.url.endswith("/login"):
             logger.warning(f"Initial GET {login_url} redirected to {login_page_resp.url}. Maybe already logged in?")
             return check_authentication(session, base_url)

        # 2. Parse the login form
        logger.info("Parsing login form...")
        login_form_inputs = get_form_inputs(login_page_resp.text, 'form[name="login_form"]')
        if not login_form_inputs: raise ValueError("Failed to parse login form inputs.")

        # 3. Prepare login POST data
        login_data = login_form_inputs.copy()
        username_field = next((k for k in login_data if 'username' in k), None)
        password_field = next((k for k in login_data if 'password' in k), None)
        if not username_field or not password_field: raise ValueError(f"Could not find username or password fields. Found: {list(login_data.keys())}")
        login_data[username_field] = USERNAME
        login_data[password_field] = PASSWORD
        log_data = {k: (v if 'password' not in k else '********') for k, v in login_data.items()}
        logger.debug(f"Login POST data prepared: {log_data}")

        # 4. POST the login data
        logger.info(f"POSTing credentials to {login_url}")
        # Follow redirects initially to see where the login POST *ultimately* lands
        login_post_resp = session.post(login_url, data=login_data, allow_redirects=True)
        login_post_resp.raise_for_status() # Check for errors after redirects

        logger.info(f"Login POST completed. Final URL after redirects: {login_post_resp.url}")

        # 5. Handle Verification if needed
        # Check if the *final* URL after the login POST is the verification page
        needs_verification = login_post_resp.url.endswith('/account-verification')

        if needs_verification:
            logger.info("Account verification required.")
            # We already landed on the verification page, use its content
            verification_html = login_post_resp.text
            current_verification_url = login_post_resp.url

            # Parse verification form
            logger.info("Parsing verification form...")
            verification_form_inputs = get_form_inputs(verification_html, 'form[name="account_verification_form"]')
            if not verification_form_inputs: verification_form_inputs = get_form_inputs(verification_html, 'form:has(input#account_verification_form__token)') # Fallback
            if not verification_form_inputs: raise ValueError("Failed to parse verification form inputs.")

            # Prepare verification POST data
            verification_data = verification_form_inputs.copy()
            security_question_field = next((k for k in verification_data if '_security_question_answer' in k), None)
            if not security_question_field: raise ValueError("Could not find security question field in verification form.")
            if not BIRTH_DATE: raise ValueError("Birth date is required for verification but not provided.")

            # --- Format Birth Date Correctly ---
            birth_date_str = BIRTH_DATE
            if isinstance(BIRTH_DATE, datetime.date):
                birth_date_str = BIRTH_DATE.strftime('%Y-%m-%d')
                logger.debug(f"Formatted datetime.date object to string: {birth_date_str}")
            elif isinstance(BIRTH_DATE, str):
                # Ensure it has hyphens if it's already a string
                original_birth_date_str = birth_date_str # Keep original for comparison
                birth_date_str = BIRTH_DATE.replace('/', '-')
                if birth_date_str != original_birth_date_str:
                     logger.debug(f"Replaced slashes in birth date string: {birth_date_str}")
            else:
                 logger.warning(f"Birth date is of unexpected type: {type(BIRTH_DATE)}. Attempting to use as is.")
            # --- End Format Birth Date ---

            verification_data[security_question_field] = birth_date_str # Use the formatted string

            logger.debug(f"Verification POST data prepared: {verification_data}")

            # POST the verification data
            logger.info(f"POSTing verification data to {current_verification_url}")
            verification_post_resp = session.post(current_verification_url, data=verification_data, allow_redirects=True)
            verification_post_resp.raise_for_status()
            logger.info(f"Verification POST response status: {verification_post_resp.status_code}, Final URL: {verification_post_resp.url}")

            # After verification POST, check if we landed on the verification page *again* (failure)
            if verification_post_resp.url.endswith('/account-verification'):
                logger.error("Verification POST failed: Still on verification page.")
                # Optionally print response text for clues
                # print(verification_post_resp.text[:1000])
                return False
            # If not on verification page, proceed to final check below

        # 6. Final Check (runs after successful login OR successful verification)
        logger.info("Performing final authentication check...")
        # Use the session state *after* all login/verification steps
        # We might already be on the homepage if login didn't need verification,
        # or if verification succeeded. check_authentication handles this.
        return check_authentication(session, base_url)

    except requests.exceptions.RequestException as e:
        logger.exception(f"Standalone Login Failed: RequestException: {e}")
        return False
    except ValueError as e:
        logger.error(f"Standalone Login Failed: ValueError: {e}")
        return False
    except Exception as e:
        logger.exception("Standalone Login Failed: Unexpected error")
        return False

# --- Main Execution ---
print("\nStarting standalone authentication test...")

authenticated = attempt_standalone_login()

if authenticated:
    print("\nSUCCESS: Standalone authentication worked.")
else:
    print("\nFAILURE: Standalone authentication failed.")

print("\nTest script finished.")