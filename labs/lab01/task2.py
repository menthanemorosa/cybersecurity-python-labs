users = {
    "cloud_architect": {"role": "cloud_security", "clearance": 4, "department": "Cloud", "active": True},
    "devops_engineer": {"role": "devops", "clearance": 3, "department": "DevOps", "active": True},
    "qa_tester": {"role": "quality_assurance", "clearance": 2, "department": "QA", "active": True},
    "partner_access": {"role": "partner", "clearance": 2, "department": "Partnership", "active": True},
    "migrated_user": {"role": "migrated", "clearance": 1, "department": "Migration", "active": False}
}

resources = [
    ("cloud_configs", 4), ("deployment_pipelines", 3), ("test_environments", 2),
    ("partner_apis", 2), ("infrastructure_code", 4), ("shared_resources", 1),
    ("container_registry", 3), ("secrets_vault", 4), ("build_artifacts", 2),
    ("public_endpoints", 1)
]

security_levels = ("Development", "Staging", "Production", "Critical Infrastructure")
blocked_users = {"migrated_user", "container_breach", "pipeline_compromise"}

def get_security_level(level: int) -> str:
    if 1 <= level <= len(security_levels):
        return security_levels[level - 1]
    return "Unknown"

def check_access(user: str, resource: str, resource_level: int) -> str:
    if user not in users:
        return f"user={user} resource={resource} -> DENY (User not found)"
    if user in blocked_users:
        return f"user={user} resource={resource} -> DENY (User is blocked)"
    if not users[user]["active"]:
        return f"user={user} resource={resource} -> DENY (Account inactive)"
    if users[user]["clearance"] >= resource_level:
        return f"user={user} resource={resource} -> ALLOW"
    return f"user={user} resource={resource} -> DENY (Insufficient clearance)"

print("📋 Список ресурсів:")
for res, lvl in resources:
    print(f"{res:<20} | {get_security_level(lvl)}")

print("\n🔐 Результати перевірки доступу:")
for user in users:
    for res, lvl in resources:
        print(check_access(user, res, lvl))
