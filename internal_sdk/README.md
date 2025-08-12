# SDK Generation

Once the Portfolio service is running, you can generate a typed Python SDK via:

```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json --meta none --config sdk_config.yml
```
