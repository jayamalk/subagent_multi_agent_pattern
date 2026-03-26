# Tasks - Enable Email Guardrail

## Implementation

- [x] Create EmailApprovalGuardrail middleware class
- [x] Add auto_approve flag to guardrail with environment config
- [x] Import guardrail into email_agent
- [x] Update email agent to use guardrail
- [x] Add EMAIL_GUARDRAIL_AUTO_APPROVE to .env file

## Testing

- [x] Update existing tests to verify guardrail execution
- [x] Create conftest.py for test environment setup
- [x] Verify all trajectory evaluation tests pass (2/2)
- [x] Verify schedule_event test (no guardrail trigger)
- [x] Verify schedule_event_and_email test (guardrail triggers)

## Configuration

- [x] Add get_email_guardrail_auto_approve() to ollama_config.py
- [x] Read EMAIL_GUARDRAIL_AUTO_APPROVE from .env with default false
- [x] Document production vs test mode configuration

## Documentation

- [x] Create OpenSpec change documentation
- [x] Document guardrail behavior and migration path
- [x] Update email_agent.py comments

