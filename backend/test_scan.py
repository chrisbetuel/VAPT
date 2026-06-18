import httpx, json, time

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzgxNzA2OTUzLCJpYXQiOjE3ODE3MDUxNTMsImlzcyI6IlZBUFQgUGxhdGZvcm0iLCJ0eXBlIjoiYWNjZXNzIiwicm9sZSI6InZpZXdlciJ9.zPeigtCq2p8dEAQw51JfjpHva1OYQueT0FMz7Cr9qMk'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

r = httpx.get('http://localhost:8000/api/v1/targets/2', headers=headers)
target = r.json().get('data', {})
print(f'Target: {target.get("name")} - {target.get("url")}')

scan_data = {
    'target_id': 2, 'name': 'Test ZAP Scan',
    'config': {'scan_type': 'quick', 'scanners': ['zap', 'nmap'], 'intensity': 'normal'}
}
r = httpx.post('http://localhost:8000/api/v1/scans', json=scan_data, headers=headers)
scan = r.json().get('data', r.json())
scan_id = scan.get('id')
print(f'Created scan {scan_id}, status={scan.get("status")}')

r = httpx.post(f'http://localhost:8000/api/v1/scans/{scan_id}/start', headers=headers)
scan = r.json().get('data', r.json())
print(f'Started scan {scan_id}, status={scan.get("status")}')

for i in range(10):
    time.sleep(3)
    r = httpx.get(f'http://localhost:8000/api/v1/scans/{scan_id}', headers=headers)
    s = r.json().get('data', r.json())
    logs = s.get('logs') or []
    print(f'  Poll {i+1}: status={s.get("status")}, progress={s.get("progress")}, logs={len(logs)}')
    for log in logs[-3:]:
        print(f'    {log.get("level")}: {log.get("message")}')
