"""Allow running with: python -m tabb."""

import uvicorn

from tabb.adapters.config.settings import settings
from tabb.adapters.outbound.logging.logger import setup_logging

setup_logging()

if __name__ == "__main__":
    uvicorn.run(
        "tabb.adapters.inbound.api.rest.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )
