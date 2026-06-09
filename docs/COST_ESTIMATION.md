# Cost Estimation

## Assumptions
- Average user: 5 food logs/day (3 text + 2 photo)
- Average AI call: ~800 tokens input + ~400 output
- OpenAI pricing (as of mid-2025): gpt-4o-mini $0.15/1M input, $0.60/1M output
- OpenAI Vision (gpt-4o): $2.50/1M input tokens, ~300 tokens/image
- 30% of messages generate a coaching reply

---

## 100 Active Users / Month

| Service | Usage | Monthly Cost |
|---|---|---|
| VPS 2vCPU/4GB (Hetzner/DO) | 1 server | $20 |
| PostgreSQL (managed) | db.t3.micro | $15 |
| Redis (managed) | cache.t3.micro | $10 |
| OpenAI Text (gpt-4o-mini) | 100×3×30×1.2K tokens | ~$2 |
| OpenAI Vision (gpt-4o) | 100×2×30 calls | ~$6 |
| OpenAI Coaching | 100×30×800 tokens | ~$1 |
| S3 Storage (1 GB photos) | Standard | $0.50 |
| **Total** | | **~$55/month** |

Break-even: ~6 premium users at $9.99/month.

---

## 1,000 Active Users / Month

| Service | Usage | Monthly Cost |
|---|---|---|
| 2× VPS 2vCPU/4GB | Load balanced | $40 |
| PostgreSQL db.t3.small | Managed | $30 |
| Redis cache.t3.small | Managed | $20 |
| OpenAI Text (gpt-4o-mini) | 1000×3×30 calls | ~$22 |
| OpenAI Vision (gpt-4o) | 1000×2×30 calls | ~$60 |
| OpenAI Coaching | 1000×30 | ~$10 |
| S3 Storage (10 GB) | Standard | $2 |
| **Total** | | **~$184/month** |

Break-even: ~19 premium users. Easily achievable at 1000 users.

---

## 10,000 Active Users / Month

| Service | Usage | Monthly Cost |
|---|---|---|
| 4× VPS 4vCPU/8GB | Load balanced | $160 |
| PostgreSQL db.t3.medium (Multi-AZ) | Managed | $120 |
| Redis cache.t3.medium | Managed | $80 |
| OpenAI Text (gpt-4o-mini) | 10K×3×30 calls | ~$220 |
| OpenAI Vision (gpt-4o) | 10K×2×30 calls | ~$600 |
| OpenAI Coaching | 10K×30 | ~$100 |
| S3 Storage (100 GB) | Standard + CDN | $15 |
| CloudFront CDN | 500 GB transfer | $45 |
| Monitoring (Datadog) | Infrastructure | $60 |
| **Total** | | **~$1,400/month** |

Revenue at 10% premium (1,000 users × $9.99) = $9,990/month → **7× ROI**.

---

## Cost Optimization Tips

1. **Use gpt-4o-mini for text analysis** — 95% as good as gpt-4o at 10% cost
2. **Cache meal analyses** — if user logs "200g chicken" again, reuse cached analysis
3. **Batch coaching messages** — send to all users at once from worker, not per-message
4. **Compress photos** — resize to max 1024px before Vision API → fewer tokens
5. **Rate limit aggressively** — free users already limited; reduces API abuse cost
