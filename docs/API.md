# API Documentation: Autonomous Web Agent

This API manages the execution lifecycles of the Autonomous Web Agent. It is built using FastAPI and communicates via JSON.

---

## ⚡ Summary of Endpoints

| Endpoint | Method | Owner | Description |
| :--- | :--- | :--- | :--- |
| [`/plan`](#post-plan) | `POST` | Member A | Accepts a user request and compiles it into an ordered execution plan. |
| [`/browse`](#post-browse) | `POST` | Member B | Executes navigation, clicks, and scrolls using Playwright. |
| [`/process`](#post-process) | `POST` | Member C | Cleans DOM, strips boilerplate, converts to Markdown, and extracts entities. |
| [`/verify`](#post-verify) | `POST` | Member C | Compares assertions across sources, calculates confidence scores. |
| [`/health`](#get-health) | `GET` | Member A | Evaluates system status, Playwright installation, and API connectivity. |

---

## 📌 POST /plan

Accepts user prompt and converts it into a structured set of navigation execution instructions.

* **URL**: `/api/v1/plan`
* **Headers**: `Content-Type: application/json`

### Request Schema

```json
{
  "query": "Compare prices of the Kindle Paperwhite 16GB on Amazon and Best Buy",
  "max_steps": 5,
  "options": {
    "prefer_direct_sources": true
  }
}
```

* `query` (str): Raw target objective from the user.
* `max_steps` (int, optional): Boundary limit on step count. Defaults to 5.
* `options` (dict, optional): Context configuration options.

### Response Schema (200 OK)

```json
{
  "goal_id": "goal_8f2d61a2",
  "structured_goal": {
    "objective": "Compare prices of Kindle Paperwhite 16GB",
    "constraints": ["Exclude marketplace third-party sellers", "Amazon US only", "Best Buy US only"]
  },
  "steps": [
    {
      "step_id": 1,
      "action": "navigate",
      "url": "https://www.amazon.com",
      "description": "Navigate to Amazon homepage and search for Kindle Paperwhite 16GB"
    },
    {
      "step_id": 2,
      "action": "navigate",
      "url": "https://www.bestbuy.com",
      "description": "Navigate to Best Buy homepage and search for Kindle Paperwhite 16GB"
    }
  ]
}
```

* `goal_id` (str): Unique UUID tracking the search transaction.
* `structured_goal` (object): Parsed goals and constraints.
* `steps` (array): List of planned navigation items.

### Status Codes
* `200 OK`: Plan compiled successfully.
* `400 Bad Request`: Query was blank or failed schema constraints.
* `500 Internal Server Error`: LLM reasoning failed.

---

## 📌 POST /browse

Invokes the Playwright module to run a specific navigation, click, or scroll step.

* **URL**: `/api/v1/browse`
* **Headers**: `Content-Type: application/json`

### Request Schema

```json
{
  "goal_id": "goal_8f2d61a2",
  "step": {
    "step_id": 1,
    "action": "navigate",
    "url": "https://www.amazon.com/s?k=Kindle+Paperwhite+16GB",
    "description": "Navigate to product search results"
  },
  "browser_config": {
    "headless": true,
    "timeout_ms": 30000
  }
}
```

### Response Schema (200 OK)

```json
{
  "step_id": 1,
  "status": "success",
  "url": "https://www.amazon.com/s?k=Kindle+Paperwhite+16GB",
  "raw_html": "<html><body><div id='dp'>Kindle Paperwhite...</div></body></html>",
  "screenshot_path": "/artifacts/screenshots/goal_8f2d61a2_step1.webp",
  "error_message": null
}
```

* `status` (str): Indicates outcome (`success`, `failed`, `timeout`).
* `raw_html` (str): Full raw page DOM source.
* `screenshot_path` (str): Reference path to the saved visual viewport check.

### Status Codes
* `200 OK`: Step executed. Note that if the selector wasn't found but page loaded, status is 200 with status="failed".
* `400 Bad Request`: Malformed step request.
* `504 Gateway Timeout`: Page load timed out beyond config boundaries.

---

## 📌 POST /process

Cleans raw DOM markup and converts to clean Markdown. Then performs entity extraction.

* **URL**: `/api/v1/process`
* **Headers**: `Content-Type: application/json`

### Request Schema

```json
{
  "goal_id": "goal_8f2d61a2",
  "step_id": 1,
  "raw_html": "<html><body><script>...</script><div id='dp'>Kindle Paperwhite 16GB - Price: $149.99</div></body></html>",
  "extraction_keys": ["price", "availability", "model_number"]
}
```

### Response Schema (200 OK)

```json
{
  "step_id": 1,
  "cleaned_markdown": "Kindle Paperwhite 16GB - Price: $149.99",
  "entities": {
    "price": "$149.99",
    "availability": "In Stock",
    "model_number": "B09TWDYSVP"
  }
}
```

* `cleaned_markdown` (str): Pure text content output by MarkItDown with boilerplate removed.
* `entities` (dict): Extracted property-value pairs based on extraction requests.

### Status Codes
* `200 OK`: Processing and conversion completed.
* `422 Unprocessable Entity`: Input HTML could not be parsed.

---

## 📌 POST /verify

Verifies facts across multiple sources and scores confidence.

* **URL**: `/api/v1/verify`
* **Headers**: `Content-Type: application/json`

### Request Schema

```json
{
  "goal_id": "goal_8f2d61a2",
  "extracted_data": [
    {
      "source": "amazon.com",
      "entities": {
        "price": "$149.99",
        "model_number": "B09TWDYSVP"
      }
    },
    {
      "source": "bestbuy.com",
      "entities": {
        "price": "$149.99",
        "model_number": "B09TWDYSVP"
      }
    }
  ]
}
```

### Response Schema (200 OK)

```json
{
  "goal_id": "goal_8f2d61a2",
  "verified_entities": {
    "price": "$149.99",
    "model_number": "B09TWDYSVP"
  },
  "confidence_score": 1.0,
  "contradictions": [],
  "sources_consulted": ["amazon.com", "bestbuy.com"]
}
```

* `confidence_score` (float): Degree of cross-site agreement (0.0 to 1.0).
* `contradictions` (array): List of assertions that had conflicting values.

### Status Codes
* `200 OK`: Verification complete.
* `400 Bad Request`: Insufficient data entries to verify.

---

## 📌 GET /health

Returns basic health diagnostics of backend modules and browser binaries.

* **URL**: `/api/v1/health`

### Response Schema (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2026-08-18T11:14:23Z",
  "services": {
    "database": "connected",
    "playwright": "available",
    "llm_api": "accessible"
  }
}
```

### Status Codes
* `200 OK`: System is ready.
* `503 Service Unavailable`: Playwright executable is missing or database is down.
