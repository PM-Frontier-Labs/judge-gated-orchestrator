"""Plan.yaml schema validation."""
from typing import Dict, Any, List
from pathlib import Path


def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """
    Validate plan.yaml structure and contents.

    Returns list of validation errors (empty = valid).
    """
    errors = []

    # Check top-level structure
    if "plan" not in plan:
        errors.append("Missing required top-level key: 'plan'")
        return errors  # Can't continue without plan key

    plan_config = plan["plan"]

    # Validate required fields
    if "id" not in plan_config:
        errors.append("Missing required field: plan.id")
    elif not isinstance(plan_config["id"], str) or not plan_config["id"].strip():
        errors.append("plan.id must be a non-empty string")

    if "summary" not in plan_config:
        errors.append("Missing required field: plan.summary")
    elif not isinstance(plan_config["summary"], str):
        errors.append("plan.summary must be a string")

    if "phases" not in plan_config:
        errors.append("Missing required field: plan.phases")
        return errors  # Can't continue without phases

    if not isinstance(plan_config["phases"], list):
        errors.append("plan.phases must be a list")
        return errors

    if len(plan_config["phases"]) == 0:
        errors.append("plan.phases must contain at least one phase")
        return errors

    # Validate optional fields
    if "base_branch" in plan_config and not isinstance(plan_config["base_branch"], str):
        errors.append("plan.base_branch must be a string")

    if "test_command" in plan_config:
        tc = plan_config["test_command"]
        if not isinstance(tc, (str, dict)):
            errors.append("plan.test_command must be a string or dict")
        elif isinstance(tc, dict) and "command" not in tc:
            errors.append("plan.test_command dict must have 'command' key")

    if "lint_command" in plan_config:
        lc = plan_config["lint_command"]
        if not isinstance(lc, (str, dict)):
            errors.append("plan.lint_command must be a string or dict")
        elif isinstance(lc, dict) and "command" not in lc:
            errors.append("plan.lint_command dict must have 'command' key")

    # Validate LLM review config
    if "llm_review_config" in plan_config:
        llm_config = plan_config["llm_review_config"]
        if not isinstance(llm_config, dict):
            errors.append("plan.llm_review_config must be a dict")
        else:
            # Check known fields
            if "model" in llm_config and not isinstance(llm_config["model"], str):
                errors.append("plan.llm_review_config.model must be a string")

            if "max_tokens" in llm_config and not isinstance(llm_config["max_tokens"], int):
                errors.append("plan.llm_review_config.max_tokens must be an integer")

            if "temperature" in llm_config:
                if not isinstance(llm_config["temperature"], (int, float)):
                    errors.append("plan.llm_review_config.temperature must be a number")
                elif not 0 <= llm_config["temperature"] <= 1:
                    errors.append("plan.llm_review_config.temperature must be between 0 and 1")

            if "timeout_seconds" in llm_config and not isinstance(llm_config["timeout_seconds"], int):
                errors.append("plan.llm_review_config.timeout_seconds must be an integer")

            if "budget_usd" in llm_config:
                if llm_config["budget_usd"] is not None and not isinstance(llm_config["budget_usd"], (int, float)):
                    errors.append("plan.llm_review_config.budget_usd must be a number or null")

            if "fail_on_transport_error" in llm_config and not isinstance(llm_config["fail_on_transport_error"], bool):
                errors.append("plan.llm_review_config.fail_on_transport_error must be a boolean")

            if "include_extensions" in llm_config:
                if not isinstance(llm_config["include_extensions"], list):
                    errors.append("plan.llm_review_config.include_extensions must be a list")
                elif not all(isinstance(x, str) for x in llm_config["include_extensions"]):
                    errors.append("plan.llm_review_config.include_extensions must contain only strings")

            if "exclude_patterns" in llm_config:
                if not isinstance(llm_config["exclude_patterns"], list):
                    errors.append("plan.llm_review_config.exclude_patterns must be a list")
                elif not all(isinstance(x, str) for x in llm_config["exclude_patterns"]):
                    errors.append("plan.llm_review_config.exclude_patterns must contain only strings")

    # Validate protocol_lock
    if "protocol_lock" in plan_config:
        lock = plan_config["protocol_lock"]
        if not isinstance(lock, dict):
            errors.append("plan.protocol_lock must be a dict")
        else:
            if "protected_globs" in lock:
                if not isinstance(lock["protected_globs"], list):
                    errors.append("plan.protocol_lock.protected_globs must be a list")
                elif not all(isinstance(x, str) for x in lock["protected_globs"]):
                    errors.append("plan.protocol_lock.protected_globs must contain only strings")
                elif any(not x.strip() for x in lock["protected_globs"]):
                    errors.append("plan.protocol_lock.protected_globs cannot contain empty strings")

            if "allow_in_phases" in lock:
                if not isinstance(lock["allow_in_phases"], list):
                    errors.append("plan.protocol_lock.allow_in_phases must be a list")
                elif not all(isinstance(x, str) for x in lock["allow_in_phases"]):
                    errors.append("plan.protocol_lock.allow_in_phases must contain only strings")

    # Validate each phase
    phase_ids = set()
    for i, phase in enumerate(plan_config["phases"]):
        phase_prefix = f"plan.phases[{i}]"

        if not isinstance(phase, dict):
            errors.append(f"{phase_prefix} must be a dict")
            continue

        # Required phase fields
        if "id" not in phase:
            errors.append(f"{phase_prefix}.id is required")
        elif not isinstance(phase["id"], str) or not phase["id"].strip():
            errors.append(f"{phase_prefix}.id must be a non-empty string")
        else:
            # Check for duplicate phase IDs
            if phase["id"] in phase_ids:
                errors.append(f"Duplicate phase ID: {phase['id']}")
            phase_ids.add(phase["id"])

        if "description" not in phase:
            errors.append(f"{phase_prefix}.description is required")
        elif not isinstance(phase["description"], str):
            errors.append(f"{phase_prefix}.description must be a string")

        # Validate scope
        if "scope" in phase:
            scope = phase["scope"]
            if not isinstance(scope, dict):
                errors.append(f"{phase_prefix}.scope must be a dict")
            else:
                if "include" in scope:
                    if not isinstance(scope["include"], list):
                        errors.append(f"{phase_prefix}.scope.include must be a list")
                    elif not all(isinstance(x, str) for x in scope["include"]):
                        errors.append(f"{phase_prefix}.scope.include must contain only strings")
                    elif any(not x.strip() for x in scope["include"]):
                        errors.append(f"{phase_prefix}.scope.include cannot contain empty strings")

                if "exclude" in scope:
                    if not isinstance(scope["exclude"], list):
                        errors.append(f"{phase_prefix}.scope.exclude must be a list")
                    elif not all(isinstance(x, str) for x in scope["exclude"]):
                        errors.append(f"{phase_prefix}.scope.exclude must contain only strings")

        # Validate artifacts
        if "artifacts" in phase:
            artifacts = phase["artifacts"]
            if not isinstance(artifacts, dict):
                errors.append(f"{phase_prefix}.artifacts must be a dict")
            else:
                if "must_exist" in artifacts:
                    if not isinstance(artifacts["must_exist"], list):
                        errors.append(f"{phase_prefix}.artifacts.must_exist must be a list")
                    elif not all(isinstance(x, str) for x in artifacts["must_exist"]):
                        errors.append(f"{phase_prefix}.artifacts.must_exist must contain only strings")
                    elif any(not x.strip() for x in artifacts["must_exist"]):
                        errors.append(f"{phase_prefix}.artifacts.must_exist cannot contain empty strings")

        # Validate gates
        if "gates" in phase:
            gates = phase["gates"]
            if not isinstance(gates, dict):
                errors.append(f"{phase_prefix}.gates must be a dict")
            else:
                # Define valid gate names
                valid_gates = {"tests", "lint", "integrity", "docs", "drift", "llm_review"}
                unknown_gates = set(gates.keys()) - valid_gates
                if unknown_gates:
                    errors.append(f"{phase_prefix}.gates contains unknown gates: {', '.join(sorted(unknown_gates))}")

                # Validate tests gate
                if "tests" in gates:
                    tests_gate = gates["tests"]
                    if not isinstance(tests_gate, dict):
                        errors.append(f"{phase_prefix}.gates.tests must be a dict")
                    else:
                        if "must_pass" in tests_gate and not isinstance(tests_gate["must_pass"], bool):
                            errors.append(f"{phase_prefix}.gates.tests.must_pass must be a boolean")

                        if "test_scope" in tests_gate:
                            if tests_gate["test_scope"] not in ["scope", "all"]:
                                errors.append(f"{phase_prefix}.gates.tests.test_scope must be 'scope' or 'all'")

                        if "quarantine" in tests_gate:
                            if not isinstance(tests_gate["quarantine"], list):
                                errors.append(f"{phase_prefix}.gates.tests.quarantine must be a list")
                            else:
                                for j, q in enumerate(tests_gate["quarantine"]):
                                    if not isinstance(q, dict):
                                        errors.append(f"{phase_prefix}.gates.tests.quarantine[{j}] must be a dict")
                                    else:
                                        if "path" not in q:
                                            errors.append(f"{phase_prefix}.gates.tests.quarantine[{j}].path is required")
                                        elif not isinstance(q["path"], str):
                                            errors.append(f"{phase_prefix}.gates.tests.quarantine[{j}].path must be a string")

                                        if "reason" not in q:
                                            errors.append(f"{phase_prefix}.gates.tests.quarantine[{j}].reason is required")
                                        elif not isinstance(q["reason"], str):
                                            errors.append(f"{phase_prefix}.gates.tests.quarantine[{j}].reason must be a string")

                # Validate lint gate
                if "lint" in gates:
                    lint_gate = gates["lint"]
                    if not isinstance(lint_gate, dict):
                        errors.append(f"{phase_prefix}.gates.lint must be a dict")
                    elif "must_pass" in lint_gate and not isinstance(lint_gate["must_pass"], bool):
                        errors.append(f"{phase_prefix}.gates.lint.must_pass must be a boolean")

                # Validate integrity gate
                if "integrity" in gates:
                    integrity_gate = gates["integrity"]
                    if not isinstance(integrity_gate, dict):
                        errors.append(f"{phase_prefix}.gates.integrity must be a dict")
                    elif "must_pass" in integrity_gate and not isinstance(integrity_gate["must_pass"], bool):
                        errors.append(f"{phase_prefix}.gates.integrity.must_pass must be a boolean")

                # Validate docs gate
                if "docs" in gates:
                    docs_gate = gates["docs"]
                    if not isinstance(docs_gate, dict):
                        errors.append(f"{phase_prefix}.gates.docs must be a dict")
                    else:
                        if "must_update" in docs_gate:
                            if not isinstance(docs_gate["must_update"], list):
                                errors.append(f"{phase_prefix}.gates.docs.must_update must be a list")
                            elif not all(isinstance(x, str) for x in docs_gate["must_update"]):
                                errors.append(f"{phase_prefix}.gates.docs.must_update must contain only strings")

                # Validate drift gate
                if "drift" in gates:
                    drift_gate = gates["drift"]
                    if not isinstance(drift_gate, dict):
                        errors.append(f"{phase_prefix}.gates.drift must be a dict")
                    else:
                        if "allowed_out_of_scope_changes" in drift_gate:
                            if not isinstance(drift_gate["allowed_out_of_scope_changes"], int):
                                errors.append(f"{phase_prefix}.gates.drift.allowed_out_of_scope_changes must be an integer")
                            elif drift_gate["allowed_out_of_scope_changes"] < 0:
                                errors.append(f"{phase_prefix}.gates.drift.allowed_out_of_scope_changes must be non-negative")

                # Validate llm_review gate
                if "llm_review" in gates:
                    llm_gate = gates["llm_review"]
                    if not isinstance(llm_gate, dict):
                        errors.append(f"{phase_prefix}.gates.llm_review must be a dict")
                    elif "enabled" in llm_gate and not isinstance(llm_gate["enabled"], bool):
                        errors.append(f"{phase_prefix}.gates.llm_review.enabled must be a boolean")

        # Validate drift_rules
        if "drift_rules" in phase:
            drift_rules = phase["drift_rules"]
            if not isinstance(drift_rules, dict):
                errors.append(f"{phase_prefix}.drift_rules must be a dict")
            else:
                if "forbid_changes" in drift_rules:
                    if not isinstance(drift_rules["forbid_changes"], list):
                        errors.append(f"{phase_prefix}.drift_rules.forbid_changes must be a list")
                    elif not all(isinstance(x, str) for x in drift_rules["forbid_changes"]):
                        errors.append(f"{phase_prefix}.drift_rules.forbid_changes must contain only strings")
                    elif any(not x.strip() for x in drift_rules["forbid_changes"]):
                        errors.append(f"{phase_prefix}.drift_rules.forbid_changes cannot contain empty strings")

    return errors


def validate_plan_file(plan_path: Path) -> List[str]:
    """
    Validate plan.yaml file.

    Returns list of validation errors (empty = valid).
    """
    if not plan_path.exists():
        return [f"Plan file not found: {plan_path}"]

    try:
        import yaml
        plan = yaml.safe_load(plan_path.read_text())
    except Exception as e:
        return [f"Failed to parse plan.yaml: {e}"]

    if not isinstance(plan, dict):
        return ["plan.yaml must contain a dict at top level"]

    return validate_plan(plan)
