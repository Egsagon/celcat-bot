# Celcat bot

A simple configurable workflow to dynamically convert your Celcat calendars to Google Calendars.


## Setup

1. Setup Google Calendar API
    - Create a [GCP project](https://developers.google.com/workspace/guides/create-project)
    - Setup the [OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent)
    - Create [Oauth credentials](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)
    - Enable the [Google Calendar API](https://console.cloud.google.com/apis/api/calendar-json.googleapis.com) on the project
    - Set project status to [production](https://console.cloud.google.com/apis/credentials/consent)

2. Setup project
    - Rename your `client_secrets` file to `creds.json` and place it in the repo
    - Create a `config.yml` file (see `config.example.yml`)
    - Install dependencies with `pip install -r requirements.txt`
    - Run the `update.py` script once to link it to your Google account. This will create a `token.pickle` file

3. Setup workflow
    - Configure the workflow in `.github/workflows/update.yml` (see cron interval)
    - Upload your work to a private repo
    - Verify your [Google Calendar](https://calendar.google.com/calendar) has been updated.

## License

Licensed under MIT. See the `LICENSE` file.