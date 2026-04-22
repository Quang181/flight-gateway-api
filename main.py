from app.bootstrap import create_app
from app.infrastructure.config.settings import get_settings
import uvicorn


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=8000)
