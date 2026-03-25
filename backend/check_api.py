import requests
import json

try:
    response = requests.get('http://localhost:5000/customer-problems')
    data = response.json()
    print('API Response:')
    print(json.dumps(data, indent=2))
    
    print('\nFirst problem details:')
    if data.get('problems') and len(data['problems']) > 0:
        first_problem = data['problems'][0]
        print(f"  issue_description: '{first_problem.get('issue_description', 'N/A')}'")
        print(f"  label: '{first_problem.get('label', 'N/A')}'")
        print(f"  mentions: {first_problem.get('mentions', 0)}")
        
except Exception as e:
    print(f'Error: {e}')
