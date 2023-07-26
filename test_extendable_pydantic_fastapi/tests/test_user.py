# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from requests import Response

from odoo.tests.common import tagged

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase

from ..routers import demo_pydantic_router
from ..schemas import PrivateUser, User


@tagged("post_install", "-at_install")
class TestUser(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def test_app_components(self):
        with self._create_test_client(router=demo_pydantic_router) as test_client:
            to_openapi = test_client.app.openapi()
            # Check post input and output types
            self.assertEqual(
                to_openapi["paths"]["/post_user"]["post"]["requestBody"]["content"][
                    "application/json"
                ]["schema"]["$ref"],
                "#/components/schemas/User",
            )
            self.assertEqual(
                to_openapi["paths"]["/post_user"]["post"]["responses"]["200"][
                    "content"
                ]["application/json"]["schema"]["$ref"],
                "#/components/schemas/UserSearchResponse",
            )
            self.assertEqual(
                to_openapi["paths"]["/post_private_user"]["post"]["requestBody"][
                    "content"
                ]["application/json"]["schema"]["$ref"],
                "#/components/schemas/PrivateUser",
            )
            self.assertEqual(
                to_openapi["paths"]["/post_private_user"]["post"]["responses"]["200"][
                    "content"
                ]["application/json"]["schema"]["$ref"],
                "#/components/schemas/User",
            )
            self.assertEqual(
                to_openapi["paths"]["/post_private_user_generic"]["post"][
                    "requestBody"
                ]["content"]["application/json"]["schema"]["$ref"],
                "#/components/schemas/PrivateUser",
            )
            self.assertEqual(
                to_openapi["paths"]["/post_private_user_generic"]["post"]["responses"][
                    "200"
                ]["content"]["application/json"]["schema"]["$ref"],
                "#/components/schemas/UserSearchResponse",
            )

            # Check Pydantic model extension
            self.assertEqual(
                set(to_openapi["components"]["schemas"]["User"]["properties"].keys()),
                {"name", "address"},
            )
            self.assertEqual(
                set(
                    to_openapi["components"]["schemas"]["PrivateUser"][
                        "properties"
                    ].keys()
                ),
                {"name", "address", "password"},
            )
            self.assertEqual(
                to_openapi["components"]["schemas"]["UserSearchResponse"]["properties"][
                    "items"
                ]["items"]["$ref"],
                "#/components/schemas/User",
            )

    def test_post_user(self):
        name = "Jean Dupont"
        address = "Rue du Puits 12, 4000 Liège"
        pydantic_data = User(name=name, address=address)
        # Assert that class was correctly extended
        self.assertTrue(pydantic_data.address)

        with self._create_test_client(router=demo_pydantic_router) as test_client:
            response: Response = test_client.post(
                "/post_user", content=pydantic_data.model_dump_json()
            )
            self.assertEqual(response.status_code, 200)
            res = response.json()
            self.assertEqual(res["total"], 1)
            user = res["items"][0]
            self.assertEqual(user["name"], name)
            self.assertEqual(user["address"], address)
            self.assertFalse("password" in user.keys())

    def test_post_private_user(self):
        """
        /post_private_user return attributes from User, but not PrivateUser

        Security check: this method should never return attributes from
        derived type PrivateUser, even thought a PrivateUser object
        is given as input.
        """
        name = "Jean Dupont"
        address = "Rue du Puits 12, 4000 Liège"
        password = "dummy123"
        pydantic_data = PrivateUser(name=name, address=address, password=password)
        # Assert that class was correctly extended
        self.assertTrue(pydantic_data.address)
        self.assertTrue(pydantic_data.password)

        with self._create_test_client(router=demo_pydantic_router) as test_client:
            response: Response = test_client.post(
                "/post_private_user", content=pydantic_data.model_dump_json()
            )
            self.assertEqual(response.status_code, 200)
            user = response.json()
            self.assertEqual(user["name"], name)
            self.assertEqual(user["address"], address)
            # Private attrs were not returned
            self.assertFalse("password" in user.keys())

    def test_post_private_user_generic(self):
        """
        /post_private_user_generic return attributes from User, but not PrivateUser

        Security check: this method should never return attributes from
        derived type PrivateUser, even thought a PrivateUser object
        is given as input.
        This test is specifically made to test this assertion with generics.
        """
        name = "Jean Dupont"
        address = "Rue du Puits 12, 4000 Liège"
        password = "dummy123"
        pydantic_data = PrivateUser(name=name, address=address, password=password)
        # Assert that class was correctly extended
        self.assertTrue(pydantic_data.address)
        self.assertTrue(pydantic_data.password)

        with self._create_test_client(router=demo_pydantic_router) as test_client:
            response: Response = test_client.post(
                "/post_private_user_generic", content=pydantic_data.model_dump_json()
            )
            self.assertEqual(response.status_code, 200)
            res = response.json()
            self.assertEqual(res["total"], 1)
            user = res["items"][0]
            self.assertEqual(user["name"], name)
            self.assertEqual(user["address"], address)
            # Private attrs were not returned
            self.assertFalse("password" in user.keys())
