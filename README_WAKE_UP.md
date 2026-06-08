# Streamlit App Keep-Alive

This repository includes a GitHub Actions workflow that periodically visits the
deployed Streamlit app so it does not hibernate from inactivity.

## What This Fixes

Streamlit Community Cloud hibernates apps after a period without traffic. The
workflow in `.github/workflows/wake_up_app.yml` runs every 6 hours, opens your
app, and clicks Streamlit's wake-up button if the app is already sleeping.

This greatly reduces manual restarts, but it is not the same as guaranteed
always-on hosting. GitHub scheduled jobs can be delayed or dropped during high
load, and scheduled workflows in inactive public repositories can be disabled
after 60 days without repository activity.

For a truly always-on production app, deploy to a host with an always-on process
or paid compute, such as Render, Railway, Fly.io, Azure App Service, AWS, GCP, or
a VPS.

## App URL

The workflow is already configured to wake this app:

```text
https://xai-caregiver-support.streamlit.app/
```

If the app URL changes later, update the `STREAMLIT_URL` value in
`.github/workflows/wake_up_app.yml`.

## How It Runs

The workflow runs at:

```text
17 */6 * * *
```

That means every 6 hours at minute 17 UTC. Minute 17 is used instead of minute 0
because GitHub Actions can be busier at the top of the hour.

You can also run it manually from:

```text
GitHub repository -> Actions -> Keep Streamlit App Awake -> Run workflow
```

## Files

```text
.github/workflows/wake_up_app.yml
.github/scripts/wake_up_app.py
.github/logs/.gitkeep
```

Workflow logs are uploaded as GitHub Actions artifacts after each run.
