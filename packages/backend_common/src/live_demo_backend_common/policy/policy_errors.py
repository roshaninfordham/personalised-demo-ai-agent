class PolicyError(Exception):
    code = "policy_error"


class PermissionDeniedError(PolicyError):
    code = "missing_required_permission"

    def __init__(self, permission: str) -> None:
        super().__init__("Missing required permission.")
        self.permission = permission


class PolicyConfigurationError(PolicyError):
    code = "policy_configuration_error"
