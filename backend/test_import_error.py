import sys
sys.path.append('.')

try:
    from src.services.service_factory import service_factory
    print('service_factory OK')
    
    agent = service_factory.analyst_agent
    print(f'agent OK: {type(agent).__name__}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
