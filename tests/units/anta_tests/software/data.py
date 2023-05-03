"""Test inputs for anta.tests.hardware"""

from typing import Any, Dict, List

INPUT_VERIFY_EOS_VERSION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            }
        ],
        "side_effect": ["4.27.0F", "4.28.0F"],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "modelName": "vEOS-lab",
                "internalVersion": "4.27.0F-24305004.4270F",
                "version": "4.27.0F",
            }
        ],
        "side_effect": ["4.27.1F"],
        "expected_result": "failure",
        "expected_messages": ["device is running version 4.27.0F not in expected versions: ['4.27.1F']"],
    },
]

INPUT_VERIFY_TERMINATTR_VERSION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1107543.52,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                    "switchType": "fixedSystem",
                    "packages": {
                        "TerminAttr-core": {"release": "1", "version": "v1.17.0"},
                    },
                },
            }
        ],
        "side_effect": ["v1.17.0", "v1.18.1"],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1107543.52,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                    "switchType": "fixedSystem",
                    "packages": {
                        "TerminAttr-core": {"release": "1", "version": "v1.17.0"},
                    },
                },
            }
        ],
        "side_effect": ["v1.17.1", "v1.18.1"],
        "expected_result": "failure",
        "expected_messages": ["device is running TerminAttr version v1.17.0 and is not in the allowed list: ['v1.17.1', 'v1.18.1']"],
    },
]

INPUT_VERIFY_EOS_EXTENSIONS: List[Dict[str, Any]] = [
    {
        "name": "success-no-extensions",
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": []},
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {"extensions": {}, "extensionStoredDir": "flash:", "warnings": ["No extensions are available"]},
            {"extensions": ["dummy"]},
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Missing EOS extensions: installed [] / configured: ['dummy']"],
    },
]

INPUT_FIELD_NOTICE_44_RESOLUTION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-4.0",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.0.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (4.0.1)"],
    },
    {
        "name": "failure-4.1",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.1.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (4.1.0)"],
    },
    {
        "name": "failure-6.0",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.0.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (6.0.1)"],
    },
    {
        "name": "failure-6.1",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.1.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (6.1.1)"],
    },
    {
        "name": "skipped-model",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["device is not impacted by FN044"],
    },
]
