from hr_time.api.flextime.break_time import BreakTimeRepository


def after_install():
    BreakTimeRepository().create_default()
