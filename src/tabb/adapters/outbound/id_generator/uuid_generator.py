"""UUID-based ID generator adapter."""

import uuid

from tabb.domain.ports.id_generator import IdGenerator


class UuidIdGenerator(IdGenerator):
    """Generates unique identifiers using UUID4."""

    def generate(self) -> str:
        return str(uuid.uuid4())
