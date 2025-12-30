"""User service for managing users in Neo4j database."""

import uuid
from datetime import datetime
from typing import Optional

from neo4j import Driver, GraphDatabase

from app.models.user import UserDB, UserRole, UserResponse
from app.services.auth_service import AuthenticationService, get_auth_service, pwd_context
from app.utils.logger import logger
from app.utils.settings import settings


class UserService:
    """Service for managing users in Neo4j."""

    def __init__(self, driver: Optional[Driver] = None):
        """Initialize user service.

        Args:
            driver: Neo4j driver instance. If None, creates new connection.
        """
        self.driver = driver or self._create_driver()
        self.auth_service = get_auth_service()

    @staticmethod
    def _create_driver() -> Driver:
        """Create Neo4j driver connection.

        Returns:
            Neo4j Driver instance.
        """
        uri = settings.NEO4J_URI
        user = settings.NEO4J_USER
        password = settings.NEO4J_PASSWORD

        logger.info(f"Connecting to Neo4j at {uri}")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        return driver

    def _execute_write(self, query: str, parameters: dict) -> any:
        """Execute a write query.

        Args:
            query: Cypher query.
            parameters: Query parameters.

        Returns:
            Query result.
        """
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return result.single()

    def _execute_read(self, query: str, parameters: dict) -> any:
        """Execute a read query.

        Args:
            query: Cypher query.
            parameters: Query parameters.

        Returns:
            Query result.
        """
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return result.single()

    def create_user(
        self, username: str, email: Optional[str], password: str, full_name: Optional[str], role: str = "user"
    ) -> Optional[UserResponse]:
        """Create a new user.

        Args:
            username: Username.
            email: Email address.
            password: Plain text password.
            full_name: Full name.
            role: User role (admin or user).

        Returns:
            UserResponse if created successfully, None otherwise.
        """
        # Check if user already exists
        if self.get_user_by_username(username):
            logger.warning(f"User already exists: {username}")
            return None

        user_id = str(uuid.uuid4())
        password_hash = self.auth_service.hash_password(password)
        now = datetime.utcnow().timestamp()

        query = """
        CREATE (u:Users {
            user_id: $user_id,
            username: $username,
            email: $email,
            full_name: $full_name,
            password_hash: $password_hash,
            role: $role,
            is_active: true,
            created_at: $created_at,
            updated_at: $updated_at,
            last_login: null,
            bypass_guardrails: $bypass_guardrails
        })
        RETURN u
        """

        bypass_guardrails = role == "admin"

        try:
            result = self._execute_write(
                query,
                {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "password_hash": password_hash,
                    "role": role,
                    "created_at": now,
                    "updated_at": now,
                    "bypass_guardrails": bypass_guardrails,
                },
            )

            if result:
                user_node = result["u"]
                logger.info(f"Created user: {username}")
                return self._node_to_response(user_node)

        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")

        return None

    def get_user_by_username(self, username: str) -> Optional[UserDB]:
        """Get user by username.

        Args:
            username: Username to search for.

        Returns:
            UserDB if found, None otherwise.
        """
        query = "MATCH (u:Users {username: $username}) RETURN u"

        try:
            result = self._execute_read(query, {"username": username})
            if result:
                user_node = result["u"]
                return self._node_to_db_model(user_node)
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")

        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID.

        Args:
            user_id: User ID.

        Returns:
            UserResponse if found, None otherwise.
        """
        query = "MATCH (u:Users {user_id: $user_id}) RETURN u"

        try:
            result = self._execute_read(query, {"user_id": user_id})
            if result:
                user_node = result["u"]
                return self._node_to_response(user_node)
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")

        return None

    def authenticate_user(self, username: str, password: str) -> Optional[UserDB]:
        """Authenticate a user with username and password.

        Args:
            username: Username.
            password: Plain text password.

        Returns:
            UserDB if authentication successful, None otherwise.
        """
        user = self.get_user_by_username(username)
        if not user:
            logger.debug(f"Authentication failed: user not found {username}")
            return None

        if not user.is_active:
            logger.debug(f"Authentication failed: user inactive {username}")
            return None

        # Verify password and check if hash needs upgrading
        try:
            verified = pwd_context.verify(password, user.password_hash)
            if not verified:
                logger.debug(f"Authentication failed: invalid password for {username}")
                return None

            # Check if hash needs upgrading to newer scheme
            if pwd_context.needs_update(user.password_hash):
                logger.debug(f"Upgrading password hash for user {username}")
                new_hash = pwd_context.hash(password)
                self.update_password_hash(user.user_id, new_hash)

        except Exception as e:
            logger.debug(f"Password verification error for {username}: {e}")
            return None

        # Update last login
        self.update_last_login(user.user_id)
        logger.info(f"User authenticated: {username}")
        return user

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp.

        Args:
            user_id: User ID.

        Returns:
            True if updated, False otherwise.
        """
        query = """
        MATCH (u:Users {user_id: $user_id})
        SET u.last_login = $last_login,
            u.updated_at = $updated_at
        RETURN u
        """

        now = datetime.utcnow().timestamp()

        try:
            result = self._execute_write(
                query,
                {"user_id": user_id, "last_login": now, "updated_at": now},
            )
            return result is not None
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            return False

    def update_password_hash(self, user_id: str, new_hash: str) -> bool:
        """Update user's password hash (for hash upgrades).

        Args:
            user_id: User ID.
            new_hash: New password hash.

        Returns:
            True if updated, False otherwise.
        """
        query = """
        MATCH (u:Users {user_id: $user_id})
        SET u.password_hash = $password_hash,
            u.updated_at = $updated_at
        RETURN u
        """

        now = datetime.utcnow().timestamp()

        try:
            result = self._execute_write(
                query,
                {"user_id": user_id, "password_hash": new_hash, "updated_at": now},
            )
            return result is not None
        except Exception as e:
            logger.error(f"Failed to update password hash for user {user_id}: {e}")
            return False

    def update_user(self, user_id: str, **kwargs) -> Optional[UserResponse]:
        """Update user properties.

        Args:
            user_id: User ID.
            **kwargs: Properties to update.

        Returns:
            Updated UserResponse if successful, None otherwise.
        """
        if not kwargs:
            return None

        # Build SET clause
        set_clauses = []
        params = {"user_id": user_id}

        for key, value in kwargs.items():
            if key in ["email", "full_name", "is_active"]:
                set_clauses.append(f"u.{key} = ${key}")
                params[key] = value
            elif key == "password":
                set_clauses.append("u.password_hash = $password_hash")
                params["password_hash"] = self.auth_service.hash_password(value)

        if not set_clauses:
            return None

        set_clauses.append("u.updated_at = $updated_at")
        params["updated_at"] = datetime.utcnow().timestamp()

        query = f"""
        MATCH (u:Users {{user_id: $user_id}})
        SET {", ".join(set_clauses)}
        RETURN u
        """

        try:
            result = self._execute_write(query, params)
            if result:
                user_node = result["u"]
                logger.info(f"Updated user: {user_id}")
                return self._node_to_response(user_node)
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")

        return None

    def delete_user(self, user_id: str) -> bool:
        """Delete a user.

        Args:
            user_id: User ID.

        Returns:
            True if deleted, False otherwise.
        """
        query = "MATCH (u:Users {user_id: $user_id}) DELETE u"

        try:
            with self.driver.session() as session:
                session.run(query, {"user_id": user_id})
            logger.info(f"Deleted user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False

    def list_users(self) -> list[UserResponse]:
        """List all users.

        Returns:
            List of UserResponse objects.
        """
        query = "MATCH (u:Users) RETURN u"

        try:
            with self.driver.session() as session:
                results = session.run(query)
                users = []
                for record in results:
                    user_node = record["u"]
                    user = self._node_to_response(user_node)
                    if user:
                        users.append(user)
                return users
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []

    @staticmethod
    def _node_to_db_model(node) -> UserDB:
        """Convert Neo4j node to UserDB model.

        Args:
            node: Neo4j node.

        Returns:
            UserDB instance.
        """
        return UserDB(
            user_id=node["user_id"],
            username=node["username"],
            email=node.get("email"),
            full_name=node.get("full_name"),
            password_hash=node["password_hash"],
            role=node["role"],
            is_active=node.get("is_active", True),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
            last_login=node.get("last_login"),
            bypass_guardrails=node.get("bypass_guardrails", False),
        )

    @staticmethod
    def _node_to_response(node) -> UserResponse:
        """Convert Neo4j node to UserResponse.

        Args:
            node: Neo4j node.

        Returns:
            UserResponse instance.
        """
        created_at = datetime.fromtimestamp(node["created_at"])
        updated_at = datetime.fromtimestamp(node["updated_at"])
        last_login = (
            datetime.fromtimestamp(node["last_login"]) if node.get("last_login") else None
        )

        return UserResponse(
            user_id=node["user_id"],
            username=node["username"],
            email=node.get("email"),
            full_name=node.get("full_name"),
            role=UserRole(node["role"]),
            is_active=node.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
            last_login=last_login,
            bypass_guardrails=node.get("bypass_guardrails", False),
        )

    def close(self) -> None:
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("User service connection closed")


# Global singleton instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get or create the global user service.

    Returns:
        UserService instance.
    """
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service


def initialize_user_service(driver: Optional[Driver] = None) -> UserService:
    """Initialize the global user service.

    Args:
        driver: Optional Neo4j driver.

    Returns:
        Initialized UserService instance.
    """
    global _user_service
    _user_service = UserService(driver=driver)
    return _user_service
