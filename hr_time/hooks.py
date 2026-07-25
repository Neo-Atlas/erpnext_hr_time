from . import __version__ as app_version

app_name = "hr_time"
app_title = "HR time management"
app_publisher = "AtlasAero GmbH"
app_description = "Time management module for HR"
app_email = "info@atlasaero.eu"
app_license = "MIT"

fixtures = [
    # 1. Custom fields on CORE doctypes only
    {
        "doctype": "Custom Field",
        "filters": [
            ["dt", "in", ["Task", "HR Settings", "Timesheet", "Timesheet Detail"]]
        ]
    },
    # 2. Label changes, mandatory changes, etc., on CORE doctypes
    {
        "doctype": "Property Setter",
        "filters": [
            ["doc_type", "in", ["Task", "HR Settings", "Timesheet", "Timesheet Detail"]]
        ]
    }
]

app_include_css = ['hr_time.bundle.css']
app_include_js = ["hr_time.bundle.js"]

after_install = "hr_time.setup.install.after_install"

doc_events = {
    "HR Settings": {
        "on_update": "hr_time.api.hr_settings.repository.clear_hr_settings_cache"
    }
}

scheduler_events = {
    "hourly": [
        "hr_time.api.flextime.api.generate_daily_flextime_status"
    ],
}
