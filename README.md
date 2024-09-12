# Celcat bot

A simple server script to transfer events from a Celcat calender to a Google calendar.

## Setup

- Create a GCP project and OAuth as per [the GCSA docs](https://google-calendar-simple-api.readthedocs.io/en/latest/getting_started.html)
- Create a `config.yml` (see `config.example.yml`) and `creds.json` (for the OAuth JSON credentials)
- Optionnaly, start GCSA to obtain a `token.pickle` file if your server is headless
- Install dependencies and run `app.py`

## License

Licensed under MIT. See the `LICENSE` file.