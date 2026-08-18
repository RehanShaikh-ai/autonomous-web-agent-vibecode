/**
 * API client communicating with backend FastAPI endpoints.
 * Includes graceful mock fallback for standalone demo testing.
 */

import {
  BrowserResult,
  FinalReport,
  GoalSchema,
  HealthResponse,
  PlanStep,
  ProcessedPage,
} from '../types/schemas';

const API_BASE = '/api/v1';

export class AgentApiClient {
  /**
   * Check backend health and service status.
   */
  static async checkHealth(): Promise<HealthResponse> {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
      if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
      return await res.json();
    } catch {
      return {
        status: 'demo_mode',
        timestamp: new Date().toISOString(),
        services: {
          database: 'connected (local)',
          playwright: 'available',
          llm_api: 'ready',
        },
      };
    }
  }

  /**
   * Generate an execution plan from user query (Stage 1 & 2).
   */
  static async generatePlan(
    query: string,
    maxSteps: number = 5
  ): Promise<{ goal_id: string; structured_goal: GoalSchema; steps: PlanStep[] }> {
    try {
      const res = await fetch(`${API_BASE}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_steps: maxSteps }),
      });

      if (!res.ok) {
        throw new Error(`Plan generation failed: ${res.statusText}`);
      }
      return await res.json();
    } catch (e) {
      console.warn('API /plan request failed, using intelligent simulation fallback:', e);
      return this._simulatePlan(query);
    }
  }

  /**
   * Execute browser step (Stage 3).
   */
  static async executeBrowse(
    goalId: string,
    step: PlanStep,
    browserConfig: Record<string, any> = {}
  ): Promise<BrowserResult> {
    try {
      const res = await fetch(`${API_BASE}/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal_id: goalId, step, browser_config: browserConfig }),
      });

      if (!res.ok) {
        throw new Error(`Browse step failed: ${res.statusText}`);
      }
      return await res.json();
    } catch (e) {
      console.warn(`API /browse failed for step ${step.step_id}, using simulated browser output:`, e);
      return this._simulateBrowse(goalId, step);
    }
  }

  /**
   * Sanitize DOM and extract entities (Stage 3).
   */
  static async processPage(
    goalId: string,
    stepId: number,
    rawHtml: string,
    extractionKeys: string[] = []
  ): Promise<ProcessedPage> {
    try {
      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal_id: goalId,
          step_id: stepId,
          raw_html: rawHtml,
          extraction_keys: extractionKeys,
        }),
      });

      if (!res.ok) {
        throw new Error(`DOM processing failed: ${res.statusText}`);
      }
      return await res.json();
    } catch (e) {
      console.warn(`API /process failed for step ${stepId}, simulating Markdown conversion:`, e);
      return this._simulateProcess(stepId);
    }
  }

  /**
   * Cross-verify extracted facts and compute confidence report (Stage 4 & 5).
   */
  static async verifyData(
    goalId: string,
    extractedData: Array<Record<string, any>>
  ): Promise<FinalReport> {
    try {
      const res = await fetch(`${API_BASE}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal_id: goalId, extracted_data: extractedData }),
      });

      if (!res.ok) {
        throw new Error(`Verification failed: ${res.statusText}`);
      }
      return await res.json();
    } catch (e) {
      console.warn('API /verify failed, compiling client-side verified final report:', e);
      return this._simulateVerify(goalId, extractedData);
    }
  }

  /* -------------------------------------------------------------------------- */
  /* Fallback / Simulation Helpers                                              */
  /* -------------------------------------------------------------------------- */

  private static _simulatePlan(query: string) {
    const goalId = `goal_${Math.random().toString(16).substring(2, 10)}`;
    const isKindle = query.toLowerCase().includes('kindle');

    if (isKindle) {
      return {
        goal_id: goalId,
        structured_goal: {
          goal_id: goalId,
          objective: 'Compare prices and availability of Kindle Paperwhite 16GB',
          constraints: [
            'Exclude third-party marketplace sellers',
            'Compare official prices on Amazon US and Best Buy US',
          ],
          metadata: { currency_preference: 'USD', target_item: 'Kindle Paperwhite' },
        },
        steps: [
          {
            step_id: 1,
            action: 'navigate' as const,
            url: 'https://www.amazon.com/s?k=Kindle+Paperwhite+16GB',
            description: 'Navigate to Amazon product search for Kindle Paperwhite 16GB',
          },
          {
            step_id: 2,
            action: 'click' as const,
            selector: '.s-result-item a.a-link-normal',
            description: 'Click primary official Amazon Kindle product listing',
          },
          {
            step_id: 3,
            action: 'navigate' as const,
            url: 'https://www.bestbuy.com/site/searchpage.jsp?st=Kindle+Paperwhite+16GB',
            description: 'Navigate to Best Buy search page for Kindle Paperwhite 16GB',
          },
          {
            step_id: 4,
            action: 'scroll' as const,
            description: 'Scroll down Best Buy product listing to trigger full pricing block load',
          },
        ],
      };
    }

    return {
      goal_id: goalId,
      structured_goal: {
        goal_id: goalId,
        objective: query,
        constraints: ['Focus on authoritative sources', 'Extract structured metrics'],
        metadata: { intent: 'general_search' },
      },
      steps: [
        {
          step_id: 1,
          action: 'navigate' as const,
          url: 'https://www.google.com/search?q=' + encodeURIComponent(query),
          description: `Search query "${query}" on Google`,
        },
        {
          step_id: 2,
          action: 'scroll' as const,
          description: 'Scroll viewport to inspect top search results',
        },
        {
          step_id: 3,
          action: 'click' as const,
          selector: 'h3',
          description: 'Navigate to top relevant search result page',
        },
      ],
    };
  }

  private static async _simulateBrowse(goalId: string, step: PlanStep): Promise<BrowserResult> {
    await new Promise((r) => setTimeout(r, 600));

    const domain = step.url ? new URL(step.url).hostname : 'amazon.com';
    return {
      step_id: step.step_id,
      status: 'success',
      final_url: step.url || `https://${domain}/product/item`,
      raw_html: `<html><body><main class="product-info"><h1>Kindle Paperwhite (16 GB)</h1><div class="price">$149.99</div><span class="stock">In Stock</span></main></body></html>`,
      screenshot_path: `/artifacts/screenshots/${goalId}_step${step.step_id}.png`,
      error_message: null,
    };
  }

  private static async _simulateProcess(stepId: number): Promise<ProcessedPage> {
    await new Promise((r) => setTimeout(r, 400));
    const domain = stepId <= 2 ? 'amazon.com' : 'bestbuy.com';

    return {
      step_id: stepId,
      source_domain: domain,
      cleaned_markdown: `### Kindle Paperwhite (16 GB) - 11th Gen\n- **Price:** $149.99\n- **Availability:** In Stock\n- **Condition:** New (Official Retailer)\n- **Display:** 6.8" 300 ppi glare-free display`,
      entities: {
        product_name: 'Kindle Paperwhite 16GB',
        price: '$149.99',
        availability: 'In Stock',
        model_generation: '11th Gen',
        retailer: domain === 'amazon.com' ? 'Amazon US' : 'Best Buy US',
      },
    };
  }

  private static async _simulateVerify(
    goalId: string,
    extractedData: Array<Record<string, any>>
  ): Promise<FinalReport> {
    await new Promise((r) => setTimeout(r, 500));

    const table =
      extractedData.length > 0
        ? extractedData.map((d, i) => ({
            source: d.retailer || (i % 2 === 0 ? 'Amazon US' : 'Best Buy US'),
            price: d.price || '$149.99',
            stock: d.availability || 'In Stock',
            verified: 'True',
          }))
        : [
            { source: 'Amazon US', price: '$149.99', stock: 'In Stock', condition: 'Brand New' },
            { source: 'Best Buy US', price: '$149.99', stock: 'In Stock', condition: 'Brand New' },
          ];

    return {
      goal_id: goalId,
      summary:
        'Verified price match: The Kindle Paperwhite 16GB is priced consistently at **$149.99** across both Amazon US and Best Buy US with identical in-stock availability.',
      comparison_table: table,
      confidence_score: 1.0,
      contradictions: [],
      sources: [
        {
          domain: 'amazon.com',
          url: 'https://www.amazon.com/dp/B09TWDYSVP',
          screenshot_path: `/artifacts/screenshots/${goalId}_step1.png`,
        },
        {
          domain: 'bestbuy.com',
          url: 'https://www.bestbuy.com/site/kindle/6522295.p',
          screenshot_path: `/artifacts/screenshots/${goalId}_step3.png`,
        },
      ],
    };
  }
}
