"""Plan.yaml schema validation."""
from typing import Dict, Any, List
from pathlib import Path


def _validate_top_level(plan: Dict[str, Any]) -> List[str]:
    """Validate top-level plan structure and required fields."""
    errors = []
    
    if "plan" not in plan:
        errors.append("Missing required top-level key: 'plan'")
        return errors
    
    plan_config = plan["plan"]
    
    # Required fields
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
    elif not isinstance(plan_config["phases"], list):
        errors.append("plan.phases must be a list")
    elif len(plan_config["phases"]) == 0:
        errors.append("plan.phases must contain at least one phase")
    
    # Optional fields
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
    
    return errors


def _validate_llm_config(llm_config: Dict[str, Any]) -> List[str]:
    """Validate LLM review configuration."""
    errors = []
    
    if not isinstance(llm_config, dict):
        errors.append("plan.llm_review_config must be a dict")
        return errors
    
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
    
    return errors


def _validate_protocol_lock(lock: Dict[str, Any]) -> List[str]:
    """Validate protocol lock configuration."""
    errors = []
    
    if not isinstance(lock, dict):
        errors.append("plan.protocol_lock must be a dict")
        return errors
    
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
    
    return errors


def _validate_phases(phases: List[Dict[str, Any]]) -> List[str]:
    """Validate phase definitions."""
    errors = []
    phase_ids = set()
    
    for i, phase in enumerate(phases):
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
            if phase["id"] in phase_ids:
                errors.append(f"Duplicate phase ID: {phase['id']}")
            phase_ids.add(phase["id"])
        
        if "description" not in phase:
            errors.append(f"{phase_prefix}.description is required")
        elif not isinstance(phase["description"], str):
            errors.append(f"{phase_prefix}.description must be a string")
        
        # Validate scope
        if "scope" in phase:
            errors.extend(_validate_scope(phase["scope"], phase_prefix))
        
        # Validate artifacts
        if "artifacts" in phase:
            errors.extend(_validate_artifacts(phase["artifacts"], phase_prefix))
        
        # Validate gates
        if "gates" in phase:
            errors.extend(_validate_gates(phase["gates"], phase_prefix))
        
        # Validate drift_rules
        if "drift_rules" in phase:
            errors.extend(_validate_drift_rules(phase["drift_rules"], phase_prefix))
    
    return errors


def _validate_scope(scope: Dict[str, Any], prefix: str) -> List[str]:
    """Validate phase scope configuration."""
    errors = []
    
    if not isinstance(scope, dict):
        errors.append(f"{prefix}.scope must be a dict")
        return errors
    
    if "include" in scope:
        if not isinstance(scope["include"], list):
            errors.append(f"{prefix}.scope.include must be a list")
        elif not all(isinstance(x, str) for x in scope["include"]):
            errors.append(f"{prefix}.scope.include must contain only strings")
        elif any(not x.strip() for x in scope["include"]):
            errors.append(f"{prefix}.scope.include cannot contain empty strings")
    
    if "exclude" in scope:
        if not isinstance(scope["exclude"], list):
            errors.append(f"{prefix}.scope.exclude must be a list")
        elif not all(isinstance(x, str) for x in scope["exclude"]):
            errors.append(f"{prefix}.scope.exclude must contain only strings")
    
    return errors


def _validate_artifacts(artifacts: Dict[str, Any], prefix: str) -> List[str]:
    """Validate phase artifacts configuration."""
    errors = []
    
    if not isinstance(artifacts, dict):
        errors.append(f"{prefix}.artifacts must be a dict")
        return errors
    
    if "must_exist" in artifacts:
        if not isinstance(artifacts["must_exist"], list):
            errors.append(f"{prefix}.artifacts.must_exist must be a list")
        elif not all(isinstance(x, str) for x in artifacts["must_exist"]):
            errors.append(f"{prefix}.artifacts.must_exist must contain only strings")
        elif any(not x.strip() for x in artifacts["must_exist"]):
            errors.append(f"{prefix}.artifacts.must_exist cannot contain empty strings")
    
    return errors


def _validate_gates(gates: Dict[str, Any], prefix: str) -> List[str]:
    """Validate phase gates configuration."""
    errors = []
    
    if not isinstance(gates, dict):
        errors.append(f"{prefix}.gates must be a dict")
        return errors
    
    valid_gates = {"tests", "lint", "docs", "drift", "llm_review"}
    unknown_gates = set(gates.keys()) - valid_gates
    if unknown_gates:
        errors.append(f"{prefix}.gates contains unknown gates: {', '.join(sorted(unknown_gates))}")
    
    # Validate tests gate
    if "tests" in gates:
        tests_gate = gates["tests"]
        if not isinstance(tests_gate, dict):
            errors.append(f"{prefix}.gates.tests must be a dict")
        else:
            if "must_pass" in tests_gate and not isinstance(tests_gate["must_pass"], bool):
                errors.append(f"{prefix}.gates.tests.must_pass must be a boolean")
            
            if "test_scope" in tests_gate:
                if tests_gate["test_scope"] not in ["scope", "all"]:
                    errors.append(f"{prefix}.gates.tests.test_scope must be 'scope' or 'all'")
            
            if "quarantine" in tests_gate:
                if not isinstance(tests_gate["quarantine"], list):
                    errors.append(f"{prefix}.gates.tests.quarantine must be a list")
                else:
                    for j, q in enumerate(tests_gate["quarantine"]):
                        if not isinstance(q, dict):
                            errors.append(f"{prefix}.gates.tests.quarantine[{j}] must be a dict")
                        else:
                            if "path" not in q:
                                errors.append(f"{prefix}.gates.tests.quarantine[{j}].path is required")
                            elif not isinstance(q["path"], str):
                                errors.append(f"{prefix}.gates.tests.quarantine[{j}].path must be a string")
                            
                            if "reason" not in q:
                                errors.append(f"{prefix}.gates.tests.quarantine[{j}].reason is required")
                            elif not isinstance(q["reason"], str):
                                errors.append(f"{prefix}.gates.tests.quarantine[{j}].reason must be a string")
    
    # Validate lint gate
    if "lint" in gates:
        lint_gate = gates["lint"]
        if not isinstance(lint_gate, dict):
            errors.append(f"{prefix}.gates.lint must be a dict")
        elif "must_pass" in lint_gate and not isinstance(lint_gate["must_pass"], bool):
            errors.append(f"{prefix}.gates.lint.must_pass must be a boolean")
    
    # Validate docs gate
    if "docs" in gates:
        docs_gate = gates["docs"]
        if not isinstance(docs_gate, dict):
            errors.append(f"{prefix}.gates.docs must be a dict")
        else:
            if "must_update" in docs_gate:
                if not isinstance(docs_gate["must_update"], list):
                    errors.append(f"{prefix}.gates.docs.must_update must be a list")
                elif not all(isinstance(x, str) for x in docs_gate["must_update"]):
                    errors.append(f"{prefix}.gates.docs.must_update must contain only strings")
    
    # Validate drift gate
    if "drift" in gates:
        drift_gate = gates["drift"]
        if not isinstance(drift_gate, dict):
            errors.append(f"{prefix}.gates.drift must be a dict")
        else:
            if "allowed_out_of_scope_changes" in drift_gate:
                if not isinstance(drift_gate["allowed_out_of_scope_changes"], int):
                    errors.append(f"{prefix}.gates.drift.allowed_out_of_scope_changes must be an integer")
                elif drift_gate["allowed_out_of_scope_changes"] < 0:
                    errors.append(f"{prefix}.gates.drift.allowed_out_of_scope_changes must be non-negative")
    
    # Validate llm_review gate
    if "llm_review" in gates:
        llm_gate = gates["llm_review"]
        if not isinstance(llm_gate, dict):
            errors.append(f"{prefix}.gates.llm_review must be a dict")
        elif "enabled" in llm_gate and not isinstance(llm_gate["enabled"], bool):
            errors.append(f"{prefix}.gates.llm_review.enabled must be a boolean")
    
    return errors


def _validate_drift_rules(drift_rules: Dict[str, Any], prefix: str) -> List[str]:
    """Validate drift rules configuration."""
    errors = []
    
    if not isinstance(drift_rules, dict):
        errors.append(f"{prefix}.drift_rules must be a dict")
        return errors
    
    if "forbid_changes" in drift_rules:
        if not isinstance(drift_rules["forbid_changes"], list):
            errors.append(f"{prefix}.drift_rules.forbid_changes must be a list")
        elif not all(isinstance(x, str) for x in drift_rules["forbid_changes"]):
            errors.append(f"{prefix}.drift_rules.forbid_changes must contain only strings")
        elif any(not x.strip() for x in drift_rules["forbid_changes"]):
            errors.append(f"{prefix}.drift_rules.forbid_changes cannot contain empty strings")
    
    return errors


def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """
    Validate plan.yaml structure and contents.

    Returns list of validation errors (empty = valid).
    """
    errors = []
    
    # Validate top-level structure
    errors.extend(_validate_top_level(plan))
    if "plan" not in plan:
        return errors  # Can't continue without plan key
    
    plan_config = plan["plan"]
    
    # Can't validate phases if they don't exist or are invalid
    if "phases" not in plan_config or not isinstance(plan_config.get("phases"), list) or len(plan_config.get("phases", [])) == 0:
        return errors
    
    # Validate LLM config
    if "llm_review_config" in plan_config:
        errors.extend(_validate_llm_config(plan_config["llm_review_config"]))
    
    # Validate protocol lock
    if "protocol_lock" in plan_config:
        errors.extend(_validate_protocol_lock(plan_config["protocol_lock"]))
    
    # Validate phases
    errors.extend(_validate_phases(plan_config["phases"]))
    
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
