Continue the existing flight booking wrapper project.

Important constraints:
- The project already has:
  - domain models / schemas
  - required dependencies
  - an existing hexagonal architecture
  - an existing flights search/list API
- Do NOT scaffold a new project.
- Do NOT create a parallel architecture.
- Do NOT regenerate models or dependencies unnecessarily.
- Do NOT rewrite the existing flights search endpoint from scratch unless required.
- Reuse the existing project structure, naming, modules, and patterns.

Goal:
Complete the take-home assignment by fitting the required functionality into the current hexagonal architecture.

Work only on the missing or incomplete parts.

Tasks:

1) Review and minimally refine the existing flights search flow
- Keep the existing endpoint if possible
- Improve only where needed:
  - normalize price
  - normalize datetime
  - map airline code to airline name
  - map cabin code to cabin name
  - compute stops
  - compute duration_minutes
  - enrich airport info if needed
  - add wrapper-side pagination if upstream does not support it
- Keep business logic out of controllers

2) Implement or complete offer detail flow
- Integrate legacy GET /api/v2/offer/{offer_id}
- Return a clean frontend-friendly response including:
  - fare rules / ticket conditions
  - baggage
  - change policy
  - refund policy
  - airline labels
  - normalized dates
- Put mapping/transformation logic in the appropriate application/service/mapper layer according to the existing hexagonal architecture

3) Implement or complete booking creation flow
- Integrate legacy POST /booking/create
- Validate request before calling upstream
- Input should support:
  - offer_id
  - contact
  - passengers
- Return normalized response:
  - booking_reference
  - status
  - summary
- Reuse existing request/response models where possible

4) Implement or complete booking retrieval flow
- Integrate legacy GET /api/v1/reservations/{ref}
- Return clean summary:
  - booking_reference
  - status
  - created_at normalized
  - passengers simplified
  - itinerary simplified
  - price normalized
- Add caching using the project’s existing cache abstraction if available

5) Reuse the existing hexagonal architecture
Follow the current project structure and place code in the right layers:
- inbound adapters/controllers
- application/use cases
- ports/interfaces
- outbound adapters/legacy client/cache adapter
- infrastructure/config
Use the project’s existing folder names and conventions exactly.

6) Normalize legacy inconsistencies
Add or improve utilities/mappers for:
- mixed date parsing:
  - ISO8601
  - Unix timestamp
  - DD/MM/YYYY
  - YYYYMMDDHHMMSS
- price normalization from fields like:
  - total
  - total_amount
  - totalAmountDecimal
- code-to-label mapping:
  - MH -> Malaysia Airlines
  - AK -> AirAsia
  - SQ -> Singapore Airlines
  - Y -> Economy
  - W -> Premium Economy
  - J -> Business
  - F -> First
If unknown, keep code and use label "Unknown"

7) Error handling
Reuse the project’s existing exception handling if present.
Standardize upstream failures into a consistent error response shape:
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "Legacy service timed out",
    "details": {},
    "request_id": "uuid"
  }
}
Map at least:
- timeout -> 504
- 429 -> 429
- 503 -> 503
- bad upstream payload -> 502
- validation -> 400
- unknown -> 500

8) Retry and resilience
In the outbound legacy API adapter/client:
- add timeout
- retry only for timeout, 429, and 503
- use short exponential backoff
- do not retry 400/404

9) Cache
Reuse existing cache mechanisms if present.
Add cache where appropriate for:
- airport list/detail
- booking retrieval
Use TTL-based strategy.
Avoid introducing a new cache system unless necessary.

10) Tests
Only add or update the tests needed for missing functionality:
- offer detail transformation
- booking create validation
- booking create normalization
- booking retrieval normalization
- booking retrieval cache behavior
- error mapping
- date parsing
- money normalization
- flights search normalization if current coverage is insufficient

11) Documentation
Update existing docs instead of rewriting everything:
- README: run instructions, env vars, endpoint summary
- architecture/design note: explain how the solution fits the existing hexagonal architecture
- AI workflow note: concise and realistic

Expected output:
- modify existing files where appropriate
- create only genuinely missing files
- keep changes minimal, coherent, and aligned with the current codebase
  1. a summary of modified files
  2. architectural notes
  3. assumptions made about upstream payloads
  4. TODO / future improvements
