import asyncio, httpx

async def test():
    async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
        r = await client.post('/api/v1/auth/login', json={'email': 'test@test.com', 'password': 'password123'})
        if r.status_code != 200:
            print('Login failed:', r.status_code, r.text[:200])
            return
        tokens = r.json()
        token = tokens['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test scan list
        r2 = await client.get('/api/v1/scans', headers=headers)
        print('List scans:', r2.status_code)
        if r2.status_code == 200:
            data = r2.json()
            print('Total scans:', data.get('total', 0))
            for s in data.get('items', []):
                print(f'  Scan {s["id"]}: {s.get("name")} ({s.get("status")})')
        
        # Test scan detail for ID 4
        for scan_id in [1, 2, 3, 4]:
            r3 = await client.get(f'/api/v1/scans/{scan_id}', headers=headers)
            print(f'Get scan {scan_id}: {r3.status_code}', end='')
            if r3.status_code == 200:
                s = r3.json()
                print(f' => {s.get("name")} ({s.get("status")})')
            else:
                print(f' => {r3.text[:100]}')

asyncio.run(test())
