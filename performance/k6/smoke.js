import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const url = 'http://localhost:8000/health';
  const res = http.get(url);
  check(res, { 'status was 200': (r) => r.status === 200 });
  sleep(0.5);
}
