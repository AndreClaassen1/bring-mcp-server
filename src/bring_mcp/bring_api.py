"""Bring! API Client for shopping list management."""

import hashlib
import uuid
from typing import Any
from urllib.parse import urljoin

import httpx


class BringAPIError(Exception):
    """Exception raised for Bring! API errors."""
    pass


class BringAPI:
    """Client for interacting with the Bring! Shopping List API."""

    BASE_URL = "https://api.getbring.com/rest/v2/"

    def __init__(self, email: str, password: str):
        """Initialize the Bring! API client.

        Args:
            email: Bring! account email
            password: Bring! account password
        """
        self.email = email
        self.password = password
        self.uuid = str(uuid.uuid4())
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._user_uuid: str | None = None
        self._client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for authenticated requests."""
        if not self._access_token:
            raise BringAPIError("Not authenticated. Call login() first.")

        return {
            "Authorization": f"Bearer {self._access_token}",
            "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
            "X-BRING-CLIENT": "webApp",
            "X-BRING-CLIENT-SOURCE": "webApp",
            "X-BRING-COUNTRY": "DE",
            "Content-Type": "application/json",
        }

    async def login(self) -> dict[str, Any]:
        """Authenticate with Bring! API.

        Returns:
            Authentication response data

        Raises:
            BringAPIError: If authentication fails
        """
        url = urljoin(self.BASE_URL, "bringauth")

        headers = {
            "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
            "X-BRING-CLIENT": "webApp",
            "X-BRING-CLIENT-SOURCE": "webApp",
            "X-BRING-COUNTRY": "DE",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "email": self.email,
            "password": self.password,
        }

        try:
            response = await self._client.post(url, headers=headers, data=data)
            response.raise_for_status()

            auth_data = response.json()
            self._access_token = auth_data.get("access_token")
            self._refresh_token = auth_data.get("refresh_token")
            self._user_uuid = auth_data.get("uuid")

            if not self._access_token:
                raise BringAPIError("No access token in response")

            return auth_data

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Login failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Login error: {str(e)}")

    async def get_lists(self) -> list[dict[str, Any]]:
        """Get all shopping lists for the authenticated user.

        Returns:
            List of shopping list objects with name, listUuid, and theme

        Raises:
            BringAPIError: If request fails
        """
        url = urljoin(self.BASE_URL, f"bringusers/{self._user_uuid}/lists")

        try:
            response = await self._client.get(url, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()
            return data.get("lists", [])

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Failed to get lists: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Error getting lists: {str(e)}")

    async def get_list_items(self, list_uuid: str) -> dict[str, Any]:
        """Get all items from a specific shopping list.

        Args:
            list_uuid: UUID of the shopping list

        Returns:
            Dictionary with 'purchase' (items to buy) and 'recently' (recent items) lists

        Raises:
            BringAPIError: If request fails
        """
        url = urljoin(self.BASE_URL, f"bringlists/{list_uuid}")

        try:
            response = await self._client.get(url, headers=self._get_headers())
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Failed to get list items: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Error getting list items: {str(e)}")

    async def add_item(
        self,
        list_uuid: str,
        item_name: str,
        specification: str = ""
    ) -> dict[str, Any]:
        """Add an item to a shopping list.

        Args:
            list_uuid: UUID of the shopping list
            item_name: Name of the item to add
            specification: Optional specification/details for the item

        Returns:
            Response data from the API

        Raises:
            BringAPIError: If request fails
        """
        url = urljoin(self.BASE_URL, f"bringlists/{list_uuid}")

        headers = self._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        data = {
            "uuid": self._generate_item_uuid(item_name),
            "purchase": item_name,
            "specification": specification,
        }

        try:
            response = await self._client.put(url, headers=headers, data=data)
            response.raise_for_status()

            if response.text:
                return response.json()
            return {"status": "ok"}

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Failed to add item: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Error adding item: {str(e)}")

    async def complete_item(self, list_uuid: str, item_name: str) -> dict[str, Any]:
        """Mark an item as completed (purchased) and move it to recently purchased.

        Args:
            list_uuid: UUID of the shopping list
            item_name: Name of the item to complete

        Returns:
            Response data from the API

        Raises:
            BringAPIError: If request fails
        """
        url = urljoin(self.BASE_URL, f"bringlists/{list_uuid}")

        headers = self._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        data = {
            "uuid": self._generate_item_uuid(item_name),
            "recently": item_name,
            "specification": "",
        }

        try:
            response = await self._client.put(url, headers=headers, data=data)
            response.raise_for_status()

            if response.text:
                return response.json()
            return {"status": "ok"}

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Failed to complete item: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Error completing item: {str(e)}")

    async def remove_item(self, list_uuid: str, item_name: str) -> dict[str, Any]:
        """Remove an item from a shopping list completely.

        Args:
            list_uuid: UUID of the shopping list
            item_name: Name of the item to remove

        Returns:
            Response data from the API

        Raises:
            BringAPIError: If request fails
        """
        url = urljoin(self.BASE_URL, f"bringlists/{list_uuid}")

        headers = self._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        data = {
            "uuid": self._generate_item_uuid(item_name),
            "remove": item_name,
        }

        try:
            response = await self._client.put(url, headers=headers, data=data)
            response.raise_for_status()

            if response.text:
                return response.json()
            return {"status": "ok"}

        except httpx.HTTPStatusError as e:
            raise BringAPIError(f"Failed to remove item: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise BringAPIError(f"Error removing item: {str(e)}")

    def _generate_item_uuid(self, item_name: str) -> str:
        """Generate a deterministic UUID for an item based on its name.

        Args:
            item_name: Name of the item

        Returns:
            UUID string
        """
        # Create a hash from the item name and use it to generate a UUID
        hash_obj = hashlib.md5(item_name.encode())
        hash_hex = hash_obj.hexdigest()
        return f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
