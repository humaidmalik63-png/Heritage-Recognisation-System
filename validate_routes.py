import subprocess

routes = [
    ('/', 'Drop specimen photograph'),
    ('/history', 'Taj Mahal'),
    ('/login', 'Curator Sign In'),
    ('/signup', 'Create Archival Account')
]

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

for route, pattern in routes:
    cmd = [edge_path, '--headless=new', '--dump-dom', '--virtual-time-budget=3000', f'http://127.0.0.1:5173{route}']
    res = subprocess.run(cmd, capture_output=True, text=True)
    dom = res.stdout
    if pattern.lower() in dom.lower():
        print(f'[PASS] Route {route} rendered: found "{pattern}"')
    else:
        print(f'[FAIL] Route {route} did NOT contain "{pattern}"')

