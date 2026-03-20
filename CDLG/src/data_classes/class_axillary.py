from enum import Enum


class InfoTypes(Enum):
    drift_info = "drift:info"
    noise_info = "noise:info"


class DriftTypes(Enum):
    sudden = 'sudden'
    gradual = 'gradual'
    recurring = 'recurring'
    incremental = 'incremental'


class ChangeTypes(Enum):
    sudden = 'sudden'
    gradual = 'gradual'


class TraceAttributes(Enum):
    concept_name = "concept:name"
    timestamp = "time:timestamp"
    model_version = "model_version:id"
