"""Script to initialize default admin user in Neo4j database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.user_service import UserService
from app.utils.logger import logger


def initialize_admin_user() -> None:
    """Initialize default admin user in database.

    Creates an admin user with credentials: username='admin', password='Admin@123'
    if it doesn't already exist.
    """
    logger.info("Initializing admin user...")

    try:
        user_service = UserService()

        # Check if admin already exists
        existing_admin = user_service.get_user_by_username("admin")
        if existing_admin:
            logger.info("Admin user already exists")
            user_service.close()
            return

        # Create admin user
        admin = user_service.create_user(
            username="admin",
            email="admin@localhost",
            password="Admin@123",
            full_name="System Administrator",
            role="admin",
        )

        if admin:
            logger.info(f"Successfully created admin user with ID: {admin.user_id}")
        else:
            logger.error("Failed to create admin user")

        user_service.close()

    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")
        raise


if __name__ == "__main__":
    initialize_admin_user()
    logger.info("Admin user initialization completed")
