/**
 * k6 Load Test Suite for FastAPI Enterprise Application
 *
 * This script provides comprehensive load testing scenarios for the FastAPI
 * pricing API including smoke tests, load tests, stress tests, and spike tests.
 *
 * Usage:
 *   # Smoke test (quick validation)
 *   k6 run --vus 1 --duration 30s k6-load-test.js
 *
 *   # Load test (normal expected load)
 *   k6 run --vus 10 --duration 5m k6-load-test.js
 *
 *   # Stress test (find breaking point)
 *   k6 run --vus 50 --duration 10m k6-load-test.js
 *
 *   # Spike test (sudden traffic increase)
 *   k6 run --stage 5s:5,30s:50,5s:5 k6-load-test.js
 *
 *   # Custom test with environment variable
 *   BASE_URL=http://localhost:8000 k6 run k6-load-test.js
 */

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';
import { check, sleep } from 'k6';
import http from 'k6/http';
import { Counter, Rate, Trend } from 'k6/metrics';

// Test configuration - following k6 best practices
export const options = {
  stages: [
    // Ramp-up to normal load
    { duration: '1m', target: 10 },
    // Stay at normal load
    { duration: '3m', target: 10 },
    // Ramp-up to stress test
    { duration: '2m', target: 30 },
    // Stay at stress load
    { duration: '3m', target: 30 },
    // Cool down
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    // Global response time thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms, 99% under 1s
    // Exclude error handling tests from failure rate calculation
    // Error handling tests intentionally send invalid requests that return 400/422
    'http_req_failed{type:!error_handling}': ['rate<0.01'], // Less than 1% failures (excluding error tests)

    // Endpoint-specific thresholds (using tags)
    'http_req_duration{endpoint:pricing}': ['p(95)<800', 'p(99)<1500'],
    'http_req_duration{endpoint:health}': ['p(95)<100', 'p(99)<200'],
    'http_req_duration{endpoint:metadata}': ['p(95)<200', 'p(99)<500'],

    // Response receiving time
    http_req_receiving: ['avg<200'],

    // Custom metric thresholds
    pricing_calculation_success: ['rate>0.95'], // 95% success rate
    health_check_success: ['rate>0.99'], // 99% success rate
    pricing_calculation_duration: ['p(95)<800', 'p(99)<1500'],
  },
  // Resource optimization - discard response bodies to save memory
  discardResponseBodies: false, // Keep bodies for validation, but can set to true for very large tests
  // HTTP timeouts - include 400 for domain errors (invalid enum values, etc.)
  httpReq: {
    expectedStatuses: [200, 400, 422], // Accept success, domain errors (400), and validation errors (422)
  },
};

// Base URL - can be overridden with BASE_URL environment variable
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Custom metrics
const pricingCalculationSuccess = new Rate('pricing_calculation_success');
const healthCheckSuccess = new Rate('health_check_success');
const pricingCalculationDuration = new Trend('pricing_calculation_duration');
const requestCounter = new Counter('total_requests');

// Test data - realistic manufacturing part specifications
// Materials match Material enum from app/core/domain/cost/models/enums.py
const materials = [
  'aluminum',
  'steel',
  'stainless_steel',
  'titanium',
  'plastic_abs',
  'plastic_pla',
  'plastic_petg',
  'brass',
  'copper',
  'carbon_fiber',
];
// Processes match ManufacturingProcess enum - fetched from /api/v1/pricing/processes
// Actual values: cnc, 3d_printing, sheet_cutting, tube_bending, injection_molding, laser_cutting, waterjet_cutting
const processes = [
  'cnc',
  '3d_printing',
  'waterjet_cutting',
  'laser_cutting',
  'sheet_cutting',
  'tube_bending',
  'injection_molding',
];
const customerTiers = ['standard', 'premium', 'enterprise'];
const shippingZones = [1, 2, 3, 4]; // 1=local, 2=regional, 3=national, 4=international

/**
 * Safely parse JSON with error handling
 */
function safeJsonParse(jsonString) {
  try {
    return JSON.parse(jsonString);
  } catch (e) {
    console.error('Failed to parse JSON:', e.message);
    return null;
  }
}

/**
 * Generate a random pricing request with realistic values
 * Following best practice: parameterized, realistic data
 */
function generatePricingRequest() {
  const complexity = Math.random() * 4 + 1; // 1.0 to 5.0
  const quantity = Math.floor(Math.random() * 999) + 1; // 1 to 1000
  const length = Math.floor(Math.random() * 300) + 50; // 50-350mm
  const width = Math.floor(Math.random() * 200) + 30; // 30-230mm
  const height = Math.floor(Math.random() * 100) + 10; // 10-110mm

  return {
    dimensions: {
      length_mm: length,
      width_mm: width,
      height_mm: height,
    },
    geometric_complexity_score: Math.round(complexity * 10) / 10,
    material: materials[Math.floor(Math.random() * materials.length)],
    process: processes[Math.floor(Math.random() * processes.length)],
    quantity: quantity,
    customer_tier:
      customerTiers[Math.floor(Math.random() * customerTiers.length)],
    shipping_distance_zone:
      shippingZones[Math.floor(Math.random() * shippingZones.length)],
  };
}

/**
 * Test health check endpoints
 * Following best practice: clear tags, error handling, single JSON parse
 */
function testHealthChecks() {
  // Root endpoint
  const rootResponse = http.get(`${BASE_URL}/`, {
    tags: { endpoint: 'root', type: 'health' },
  });
  const rootBody = safeJsonParse(rootResponse.body);
  check(rootResponse, {
    'root endpoint status is 200': (r) => r.status === 200,
    'root endpoint has message': () => rootBody?.message !== undefined,
  });
  requestCounter.add(1);

  // Basic health check
  const healthResponse = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: 'health', type: 'health' },
  });
  const healthBody = safeJsonParse(healthResponse.body);
  const healthOk = check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check status is healthy': () => healthBody?.status === 'healthy',
    'health check has service name': () => healthBody?.service !== undefined,
  });
  healthCheckSuccess.add(healthOk);
  requestCounter.add(1);

  // Metrics endpoint
  const metricsResponse = http.get(`${BASE_URL}/metrics`, {
    tags: { endpoint: 'metrics', type: 'metrics' },
  });
  check(metricsResponse, {
    'metrics endpoint status is 200': (r) => r.status === 200,
    'metrics endpoint returns Prometheus format': (r) =>
      r.body && r.body.includes('# TYPE'),
  });
  requestCounter.add(1);
}

/**
 * Test pricing metadata endpoints
 * Following best practice: single JSON parse, proper error handling
 */
function testPricingMetadata() {
  // Get materials
  const materialsResponse = http.get(`${BASE_URL}/api/v1/pricing/materials`, {
    tags: { endpoint: 'metadata', type: 'materials' },
  });
  const materialsBody = safeJsonParse(materialsResponse.body);
  check(materialsResponse, {
    'materials endpoint status is 200': (r) => r.status === 200,
    'materials endpoint returns array': () => Array.isArray(materialsBody),
    'materials array is not empty': () => materialsBody && materialsBody.length > 0,
  });
  requestCounter.add(1);

  // Get processes
  const processesResponse = http.get(`${BASE_URL}/api/v1/pricing/processes`, {
    tags: { endpoint: 'metadata', type: 'processes' },
  });
  const processesBody = safeJsonParse(processesResponse.body);
  check(processesResponse, {
    'processes endpoint status is 200': (r) => r.status === 200,
    'processes endpoint returns array': () => Array.isArray(processesBody),
    'processes array is not empty': () => processesBody && processesBody.length > 0,
  });
  requestCounter.add(1);

  // Note: Tiers endpoint doesn't exist - tiers are part of pricing response
  // Skipping this test to match actual API
}

/**
 * Test pricing calculation endpoint
 * Following best practice: single JSON parse, proper tags, error handling
 */
function testPricingCalculation() {
  const requestData = generatePricingRequest();
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: {
      endpoint: 'pricing',
      method: 'POST',
      material: requestData.material,
      process: requestData.process,
      customer_tier: requestData.customer_tier,
    },
  };

  const response = http.post(
    `${BASE_URL}/api/v1/pricing`,
    JSON.stringify(requestData),
    params
  );

  // Single JSON parse - following best practice
  const responseBody = safeJsonParse(response.body) || {};
  const tiers = responseBody.pricing_tiers || responseBody.pricing || {};

  const success = check(response, {
    'pricing endpoint status is 200': (r) => r.status === 200,
    'pricing response has cost_breakdown': () => responseBody.cost_breakdown !== undefined,
    'pricing response has pricing': () =>
      responseBody.pricing !== undefined || responseBody.pricing_tiers !== undefined,
    'pricing response has part_specification': () =>
      responseBody.part_specification !== undefined,
    'cost breakdown has total_cost': () =>
      responseBody.cost_breakdown?.total_cost !== undefined,
    'pricing tiers have all four tiers': () => (
      tiers.expedited &&
      tiers.standard &&
      tiers.economy &&
      tiers.domestic_economy
    ),
    'final prices are positive': () => (
      tiers.expedited?.final_price > 0 &&
      tiers.standard?.final_price > 0 &&
      tiers.economy?.final_price > 0 &&
      tiers.domestic_economy?.final_price > 0
    ),
  });

  pricingCalculationSuccess.add(success);
  if (response.timings.duration) {
    pricingCalculationDuration.add(response.timings.duration);
  }
  requestCounter.add(1);

  // Log failed requests for debugging (only on failure)
  if (!success) {
    console.error(`Pricing calculation failed: ${response.status}`, {
      request: requestData,
      response: responseBody,
    });
  }

  return success;
}

/**
 * Test error handling with invalid requests
 * Following best practice: proper error validation, tags for filtering
 */
function testErrorHandling() {
  // Test invalid material
  const invalidMaterialRequest = {
    dimensions: { length_mm: 100, width_mm: 50, height_mm: 25 },
    geometric_complexity_score: 3.0,
    material: 'invalid_material',
    process: 'cnc',
    quantity: 50,
    customer_tier: 'standard',
    shipping_distance_zone: 1,
  };

  const invalidMaterialResponse = http.post(
    `${BASE_URL}/api/v1/pricing`,
    JSON.stringify(invalidMaterialRequest),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'pricing', type: 'error_handling', error_type: 'invalid_material' },
    }
  );

  const invalidMaterialBody = safeJsonParse(invalidMaterialResponse.body);
  check(invalidMaterialResponse, {
    'invalid material returns 400': (r) => r.status === 400,
    'invalid material has error structure': () =>
      invalidMaterialBody?.detail?.error !== undefined || invalidMaterialBody?.error !== undefined,
  });
  requestCounter.add(1);

  // Test invalid dimensions
  const invalidDimensionsRequest = {
    dimensions: { length_mm: -100, width_mm: 50, height_mm: 25 },
    geometric_complexity_score: 3.0,
    material: 'aluminum',
    process: 'cnc',
    quantity: 50,
    customer_tier: 'standard',
    shipping_distance_zone: 1,
  };

  const invalidDimensionsResponse = http.post(
    `${BASE_URL}/api/v1/pricing`,
    JSON.stringify(invalidDimensionsRequest),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'pricing', type: 'error_handling', error_type: 'invalid_dimensions' },
    }
  );

  const invalidDimensionsBody = safeJsonParse(invalidDimensionsResponse.body);
  check(invalidDimensionsResponse, {
    'invalid dimensions returns 400 or 422': (r) => r.status === 400 || r.status === 422,
    'invalid dimensions has error structure': () =>
      invalidDimensionsBody?.detail?.error !== undefined ||
      invalidDimensionsBody?.error !== undefined ||
      invalidDimensionsBody?.detail !== undefined,
  });
  requestCounter.add(1);
}

/**
 * Main test function - executed by each virtual user
 * Following best practice: realistic think time patterns
 */
export default function () {
  // Test health checks (lightweight, should be fast)
  testHealthChecks();
  // Realistic think time: 1-3 seconds (exponential distribution is more realistic)
  sleep(Math.random() * 2 + 1);

  // Test metadata endpoints (moderate load)
  testPricingMetadata();
  sleep(Math.random() * 2 + 1);

  // Test pricing calculation (main workload)
  testPricingCalculation();
  // Longer think time after complex operation: 2-5 seconds
  sleep(Math.random() * 3 + 2);

  // Occasionally test error handling (10% of the time - realistic error rate)
  if (Math.random() < 0.1) {
    testErrorHandling();
    sleep(1);
  }
}

/**
 * Setup function - runs once before the test starts
 * Following best practice: validate environment and API availability
 */
export function setup() {
  console.log(`Starting load test against ${BASE_URL}`);
  console.log(`Test configuration:`, JSON.stringify(options, null, 2));

  // Verify API is accessible and healthy
  const healthCheck = http.get(`${BASE_URL}/health`, {
    tags: { name: 'setup_health_check' },
    timeout: '10s',
  });

  if (healthCheck.status !== 200) {
    console.error(`❌ API health check failed! Status: ${healthCheck.status}`);
    console.error(`Make sure the API is running at ${BASE_URL}`);
    return { api_available: false };
  }

  const healthBody = safeJsonParse(healthCheck.body);
  if (healthBody?.status !== 'healthy') {
    console.error(`❌ API is not healthy! Status: ${healthBody?.status}`);
    return { api_available: false };
  }

  console.log('✅ API is accessible and healthy');
  return { api_available: true };
}

/**
 * Teardown function - runs once after the test completes
 * Following best practice: cleanup and summary
 */
export function teardown(data) {
  console.log('Load test completed');
  if (data && data.api_available === false) {
    console.warn('⚠️  API was not available during setup - results may be invalid');
  }
}

/**
 * Handle test results and generate reports
 */
export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
    'k6-load-test-report.html': htmlReport(data),
  };
}
