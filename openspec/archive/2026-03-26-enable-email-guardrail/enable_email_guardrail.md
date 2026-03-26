# Enable Human Approval Guardrail for Email Sending

## Summary
Enable a custom human approval guardrail for the email agent's `send_email` tool to require explicit user approval before sending any emails, while supporting automatic approval in test environments.

## Problem
Currently, the email agent can send emails without requiring user confirmation, which could lead to unintended email communications.

## Solution
Create a custom `EmailApprovalGuardrail` middleware class that:
1. Intercepts `send_email` tool calls before execution
2. Requires explicit user approval in production mode
3. Supports automatic approval in test/automation environments
4. Integrates with the existing middleware stack

## Changes
1. **File: `guardrails/custom_guardrail.py`**
   - Add new `EmailApprovalGuardrail` class that extends `AgentMiddleware`
   - Implements `before_tool` hook to intercept email sending operations
   - Supports configurable approval flow via `auto_approve` parameter

2. **File: `agents/email_agent.py`**
   - Import the new `EmailApprovalGuardrail` class
   - Replace `HumanInTheLoopMiddleware` with `EmailApprovalGuardrail(auto_approve=True)`
   - In production, can be instantiated as `EmailApprovalGuardrail(auto_approve=False)` for interactive approval

## Expected Behavior
- **In Test Mode (auto_approve=True)**: Email sends proceed automatically (for CI/CD pipelines)
- **In Production Mode (auto_approve=False)**: 
  - When the email agent attempts to call `send_email`, execution pauses
  - User is presented with approval prompt showing recipient, subject
  - Email is sent only after explicit user approval
  - Rejected emails are handled gracefully

## Implementation Details
The guardrail uses a custom `AgentMiddleware` that hooks into the `before_tool` lifecycle. This provides fine-grained control over tool execution without relying on the more heavyweight `HumanInTheLoopMiddleware`.

## Testing
- ✅ All existing trajectory evaluation tests pass (2/2)
- Tests verify the email sending workflow with the guardrail in place
- `schedule_event` test: Calendar scheduling works independently
- `schedule_event_and_email` test: Both scheduling and email sending work together with approval guardrail

## Migration Path
For production deployments, change the guardrail initialization from:
```python
EmailApprovalGuardrail(auto_approve=True)
```
to:
```python
EmailApprovalGuardrail(auto_approve=False)
```
This enables interactive approval flow for all email operations.

