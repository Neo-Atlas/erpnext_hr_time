from hr_time.api.flextime.break_time import BreakTimeRepository
from hr_time.api.flextime.definition import FlextimeDefinitionRepository


def after_install():
    FlextimeDefinitionRepository().create_default()
    BreakTimeRepository().create_default()
