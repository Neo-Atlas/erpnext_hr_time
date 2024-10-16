from . import __version__ as app_version

app_name = "hr_time"
app_title = "HR time management"
app_publisher = "AtlasAero GmbH"
app_description = "Time management module for HR"
app_email = "info@atlasaero.eu"
app_license = "MIT"

fixtures = ["Custom Field"]
app_include_css = ['hr_time.bundle.css']
app_include_js = ["hr_time.bundle.js"]

after_install = "hr_time.setup.install.after_install"

scheduler_events = {
    "hourly": [
        "hr_time.api.flextime.api.generate_daily_flextime_status"
    ],
}
