"""API client for HiMama."""
import asyncio
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup

from .const import DEFAULT_LOGIN_URL, DEFAULT_ACCOUNTS_URL, DEFAULT_REPORTS_URL

_LOGGER = logging.getLogger(__name__)

class HiMamaApiError(Exception):
    """General API error."""
    pass

class HiMamaAuthError(Exception):
    """Authentication error."""
    pass

class HiMamaNoChildrenError(Exception):
    """No children found error."""
    pass

class HiMamaApi:
    def __init__(self, session, email, password, child_id=None):
        self.session = session
        self.email = email
        self.password = password
        self.child_id = child_id

    async def async_login(self):
        """Log into HiMama."""
        try:
            async with self.session.get(DEFAULT_LOGIN_URL) as resp:
                text = await resp.text()

            match = re.search(r'meta name="csrf-token" content="(.*?)"', text)
            if not match:
                raise HiMamaApiError("Could not find CSRF token")
            csrf_token = match.group(1)

            data = {
                "authenticity_token": csrf_token,
                "user[login]": self.email,
                "user[password]": self.password,
                "commit": "Log In",
            }

            async with self.session.post(DEFAULT_LOGIN_URL, data=data) as resp:
                if resp.status >= 400:
                    raise HiMamaAuthError("Login failed")
                if "login" in str(resp.url):
                    raise HiMamaAuthError("Login failed (invalid credentials)")
        except Exception as e:
            if isinstance(e, (HiMamaApiError, HiMamaAuthError)):
                raise
            raise HiMamaApiError(f"Error during login: {e}")

    async def async_get_kids(self):
        """Fetch list of kids after login."""
        try:
            # Try to get the root page which should redirect to dashboard
            async with self.session.get("https://www.himama.com/") as resp:
                html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            kids = []
            seen_ids = set()

            for a in soup.find_all('a', href=True):
                href = a['href']
                match = re.search(r'/accounts/(\d+)', href)
                if match:
                    child_id = match.group(1)
                    if child_id not in seen_ids:
                        name = a.get_text(strip=True)
                        if not name:
                            img = a.find('img')
                            if img and img.get('alt'):
                                name = img['alt']
                            else:
                                name = f"Child {child_id}"
                        
                        if name.lower() in ["reports", "profile", "messages", "attendance"]:
                            name = f"Child {child_id}"
                            
                        seen_ids.add(child_id)
                        kids.append({"id": child_id, "name": name})

            if not kids:
                raise HiMamaNoChildrenError("No children found")

            return kids
        except Exception as e:
            if isinstance(e, HiMamaNoChildrenError):
                raise
            raise HiMamaApiError(f"Error getting kids: {e}")

    async def async_get_activities(self):
        """Get latest activities for the child."""
        try:
            url = DEFAULT_ACCOUNTS_URL.format(self.child_id)
            async with self.session.get(url) as resp:
                text = await resp.text()

            reports = re.finditer(r'href="/reports/(.*?)"', text)
            
            activities = []
            activity_id_counter = 1

            for report in reports:
                report_id = report.group(1)
                report_url = DEFAULT_REPORTS_URL.format(report_id)
                async with self.session.get(report_url) as resp:
                    report_html = await resp.text()

                # Running BeautifulSoup parsing in executor to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                parsed_activities = await loop.run_in_executor(None, self._parse_report_html, report_html, activity_id_counter)
                activities.extend(parsed_activities)
                activity_id_counter += len(parsed_activities)
                
                # Procare addon only gets latest day or week, we can just process the first few reports
                # to avoid massive fetching. Let's just break after the first report (latest day)
                break

            return activities
            
        except Exception as e:
            raise HiMamaApiError(f"Error getting activities: {e}")

    def _parse_report_html(self, html, start_id):
        soup = BeautifulSoup(html, "html.parser")
        activities = []
        
        # Determine the date of the report
        report_date = datetime.now()
        h2s = soup.find_all("h2")
        for h2 in h2s:
            h2_text = h2.get_text(strip=True)
            if "Report" in h2_text and "Preview" not in h2_text:
                try:
                    # Let's try to find the date near the h2
                    next_node = h2.find_next_sibling()
                    if next_node:
                        date_str = next_node.get_text(strip=True)
                        # Matches e.g. "Monday, May 04, 2026"
                        match = re.search(r'\w+day, \w+ \d{1,2}, \d{4}', date_str)
                        if match:
                            report_date = datetime.strptime(match.group(0), "%A, %b %d, %Y")
                except Exception:
                    pass
                break

        for h2 in h2s:
            h2_text = h2.get_text(strip=True)
            if "Preview" in h2_text or "Report" in h2_text:
                continue

            category = h2_text
            details = []
            
            # Extract content from the next sibling (likely a div or ul containing details)
            next_node = h2.find_next_sibling()
            if next_node:
                text = next_node.get_text(strip=True, separator=' | ')
                if text:
                    details.append(text)
                
            if details:
                activities.append({
                    "id": str(start_id),
                    "timestamp": report_date.isoformat(),
                    "title": category,
                    "details": " | ".join(details),
                    "photo_url": None,
                    "staff": None
                })
                start_id += 1

        # Reverse so the newest is first in the list
        activities.reverse()
        return activities
