import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const VUS = Number(__ENV.VUS || '1');
const DURATION = __ENV.DURATION || '65s';
const USERNAME = __ENV.NEMO_USER || 'lab_user';
const PASSWORD = __ENV.NEMO_PASS || 'nemo-sqe-test-2026';

export const options = {
  scenarios: {
    steady_load: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{endpoint:access_requests}': ['p(95)<=500'],
  },
};

export function setup() {
  const loginGet = http.get(`${BASE_URL}/login/`);
  const csrfMatch = loginGet.body.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
  const csrfToken = csrfMatch ? csrfMatch[1] : '';

  const res = http.post(
    `${BASE_URL}/login/`,
    {
      username: USERNAME,
      password: PASSWORD,
      csrfmiddlewaretoken: csrfToken,
    },
    {
      redirects: 0,
      headers: {
        Referer: `${BASE_URL}/login/`,
      },
    }
  );

  const sessionCookie = res.cookies.sessionid ? res.cookies.sessionid[0].value : '';
  const csrfCookie = res.cookies.csrftoken ? res.cookies.csrftoken[0].value : csrfToken;
  if (!sessionCookie) {
    throw new Error(`k6 setup login failed (status=${res.status})`);
  }

  return {
    cookieHeader: `sessionid=${sessionCookie}; csrftoken=${csrfCookie}`,
  };
}

export default function (data) {
  const res = http.get(`${BASE_URL}/access_requests/`, {
    headers: {
      Cookie: data.cookieHeader,
    },
    tags: {
      endpoint: 'access_requests',
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'contains access requests markup': (r) => r.body.includes('New request'),
  });

  sleep(0.1);
}
