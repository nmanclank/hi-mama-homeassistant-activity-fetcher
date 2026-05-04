# HiMama (Lillio) Home Assistant Integration

This is a custom integration for Home Assistant to display the latest activities from the [HiMama (Lillio)](https://www.himama.com/) platform. It creates a sensor that shows the most recent activity for a selected child and stores all of today's activities in the sensor's attributes.

## Features

- **Fetches Daily Activities:** Retrieves the latest activities for a selected child from the HiMama reports page.
- **Real-time Sensor:** Creates a sensor entity in Home Assistant for the most recent activity. The sensor's state is the title of the latest activity (e.g., "Meals", "Naps").
- **Detailed Attributes:** Stores all activities from the latest report in the sensor's attributes.
- **Auto-Discovery:** Automatically detects children associated with your account, so you don't need to manually find their IDs.

## Installation

### HACS (Recommended)

1. Go to HACS > Integrations > ... (three dots in the top right).
2. Select "Custom repositories".
3. Paste the URL to this repository in the "Repository" field.
4. Select "Integration" as the category.
5. Click "Add".
6. Search for "HiMama Activities" and install it.
7. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/himama_activities` directory from this repository into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.

## Configuration

1. Go to Settings > Devices & Services.
2. Click Add Integration and search for "HiMama Activities".
3. Enter your HiMama email and password.
4. The integration will fetch the list of children from your account. Select the child you want to monitor from the dropdown.
5. A new sensor will be created for the selected child. If you want to monitor multiple children, add the integration again for each child.

## Sensor Usage

The integration creates a sensor named `sensor.<child_name>_latest_activity`.

- **State:** The state of the sensor will be the title of the most recent activity (e.g., "Naps").
- **Attributes:** The sensor's attributes contain a list of activities. Each activity is a dictionary with the following keys:
  - `id`: The unique ID of the activity (incremented per item).
  - `timestamp`: The time the activity occurred (ISO 8601 format).
  - `title`: A descriptive title for the activity.
  - `details`: Additional details about the activity.
  - `photo_url`: A URL to a photo associated with the activity (if available).
  - `staff`: The name of the staff member who recorded the activity (if available).

You can use this data to create automations or display it in your Home Assistant dashboard.
