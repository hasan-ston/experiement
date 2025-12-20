# Personal Finance Tracker

Flask + React expense tracker with Redis caching, JWT auth, and AI-powered spending insights. Built to learn production-grade concepts like caching strategies, stateless authentication, and cloud deployment.

🔗 Try it: [App](https://experiement-ijm4-lpui9zc72-hasan-stons-projects.vercel.app/) | [API](https://experiement.onrender.com)

## What it does
- User authentication with CRUD operations for expenses.
- Redis caches category summaries per user (cache miss ~3ms → hit ~0.6ms server-side). Cache invalidates automatically on writes.
- Comprehensive logging for cache performance and AI provider selection.

## Tech Stack
- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Limiter, Redis client, CORS
- **Database**: SQLite (in development), Postgres (in production)
- **Cache**: Redis with 5 minute TTL per user
- **Frontend**: Vite + React
- **Deployment**: Backend deployed on Render, and Frontend on Vercel

## Performance Metrics (server-side)
- Summary endpoint: ~3ms on cache miss, ~0.6ms on cache hit (observable in logs)
- Caching reduces database query load by approximately 80%+ in typical read-heavy scenarios
- While network latency dominates end-to-end response time, caching significantly improves server capacity and reduces database load under heavy traffic.

## Key Learnings

### Caching Impact
Implemented Redis caching for the summary endpoint, reducing response time from ~3ms (cold) to ~0.6ms (cached). This optimization would eliminate significant database load at scale, particularly for read-heavy workloads.

### Database Indexing
Learned the difference between full table scans and indexed queries. Without proper indexes, the database scans every row sequentially. With indexes, queries jump directly to relevant data. For a small dataset the difference is milliseconds, but at scale this becomes critical.

### Network Latency vs Server Performance
The round-trip network latency typically dominates total response time. While backend optimizations like caching don't reduce network RTT, they dramatically improve server throughput and reduce database load, allowing the system to handle significantly more concurrent requests.

### JWT vs Session-Based Authentication
Most beginner tutorials use session-based auth, but I implemented JWTs after learning about their scaling advantages:

**The problem with sessions**: The server must store session data for every logged-in user. With multiple servers (required for horizontal scaling), this session data isn't automatically shared. You either need:
- A shared session store (adds complexity and a single point of failure)
- Sticky sessions (users must always hit the same server, limiting load balancing)

Either way, servers become stateful, making it difficult to scale horizontally if needed.

**How JWTs solve this**: When a user logs in, the server generates a signed token containing the user's data (like user ID). This token is cryptographically signed but not encrypted—the signature proves it hasn't been tampered with. 

On each request, the frontend sends this token in the `Authorization` header. The server:
1. Validates the signature (ensures token wasn't forged)
2. Extracts the user ID from the payload
3. Proceeds with the request

No server-side session storage needed. This makes servers stateless; they don't need to remember anything between requests. Any server can validate any token, enabling true horizontal scaling. Just spin up more servers behind a load balancer and you're good.

**Tradeoffs**: JWTs can't be easily invalidated before expiry (would need a blacklist, reintroducing state). They're also larger than session IDs, slightly increasing bandwidth. For this project, the stateless architecture and scaling benefits outweighed these concerns.

### Rate Limiting and Cache Invalidation
Implementing proper rate limits prevented API abuse, while cache invalidation logic ensured data consistency when users modified their expenses. Logging was invaluable for debugging these edge cases in production.

---

Built by a first-year engineering student exploring production concepts beyond basic CRUD applications. Open to feedback and contributions!
