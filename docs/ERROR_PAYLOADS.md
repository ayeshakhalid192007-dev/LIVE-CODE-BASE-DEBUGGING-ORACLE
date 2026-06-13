# Error Payload Examples

Sample error payloads from different monitoring systems that git-debug-oracle accepts.

## Generic Error Payload (Minimal)

Smallest valid payload:

```json
{
  "file_path": "src/app.py",
  "line_number": 42
}
```

With additional context:

```json
{
  "file_path": "src/app.py",
  "line_number": 42,
  "function_name": "process_data",
  "error_type": "ValueError",
  "error_message": "invalid input format",
  "stacktrace": "Traceback (most recent call last):\n  ..."
}
```

## Python Error

```json
{
  "file_path": "src/handlers/user_handler.py",
  "line_number": 156,
  "function_name": "create_user",
  "error_type": "IndexError",
  "error_message": "list index out of range",
  "stacktrace": "Traceback (most recent call last):\n  File \"src/handlers/user_handler.py\", line 156, in create_user\n    user_id = user_ids[index]\n  File \"src/utils/validation.py\", line 42, in validate\n    return process(data)\nIndexError: list index out of range",
  "language": "python"
}
```

## JavaScript/Node.js Error

```json
{
  "file_path": "api/routes/auth.js",
  "line_number": 89,
  "function_name": "authenticateUser",
  "error_type": "TypeError",
  "error_message": "Cannot read property 'email' of undefined",
  "stacktrace": "TypeError: Cannot read property 'email' of undefined\n    at authenticateUser (api/routes/auth.js:89:10)\n    at processRequest (api/middleware/auth.js:42:5)\n    at Router.use (api/server.js:15:3)",
  "language": "javascript"
}
```

## Java Error

```json
{
  "file_path": "com/example/service/UserService.java",
  "line_number": 234,
  "function_name": "findUserById",
  "error_type": "NullPointerException",
  "error_message": "Cannot invoke method on null object",
  "stacktrace": "java.lang.NullPointerException\n    at com.example.service.UserService.findUserById(UserService.java:234)\n    at com.example.controller.UserController.getUser(UserController.java:45)\n    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)",
  "language": "java"
}
```

## Go Error

```json
{
  "file_path": "pkg/handlers/api.go",
  "line_number": 156,
  "function_name": "HandleRequest",
  "error_type": "panic",
  "error_message": "runtime error: index out of range",
  "stacktrace": "panic: runtime error: index out of range [10] with length 5\n\ngoroutine 1 [running]:\nmain.HandleRequest()\n    /path/to/pkg/handlers/api.go:156 +0x1c4\nmain.main()\n    /path/to/main.go:42 +0x44",
  "language": "go"
}
```

## Sentry Error Format

```json
{
  "file_path": "app/views.py",
  "line_number": 127,
  "function_name": "get_user_profile",
  "error_type": "AttributeError",
  "error_message": "'NoneType' object has no attribute 'profile'",
  "stacktrace": "Traceback (most recent call last):\n  File \"app/views.py\", line 127, in get_user_profile\n    profile = user.profile\nAttributeError: 'NoneType' object has no attribute 'profile'",
  "language": "python",
  "additional_context": {
    "sentry_event_id": "abc123def456",
    "environment": "production",
    "release": "1.2.3"
  }
}
```

## Datadog Error Format

```json
{
  "file_path": "src/services/payment.py",
  "line_number": 89,
  "function_name": "process_payment",
  "error_type": "ConnectionError",
  "error_message": "Failed to connect to payment gateway",
  "stacktrace": "Traceback...",
  "language": "python",
  "additional_context": {
    "service": "payment-api",
    "host": "prod-server-01",
    "dd_trace_id": "xyz789",
    "user_id": "user_12345"
  }
}
```

## CloudWatch Error Format

```json
{
  "file_path": "lambda/index.js",
  "line_number": 45,
  "function_name": "handler",
  "error_type": "Error",
  "error_message": "Unable to invoke Lambda function",
  "stacktrace": "Error: Unable to invoke Lambda function\n    at Object.handler (lambda/index.js:45:10)",
  "language": "javascript",
  "additional_context": {
    "log_group": "/aws/lambda/my-function",
    "log_stream": "2026/06/13/[$LATEST]abc123",
    "request_id": "req-12345-67890"
  }
}
```

## Custom Monitoring System Error

```json
{
  "file_path": "modules/database/query.py",
  "line_number": 203,
  "function_name": "execute_query",
  "error_type": "DatabaseError",
  "error_message": "Query timeout after 30 seconds",
  "stacktrace": "Traceback (most recent call last):\n  File \"modules/database/query.py\", line 203, in execute_query\n    result = db.execute(sql, timeout=30)\nDatabaseError: Query timeout after 30 seconds",
  "language": "python",
  "additional_context": {
    "query": "SELECT * FROM large_table WHERE ...",
    "duration_ms": 30000,
    "error_code": "TIMEOUT_ERROR"
  }
}
```

## Webhook Format

POST request body:

```bash
curl -X POST http://localhost:8000/webhook/error \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=<signature>" \
  -d '{
    "file_path": "src/app.py",
    "line_number": 42,
    "function_name": "main",
    "error_type": "ValueError",
    "error_message": "invalid value",
    "stacktrace": "...",
    "language": "python"
  }'
```

## Response Format

Webhook returns:

```json
{
  "error_context": {
    "file_path": "src/app.py",
    "line_number": 42,
    "function_name": "main",
    "error_type": "ValueError",
    "error_message": "invalid value"
  },
  "retrieval_results": [
    {
      "rank": 1,
      "file_path": "src/app.py",
      "start_line": 38,
      "end_line": 48,
      "code_snippet": "def main():\n    try:\n        value = int(user_input)\n    except ValueError as e:\n        logger.error(e)",
      "commit_hash": "abc123def456",
      "commit_author": "John Doe",
      "commit_timestamp": "2026-06-13T12:00:00Z",
      "function_name": "main",
      "original_score": 0.92,
      "recency_score": 0.95,
      "final_score": 0.876
    }
  ],
  "fix_proposal": {
    "root_cause": "Missing validation for empty input",
    "affected_file": "src/app.py",
    "affected_lines": [38, 48],
    "code_patch": "value = int(user_input or '0')",
    "patch_language": "python",
    "confidence": 0.85,
    "explanation": "The error occurs when user_input is None or empty. Adding a default value of '0' ensures int() always receives a valid string.",
    "affected_functions": ["main"],
    "root_cause_category": "validation"
  },
  "related_diffs": [],
  "metadata": {
    "query_used": "ValueError invalid input main",
    "total_chunks_searched": 1247,
    "search_duration_ms": 342,
    "timestamp": "2026-06-13T12:25:46Z"
  }
}
```

## Integration Examples

### Sentry Integration

Forward Sentry errors via webhook:

1. Go to Project Settings → Integrations
2. Enable "Outgoing Webhooks"
3. Add URL: `http://your-server:8000/webhook/error`
4. Select events: `error`, `fatal`

### Datadog Integration

Create Datadog monitor with webhook:

```bash
# In Datadog Monitor UI:
# Notification: @webhook-git-debug-oracle
# Custom payload: (use Generic Error Payload format above)
```

### CloudWatch Integration

Create Lambda to forward errors:

```python
import json
import requests

def lambda_handler(event, context):
    # Parse CloudWatch Logs
    message = json.loads(event['awslogs']['data'])
    
    # Extract error info and send to git-debug-oracle
    payload = {
        "file_path": "...",
        "line_number": "...",
        "error_message": "...",
        "stacktrace": "..."
    }
    
    requests.post('http://your-server:8000/webhook/error', json=payload)
    
    return {'statusCode': 200}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file_path | string | Yes | Path to file where error occurred |
| line_number | integer | Yes | Line number in file |
| function_name | string | No | Function where error occurred |
| error_type | string | No | Exception/error type (ValueError, TypeError, etc.) |
| error_message | string | No | Error message text |
| stacktrace | string | No | Full stacktrace (string or list of strings) |
| language | string | No | Programming language (python, javascript, java, go) |
| additional_context | object | No | Extra context (monitoring system metadata) |
