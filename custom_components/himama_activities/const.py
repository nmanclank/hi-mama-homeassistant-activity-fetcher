"""Constants for the HiMama Activities integration."""

DOMAIN = "himama_activities"
PLATFORMS = ["sensor"]

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 30  # minutes

DEFAULT_LOGIN_URL = "https://www.himama.com/login"
DEFAULT_ACCOUNTS_URL = "https://www.himama.com/accounts/{}/reports"
DEFAULT_REPORTS_URL = "https://www.himama.com/reports/{}"
