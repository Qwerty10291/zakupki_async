import requests

print([requests.delete(f'http://127.0.0.1:8000/api/queries/{i}', params={'key': 'w1gLpauemARZOxfhziblmwOPzEMrinCF'}).json() for i in range(10, 16)])